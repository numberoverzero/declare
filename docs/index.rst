declare - Scaffolding for frameworks
=================================================

Many popular python frameworks have at some point re-invented the declarative
model, including a custom type system and various descriptors.  This is
(yet another) attempt at collecting the basic building blocks so that a
framework can pull the components they want, and quickly drop in relational
and business logic and get going.  By keeping YetAnotherBaseMetaclass out of
their code, tracing the life of an object from python -> backend -> python
should become much easier.


Code lives here: https://github.com/numberoverzero/declare

User Guide
----------

API Reference
-------------

Similar Modules
---------------
* marrow.schema_ - Almost identical, with different names and the exception
  of the Type API.  Wider compatibility (2.6+, 3.2+) with less restrictions
  (``Field``'s equivalent, ``Attribute``, does not require a type system -
  although one could be dropped in without issue.)
* normalize_ - Serialization is called out as an intended usage.  Field
  equivalent ``Property`` offers more built-in logic, such as ``required``,
  ``isa``, ``check`` attributes and various coercion/validation.
* param_ - Offers built-in subclasses of Fields (param.Number, ...) and
  bounds/doc optional kwargs.  Appears to be more focused on numeric/boolean
  fields than serialization/typing.
* scheme_ - A bit light on details, but looking through the code it seems very
  kitchen-sink - ``Field.__init__`` has 15 optional kwargs.  Also includes a
  generous handful of built-in subclasses (Binary, Boolean, Date, ...)

.. _marrow.schema: https://github.com/marrow/marrow.schema/
.. _normalize: http://hearsaycorp.github.io/normalize/
.. _param: http://ioam.github.io/param/
.. _scheme: https://github.com/siq/scheme

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
