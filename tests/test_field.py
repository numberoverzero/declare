import pytest
from declare import Field


class Container(object):
    ''' Subclass object so instances have a __dict__ '''
    field = Field()
Container.field.model_name = 'field'


def test_set_model_name_twice():

    ''' fields can be set to a model by name only once '''
    f = Field()
    f.model_name = "model1"

    with pytest.raises(AttributeError):
        f.model_name = "model2"
    assert f.model_name == "model1"


def test_set_raises_without_name():

    ''' can't store a value in obj dict without a name as a key '''
    f = Field()
    obj = object()
    with pytest.raises(AttributeError):
        f.set(obj, 'value')


def test_get_raises_without_name():

    ''' can't get a value in obj dict without a name as a key '''
    f = Field()
    obj = object()
    with pytest.raises(AttributeError):
        f.get(obj)


def test_delete_raises_without_name():

    ''' can't delete a value from obj dict without a name as a key '''
    f = Field()
    obj = object()
    with pytest.raises(AttributeError):
        f.delete(obj)


def test_set_stores_in_object_dict():

    ''' set uses object dict for storage '''
    obj = Container()
    obj.field = 'value'
    assert obj.__dict__['field'] == 'value'


def test_get_loads_from_object_dict():

    ''' get uses object dict for storage '''
    obj = Container()
    obj.__dict__['field'] = 'value'
    assert obj.field == 'value'


def test_delete_removes_from_object_dict():

    ''' del uses object dict for storage '''
    obj = Container()
    obj.__dict__['field'] = 'value'
    del obj.field
    assert 'field' not in obj.__dict__


def test_delete_before_set():

    ''' del should raise AttributeError, not KeyError '''
    obj = Container()
    with pytest.raises(AttributeError):
        del obj.field


def test_get_before_set():

    ''' get should raise AttributeError, not KeyError '''
    obj = Container()
    with pytest.raises(AttributeError):
        obj.field


def test_wrong_typedef_type():

    ''' typedef must be instanceof or subclassof TypeDefinition '''
    with pytest.raises(TypeError):
        Field(typedef=None)
