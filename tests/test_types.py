import base64
import collections
import pytest
from declare import (TypeEngine, TypeDefinition,
                     TypeEngineMeta, DeclareException)


@pytest.fixture(autouse=True)
def clear_engines(request):

    ''' Clear registered engines before and after each test '''

    TypeEngineMeta.clear_engines()
    request.addfinalizer(TypeEngineMeta.clear_engines)


@pytest.fixture()
def NumericEngine():
    class TestEngine(TypeEngine):
        ''' Only supports int and float backing types '''
        init_calls = 0

        def __init__(self, namespace, *args, **kwargs):
            TestEngine.init_calls += 1
            super().__init__(namespace, *args, **kwargs)

        def is_compatible(self, typedef):
            return typedef.backing_type in (int, float)
    return TestEngine


@pytest.fixture()
def NumericStringTypeDef():
    class TestTypeDef(TypeDefinition):
        ''' Handles python strings, converts to backing type of int '''
        python_type = str
        backing_type = int
        calls = collections.defaultdict(int)

        def bind(self, engine, **config):
            self.calls['bind'] += 1
            return super().bind(engine, **config)

        def _load(self, value, context):
            # int -> str
            return str(value)

        def _dump(self, value, context):
            # str -> int
            return int(value)

    return TestTypeDef


@pytest.fixture()
def Base64BytesTypeDef():
    class TestTypeDef(TypeDefinition):
        ''' Handles python bytes, converts to base64 encoded str '''
        python_type = bytes
        backing_type = str

        def bind(self, engine, **config):
            # return (load, dump)
            return (
                lambda x, ctx: base64.b64decode(x.encode("UTF-8")),
                lambda x, ctx: base64.b64encode(x).decode("UTF-8")
            )

    return TestTypeDef


@pytest.fixture()
def SimpleTypeDef():
    class TestTypeDef(TypeDefinition):
        ''' Always uses ``load`` and ``dump`` regardless of engine '''
        def _load(self, value, context):
            suffix = "::test"
            if value.endswith(suffix):
                return value[:-len(suffix)]
            return value

        def _dump(self, value, context):
            return value + "::test"
    return TestTypeDef


@pytest.fixture()
def TypeDefRaisesOnBind():
    class TestTypeDef(TypeDefinition):
        exception = ValueError("Default test exception")
        ''' Always raises on self.bind '''
        def bind(self, engine, **config):
            raise self.exception
    return TestTypeDef


@pytest.fixture()
def engine_for():
    def func(*typedefs):
        engine = TypeEngine.unique()
        for typedef in typedefs:
            engine.register(typedef)
        engine.bind()
        return engine
    return func


def test_unique_namespaces():

    ''' Not terribly effective test of TypeEngine.unique() '''

    engine1 = TypeEngine.unique()
    engine2 = TypeEngine.unique()

    assert engine1 is not engine2


def test_engine_same_namespace():

    ''' Two engines with the same namespace should be the same object '''

    engine1 = TypeEngine('same')
    engine2 = TypeEngine('same')
    assert engine1 is engine2


def test_init_once_per_namespace(NumericEngine):

    ''' TypeEngineMeta should make sure only new engines are __init__'d '''
    NumericEngine("foo")
    NumericEngine("foo")

    assert NumericEngine.init_calls == 1


def test_global_engine_fixed():

    ''' GlobalTypeEngine is a fixed engine, and cannot be cleared '''

    assert "global" in TypeEngineMeta.engines
    TypeEngineMeta.clear_engines()
    assert "global" in TypeEngineMeta.engines


def test_register_incompatibile_typedef(NumericEngine, Base64BytesTypeDef):

    ''' register should fail if the typedef is incompatibile '''

    engine = NumericEngine("test_namespace")
    typedef = Base64BytesTypeDef()

    with pytest.raises(ValueError):
        engine.register(typedef)
    assert typedef not in engine


def test_register_multiple_calls(NumericEngine, NumericStringTypeDef):

    ''' multiple calls to register with the same typedef should be fine '''

    engine = NumericEngine("test_namespace")
    typedef = NumericStringTypeDef()

    engine.register(typedef)
    assert typedef not in engine
    engine.register(typedef)
    assert typedef not in engine


def test_register_compatibile_typedef(NumericEngine, NumericStringTypeDef):

    ''' register should succeed if the typedef is compatibile '''

    engine = NumericEngine("test_namespace")
    typedef = NumericStringTypeDef()

    engine.register(typedef)
    assert typedef not in engine

    engine.bind()
    assert typedef in engine


def test_register_does_not_bind(NumericEngine, NumericStringTypeDef):

    ''' typedef binding may expect the engine to have registered all types '''

    engine = NumericEngine("test_namespace")
    typedef = NumericStringTypeDef()

    engine.register(typedef)
    assert typedef in engine.unbound_types


