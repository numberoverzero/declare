declare 0.9.5
========
:Build: |build|_ |coverage|_
:Documentation: http://declare.readthedocs.org/
:Downloads: http://pypi.python.org/pypi/declare
:Source: https://github.com/numberoverzero/declare

.. |build| image:: https://travis-ci.org/numberoverzero/declare.svg?branch=master
.. _build: https://travis-ci.org/numberoverzero/declare
.. |coverage| image:: https://coveralls.io/repos/numberoverzero/declare/badge.png?branch=master
.. _coverage: https://coveralls.io/r/numberoverzero/declare?branch=master

Declarative scaffolding for frameworks

Installation
============

``pip install declare``

Getting Started
===============

Let's build a quick model for Minecraft blocks::

    from declare import Model, Field, TypeDefinition
    import json

    # Wire format is json:
    # {
    #   "type": int     <- maps to enum
    #   "position": str <- packed x:y:z
    # }

    class BlockType(TypeDefinition):
        types = {
            0: "Grass",
            1: "Stone",
            2: "Diamond"
        }
        def load(self, value):
            return BlockType.types[value]

        def dump(self, value):
            # TODO: index types by value for O(1) lookup
            for tid, name in BlockType.types.items():
                if value == name:
                    return tid


    class Position(TypeDefinition):
        ''' [x, y, z] <--> "x:y:z" '''
        def load(self, value):
            return [int(v) for v in value.split(':')]

        def dump(self, value):
            return ':'.join(str(v) for v in value)


    class Block(Model):
        type = Field(BlockType)
        position = Field(Position)

        @classmethod
        def load(cls, wire):
            fields = cls.Meta.fields_by_model_name
            engine = cls.Meta.type_engine
            wire = json.loads(wire)
            kwargs = {}
            for name, field in fields.items():
                kwargs[name] = engine.load(field.typedef, wire[name])
            return cls(**kwargs)

        @classmethod
        def dump(cls, obj):
            fields = cls.Meta.fields_by_model_name
            engine = cls.Meta.type_engine
            kwargs = {}
            for name, field in fields.items():
                kwargs[name] = engine.dump(field.typedef, getattr(obj, name))
            return json.dumps(kwargs)


Let's set up our request handler to use these blocks::

    from bottle import route, request

    @route('/diamond_check')
    def func():
        wire = request.json
        block = Block.load(wire)
        if block.type == "Diamond":
            return {"diamond": True, "position": block.position}
        return {"diamond": False}


Alternatively, creating a diamond::

    @route('/make_diamond')
    def func():
        wire = request.json
        position = Position.load(wire)
        block = Block(type="Diamond", position=position)
        return Block.dump(block)


Nested Models
=============

Models are instances of TypeDefinitions, too.  That means models can be used
as fields, making recursive load/dump easy::

    class List(TypeDefinition):
        ''' Adapter for lists of objects '''
        def load(self, value):
            return [self.typedef.load(v) for v in value]
        def dump(self, value):
            return [self.typedef.dump(v) for v in value]


    class Region(Model):
        blocks = Field(List(Block))

        @classmethod
        def load(cls, wire):
            fields = cls.Meta.fields_by_model_name
            engine = cls.Meta.type_engine
            wire = json.loads(wire)
            kwargs = {}
            for name, field in fields.items():
                kwargs[name] = engine.load(field.typedef, wire[name])
            return cls(**kwargs)

        @classmethod
        def dump(cls, obj):
            fields = cls.Meta.fields_by_model_name
            engine = cls.Meta.type_engine
            kwargs = {}
            for name, field in fields.items():
                kwargs[name] = engine.dump(field.typedef, getattr(obj, name))
            return json.dumps(kwargs)


In fact, the same load/dump code from ``Block`` is usable here, since we're
just going to be loading/dumping from json.  When the type engine looks up the
load/dump functions for the ``List(Block)`` type, it will iteratively load/dump
each block using the Block.load and Block.dump methods.
