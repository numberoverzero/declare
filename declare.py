import collections
import uuid
__all__ = ["Model", "Field", "TypeDefinition", "TypeEngine"]

missing = object()
# These engines can't be cleared
_fixed_engines = collections.ChainMap()


class TypeEngineMeta(type):
    engines = _fixed_engines.new_child()

    def __call__(cls, namespace, *args, **kwargs):
        engine = TypeEngineMeta.engines.get(namespace)
        if engine is None:
            engine = cls.__new__(cls)
            TypeEngineMeta.engines[namespace] = engine
            cls.__init__(engine, namespace, *args, **kwargs)
        return engine

    @classmethod
    def clear_engines(metaclass):
        ''' Clear all non-fixed engines '''
        metaclass.engines.clear()


class TypeEngine(object, metaclass=TypeEngineMeta):

    def __init__(self, namespace, *args, **kwargs):
        self.namespace = namespace
        self.unbound_types = set()
        self.bound_types = {}

    def register(self, typedef):
        if not self.is_compatible(typedef):
            raise ValueError("Incompatible type {} for engine {}".format(
                typedef, self))
        if typedef not in self.bound_types:
            self.unbound_types.add(typedef)

    def bind(self, **config):
        for typedef in self.unbound_types:
            load, dump = typedef.bind(self, **config)
            self.bound_types[typedef] = {
                "load": load,
                "dump": dump
            }
        self.unbound_types.clear()

    def load(self, typedef, value):
        return self.bound_types[typedef]["load"](value)

    def dump(self, typedef, value):
        return self.bound_types[typedef]["dump"](value)

    def is_compatible(sef, typedef):  # pragma: no cover
        return True

    def __contains__(self, typedef):
        return typedef in self.bound_types

    def __repr__(self):  # pragma: no cover
        return "{}({})".format(self.__class__.__name__, self.namespace)
    __str__ = __repr__
_fixed_engines["global"] = TypeEngine("global")


class TypeDefinition(object):
    """ Translates between python types and backend/storage/transport types """
    python_type = None
    backing_type = None

    def bind(self, engine=TypeEngine('global'), **config):
        """
        Bind the typedef to an engine, compiling the typedef's ``load`` and
        ``dump`` functions.  Defaults to binding to ``TypeEngine('global')``.

        Returns (load, dump) functions.
        """
        # If the conversion function builder returned None, use self.load
        # (passthrough functions unless defined)
        load = self.bind_load_func(engine, **config) or self.load
        dump = self.bind_dump_func(engine, **config) or self.dump

        return load, dump

    def bind_load_func(self, engine, **config):  # pragma: no cover
        """
        Return a conversion function for loading values.

        Returns a callable which will receive a ``backing_type`` value as the
        sole positional argument and will return a ``python_type`` value
        to return to the user.

        If processing is not necessary, the method should return ``None``.

        """
        return None

    def bind_dump_func(self, engine, **config):  # pragma: no cover
        """
        Return a conversion function for dumping values.

        Returns a callable which will receive a ``python_type`` value as the
        sole positional argument and will return a ``backing_type`` value
        to send to the backend.

        If processing is not necessary, the method should return ``None``.

        """
        return None

    def load(self, value):
        return value

    def dump(self, value):
        return value

    def __repr__(self):  # pragma: no cover
        cls = self.__class__.__name__
        return "{}({} <-> {})".format(cls, self.python_type, self.backing_type)
    __str__ = __repr__


class Field(object):
    def __init__(self, typedef=missing, **kwargs):
        self._model_name = None
        if typedef is missing:
            typedef = TypeDefinition
        try:
            if issubclass(typedef, TypeDefinition):
                typedef = typedef()
        except TypeError:
            if not isinstance(typedef, TypeDefinition):
                raise TypeError(
                    "Expected {} to be instance or subclass of TypeDefinition".
                    format(typedef))
        self.typedef = typedef

    @property
    def model_name(self):
        return self._model_name

    @model_name.setter
    def model_name(self, value):
        if self._model_name is not None:
            raise AttributeError("{} model_name already set to '{}'".format(
                self.__class__.__name__, self._model_name))
        self._model_name = value

    def set(self, obj, value):
        if self._model_name is None:
            raise AttributeError("Can't set field without binding to model")
        obj.__dict__[self._model_name] = value

    def get(self, obj):
        if self._model_name is None:
            raise AttributeError("Can't get field without binding to model")
        try:
            return obj.__dict__[self._model_name]
        except KeyError:
            raise AttributeError("'{}' has no attribute '{}'".format(
                obj.__class__, self._model_name))

    def delete(self, obj):
        if self._model_name is None:
            raise AttributeError("Can't delete field without binding to model")
        try:
            del obj.__dict__[self._model_name]
        except KeyError:
            raise AttributeError("'{}' has no attribute '{}'".format(
                obj.__class__, self._model_name))

    # Descriptor Protocol
    # To override, use set, get, delete above
    # https://docs.python.org/3.4/howto/descriptor.html

    def __set__(self, obj, value):
        self.set(obj, value)

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        return self.get(obj)

    def __delete__(self, obj):
        self.delete(obj)