def test_register_bound_type(NumericEngine, NumericStringTypeDef):

    ''' registering a typedef that's already bound doesn't do anything '''
    engine = NumericEngine("test_namespace")
    typedef = NumericStringTypeDef()

    engine.register(typedef)
    engine.bind()
    engine.register(typedef)
    assert typedef not in engine.unbound_types


def test_register_calls_typedef_register():

    ''' registering a type informs the type that it's been registered '''

    class Notify(TypeDefinition):
        registered = False

        def _register(self, engine):
            self.registered = True

    engine = TypeEngine.unique()
    typedef = Notify()

    assert not typedef.registered
    engine.register(typedef)
    assert typedef.registered


def test_bind_empty_engine():

    ''' bind doesn't do anything when the engine has no types '''

    engine = TypeEngine.unique()
    engine.bind()
    assert not engine.bound_types


def test_multiple_bind_calls(NumericEngine, NumericStringTypeDef):

    ''' bind only binds registered typedefs it hasn't invoked bind on '''

    engine = NumericEngine("test_namespace")
    typedef = NumericStringTypeDef()
    engine.register(typedef)

    assert typedef.calls['bind'] == 0
    engine.bind()
    assert typedef.calls['bind'] == 1
    engine.bind()
    assert typedef.calls['bind'] == 1
    engine.bind()


def test_bound_default_typedef_conversions(engine_for):

    ''' typedefs should use passthrough functions if bind returned None '''

    typedef = TypeDefinition()
    engine = engine_for(typedef)
    values = ['string', 1, None, object()]
    context = {}
    for value in values:
        assert value == engine.load(typedef, value, context)
        assert value == engine.dump(typedef, value, context)


def test_bound_typedef_conversions(Base64BytesTypeDef, engine_for):

    ''' typedefs should bind load/dump '''

    typedef = Base64BytesTypeDef()
    engine = engine_for(typedef)

    values = [
        ("Hello, World!", "SGVsbG8sIFdvcmxkIQ=="),
        ("", "")
    ]
    context = {}

    for (py_str, backing_value) in values:
        py_value = py_str.encode("UTF-8")
        assert engine.dump(typedef, py_value, context) == backing_value
        assert engine.load(typedef, backing_value, context) == py_value


def test_bind_handles_exceptions(TypeDefRaisesOnBind):

    ''' A typedef that raises during bind isn't removed from unbound_types '''

    typedef = TypeDefRaisesOnBind()
    typedef.exception = TypeError("Failed to bind")

    engine = TypeEngine.unique()
    engine.register(typedef)

    with pytest.raises(TypeError):
        engine.bind()
    assert typedef in engine.unbound_types


def test_fallback_class_load_dump(SimpleTypeDef):

    ''' if the class defines ``load`` and ``dump``, fall back to those methods
    instead of the default TypeDefinition functions (passthroughs) '''

    engine = TypeEngine.unique()
    typedef = SimpleTypeDef()
    load, dump = typedef.bind(engine)
    context = {}

    assert dump("hello", context) == "hello::test"
    assert load("hello::test", context) == "hello"


def test_dump_unbound_typedef(SimpleTypeDef):

    ''' engine.dump for an unbound typedef raises, even if registered '''
    engine = TypeEngine.unique()
    typedef = SimpleTypeDef()
    context = {}

    with pytest.raises(DeclareException):
        engine.dump(typedef, "foo", context)

    engine.register(typedef)
    with pytest.raises(DeclareException):
        engine.dump(typedef, "foo", context)

    engine.bind()
    assert engine.dump(typedef, "foo", context) == "foo::test"


def test_load_unbound_typedef(SimpleTypeDef):

    ''' engine.load for an unbound typedef raises, even if registered '''
    engine = TypeEngine.unique()
    typedef = SimpleTypeDef()
    context = {}

    with pytest.raises(DeclareException):
        engine.load(typedef, "foo::test", context)

    engine.register(typedef)
    with pytest.raises(DeclareException):
        engine.load(typedef, "foo::test", context)

    engine.bind()
    assert engine.load(typedef, "foo::test", context) == "foo"


def test_context_passed(engine_for):

    ''' context is passed to load, dump through engine '''

    class Typedef(TypeDefinition):
        ''' Handles python strings, converts to backing type of int '''
        python_type = str
        backing_type = int

        def _load(self, value, context):
            context["load"] += 1
            return super()._load(value, context)

        def _dump(self, value, context):
            context["dump"] += 1
            return super()._dump(value, context)

    typedef = Typedef()
    engine = engine_for(typedef)

    value = "value"
    context = {"load": 0, "dump": 0}
    engine.load(typedef, value, context)
    engine.dump(typedef, value, context)

    assert context["load"] == 1
    assert context["dump"] == 1
