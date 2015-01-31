import collections
from declare import Field, TypeDefinition, ModelMetaclass


def test_default_metadata():

    ''' metadata is a dict when not provided '''

    class Class(metaclass=ModelMetaclass):
        pass
    assert hasattr(Class, '__meta__')


def test_non_mapping_metadata():

    ''' ModelMetaclass uses empty dict when meta
    is a non-MutableMapping value '''

    class Class(metaclass=ModelMetaclass):
        __meta__ = None
    assert isinstance(Class.__meta__, collections.MutableMapping)


def test_parent_class_mapping_metadata():

    ''' ModelMetaclass finds metadata in parent class and copies it '''
    d = {'a': 'Hello, World!'}

    class Base(metaclass=ModelMetaclass):
        __meta__ = d

    class Derived(Base):
        pass

    assert Base.__meta__['a'] == d['a']
    assert Derived.__meta__ == Base.__meta__


def test_parent_class_mapping_non_metadata():

    ''' ModelMetaclass finds non-dict metadata in
    parent class and uses new dict '''
    class Base(object):
        __meta__ = None

    class Derived(Base, metaclass=ModelMetaclass):
        pass

    assert Base.__meta__ is None
    assert isinstance(Derived.__meta__, collections.MutableMapping)


def test_field_mixin_finds_fields_and_subclasses():

    ''' All instances of ``field.Field`` and its subclasses are added to
    ``__meta__['fields']``. '''
    class Subclass(Field):
        pass

    f = Field()
    g = Subclass(typedef=TypeDefinition())

    class Model(metaclass=ModelMetaclass):
        model_f = f
        model_g = g
        other = list()

    fields = Model.__meta__['fields']
    fields_by_name = Model.__meta__['fields_by_model_name']

    # Keyed by the class's attr keys
    assert 'model_f' in fields_by_name
    assert 'model_g' in fields_by_name

    # Objects are not wrapped at instantiation
    assert fields_by_name['model_f'] is f
    assert fields_by_name['model_g'] is g

    # Order and count
    assert len(fields) == 2
    assert fields == [f, g]

    # Non-fields are not included
    assert 'other' not in fields


def test_model_sets_field_model_names():

    ''' Fields' model_name is set at model creation '''

    class Model(metaclass=ModelMetaclass):
        f = Field()
    assert Model.f.model_name == 'f'
    assert 'f' in Model.__meta__['fields_by_model_name']


def test_model_metaclass_is_typedef():

    ''' classes with meta=ModelMetaclass are instances of TypeDefinitions '''
    class Model(metaclass=ModelMetaclass):
        f = Field()
    assert isinstance(Model, TypeDefinition)