def index(objects, attr):
    """
    Generate a mapping of a list of objects indexed by the given attr.

    Example
    -------

    class Person(object):
        def __init__(self, name, email, age):
            self.name = name
            self.email = email
            self.age = age

    people = [
        Person('one', 'one@people.com', 1),
        Person('two', 'two@people.com', 2),
        Person('three', 'three@people.com', 3)
    ]

    by_email = index(people, 'email')
    by_name = index(people, 'name')

    assert by_name['one'] is people[0]
    assert by_email['two@people.com'] is people[1]

    """
    return {getattr(obj, attr): obj for obj in objects}


def metadata_from_bases(bases):
    """
    Walk up the bases of a class, looking for a __meta__ attribute.
    If one is found, try to return a copy it.  If that fails or no base has
    the attribute, return an empty dict.

    """
    # Since None is the same as "don't copy this", use a sentinel to indicate
    # a missing attribute.  Stop walking up on None, not on missing
    for base in bases:
        meta = getattr(base, '__meta__', missing)
        if meta is not missing:
            try:
                return meta.copy()
            except AttributeError:
                # Something without a copy method, such as None
                # Don't copy, return a new dict
                return {}
    # Didn't find any __meta__ to copy
    return {}


class ModelMetaclass(type, TypeDefinition):
    """
    Track the order that ``Field`` attributes are declared,
    use a namespaced TypeEngine and register/bind fields' typedefs,
    insert a __meta__ attribute in the class
    """
    @classmethod
    def __prepare__(metaclass, name, bases):
        """ Returns an OrderedDict so attribute order is preserved """
        return collections.OrderedDict()

    def __new__(metaclass, name, bases, attrs):
        """ Add an OrderedDict ``fields`` to __meta__ """

        # Track meta, either copying from bases or empty dict
        # -------------------------------------------------------
        meta = attrs.get('__meta__', missing)
        if not isinstance(meta, collections.MutableMapping):
            # Try to find it in the class's parents
            if meta is missing:
                meta = metadata_from_bases(bases)
            # __meta__ was None or list or...
            # Don't blow it away, raise because we expected a dict-like obj
            else:
                raise AttributeError("Expected __meta__ to be dict-like,"
                                     + " got {} instead".format(meta))
        attrs['__meta__'] = meta

        cls = super().__new__(metaclass, name, bases, attrs)

        # Load or create a unique namespace and engine
        # ------------------------------------------------
        engine = meta.get("type_engine", None)
        engine_config = meta.get("type_engine_config", {})
        namespace = meta.get("namespace", None)
        if (engine and namespace) and (engine.namespace != namespace):
            raise AttributeError("Model namespace is overdefined!")
        if engine:
            namespace = engine.namespace
        elif namespace:
            engine = TypeEngine(namespace)
        else:
            # Neither defined, generate a unique namespace
            namespace = "{}-{}".format(name, uuid.uuid4())
            engine = TypeEngine(namespace)
        meta['namespace'] = namespace
        meta['type_engine'] = engine
        meta['type_engine_config'] = engine_config

        # Load and index fields, register field typedefs with engine
        # ----------------------------------------------------------
        fields = []
        for name, attr in attrs.items():
            if isinstance(attr, Field):
                fields.append(attr)
                engine.register(attr.typedef)
                # This will raise AttributeError if the field's
                # name is already set
                attr.model_name = name
        meta['fields_by_model_name'] = index(fields, 'model_name')
        meta['fields'] = fields

        # TypeEngine setup
        # ----------------
        engine.bind(**engine_config)
        cls.python_type = cls

        return cls


class Model(object, metaclass=ModelMetaclass):
    pass
