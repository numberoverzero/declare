import pytest
from declare import Field, TypeDefinition, ModelMetaclass


def test_default_metadata():

    ''' metadata is a dict when not provided '''

    class Class(metaclass=ModelMetaclass):
        pass
    assert hasattr(Class, 'Meta')


def test_non_mapping_metadata():

    ''' ModelMetaclass raises when meta is a non-MutableMapping value '''

    with pytest.raises(TypeError):
        class Class(metaclass=ModelMetaclass):
            Meta = None


def test_parent_class_mapping_non_metadata():

    ''' ModelMetaclass doesn't use parent Meta instance '''
    class Base(object):
        class Meta:
            base_attr = "foo"

    class Derived(Base, metaclass=ModelMetaclass):
        pass

    assert Derived.Meta is not Base.Meta


def test_field_mixin_finds_fields_and_subclasses():

    ''' All instances of ``field.Field`` and its subclasses are added to
    ``Meta['fields']``. '''
    class Subclass(Field):
        pass

    f = Field()
    g = Subclass(typedef=TypeDefinition())

    class Model(metaclass=ModelMetaclass):
        model_f = f
        model_g = g
        other = list()

    fields = Model.Meta.fields
    fields_by_name = Model.Meta.fields_by_model_name

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
    assert 'f' in Model.Meta.fields_by_model_name


def test_model_metaclass_is_typedef():

    ''' classes with meta=ModelMetaclass are instances of TypeDefinitions '''
    class Model(metaclass=ModelMetaclass):
        f = Field()
    assert isinstance(Model, TypeDefinition)
