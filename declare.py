''' Declarative scaffolding for frameworks '''
import collections
import uuid
__all__ = ["ModelMetaclass", "Field", "TypeDefinition",
           "TypeEngine", "DeclareException"]
__version__ = "0.9.9"

missing = object()
# These engines can't be cleared
_fixed_engines = collections.ChainMap()


class DeclareException(Exception):
    '''
    Custom exception for cases where raising a built-in exception
    would be ambiguous (whether it was thrown by declare or a bound function)
    '''
    pass


class TypeEngineMeta(type):
    '''
    Factory for :class:`~TypeEngine` so that each engine is init'd only once.

    This is necessary since if :meth:`~TypeEngine.__new__` returns an instance
    of the class, the :meth:`~TypeEngine.__init__` method will be called.
    '''
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
    '''
    Collection of bound :class:`~TypeDefinition` for a given namespace.

    TypeEngines are unique by namespace::

        assert TypeEngine("foo") is TypeEngine("foo")

    This makes it easier for groups of components to use a single engine to
    translate values by type.  By default :meth:`~TypeEngine.load` and
    :meth:`~TypeEngine.dump` require a reference to the typedef used to convert
    values.  A custom Engine could use the :class:`~TypeDefinition` attributes
    ``python_type`` and ``backing_type`` to find the correct typedef from the
    set of available typedefs and automatically convert to the necessary
    format.

    '''
    def __init__(self, namespace="global", *args, **kwargs):
        self.namespace = namespace
        self.unbound_types = set()
        self.bound_types = {}

    @classmethod
    def unique(cls):
            ''' Return a unique type engine (using uuid4) '''
            namespace = str(uuid.uuid4())
            return TypeEngine(namespace)

    def register(self, typedef):
        '''
        Add the typedef to this engine if it is compatible.

        After registering a :class:`~TypeDefinition`, it will not be bound
        until :meth:`~TypeEngine.bind` is next called.

        Nothing will happen when register is called with a typedef that is
        pending binding or already bound.  Otherwise, the engine will ensure it
        is compatible with the type using :meth:`~TypeEngine.is_compatible`
        before adding it to the set of unbound types.

        Parameters
        ----------
        typedef : :class:`~TypeDefinition`
            The typedef to register with this engine

        Raises
        ------
        exc : :class:`ValueError`
            If :meth:`~TypeEngine.is_compatible` is falsey

        '''
        if typedef in self.bound_types:
            return
        if not self.is_compatible(typedef):
            raise ValueError("Incompatible type {} for engine {}".format(
                typedef, self))
        if typedef not in self.unbound_types:
            self.unbound_types.add(typedef)
            typedef._register(self)

    def bind(self, **config):
        '''
        Bind all unbound types to the engine.

        Bind each unbound typedef to the engine, passing in the engine and
        :attr:`config`.  The resulting ``load`` and ``dump`` functions can
        be found under ``self.bound_types[typedef]["load"]`` and
        ``self.bound_types[typedef]["dump"], respectively.

        Parameters
        ----------
        config : dict, optional
            Engine-binding configuration to pass to each typedef that will be
            bound.  Examples include floating-point precision values, maximum
            lengths for strings, or any other translation constraints/settings
            that a typedef needs to construct a load/dump function pair.

        '''
        while self.unbound_types:
            typedef = self.unbound_types.pop()
            try:
                load, dump = typedef.bind(self, **config)
                self.bound_types[typedef] = {
                    "load": load, "dump": dump
                }
            except Exception:
                self.unbound_types.add(typedef)
                raise

    def load(self, typedef, value, context):
        '''
        Return the result of the bound load method for a typedef

        Looks up the load function that was bound to the engine for a typedef,
        and return the result of passing the given `value` and any `context`
        to that function.

        Parameters
        ----------
        typedef : :class:`~TypeDefinition`
            The typedef whose bound load method should be used
        value : object
            The value to be passed into the bound load method
        **context : kwargs
            Context for the value being loaded

        Returns
        -------
        loaded_value : object
            The return value of the load function for the input value

        Raises
        ------
        exc : :class:`KeyError`
            If the input typedef is not bound to this engine

        Example
        -------

        .. code-block:: python

            class Account(TypeDefinition):
                prefix = "::account"
                def load(self, value, **context):
                    return value + Account.prefix

                def dump(self, value, **context):
                    return value[:-len(Account.prefix)]

            typedef = Account()
            engine = TypeEngine("accounts")
            engine.register(typedef)
            engine.bind()
            assert engine.dump(typedef, "Jill::account") == "Jill"

        '''
        try:
            bound_type = self.bound_types[typedef]
        except KeyError:
            raise DeclareException(
                "Can't load unknown type {}".format(typedef))
        else:
            # Don't need to try/catch since load/dump are bound together
            return bound_type["load"](value, context)

    def dump(self, typedef, value, context):
        '''
        Return the result of the bound dump method for a typedef

        Looks up the dump function that was bound to the engine for a typedef,
        and return the result of passing the given `value` and any `context`
        to that function.

        Parameters
        ----------
        typedef : :class:`~TypeDefinition`
            The typedef whose bound dump method should be used
        value : object
            The value to be passed into the bound dump method
        context : dict
            Context for the value being dumped

        Returns
        -------
        dumped_value : object
            The return value of the dump function for the input value

        Raises
        ------
        exc : :class:`KeyError`
            If the input typedef is not bound to this engine

        Example
        -------

        .. code-block:: python

            class Account(TypeDefinition):
                prefix = "::account"
                def load(self, value, context):
                    return value + Account.prefix

                def dump(self, value, context):
                    return value[:-len(Account.prefix)]

            typedef = Account()
            engine = TypeEngine("accounts")
            engine.register(typedef)
            engine.bind()
            assert engine.load(typedef, "Jill") == "Jill::account"

        '''
        try:
            bound_type = self.bound_types[typedef]
        except KeyError:
            raise DeclareException(
                "Can't dump unknown type {}".format(typedef))
        else:
            # Don't need to try/catch since load/dump are bound together
            return bound_type["dump"](value, context)

    def is_compatible(sef, typedef):  # pragma: no cover
        '''
        Returns ``true`` if the typedef is compatible with this engine.

        This function should return ``False`` otherwise.  The default
        implementation will always return ``True``.

        '''
        return True

    def __contains__(self, typedef):
        return typedef in self.bound_types


_fixed_engines["global"] = TypeEngine("global")


class TypeDefinition:
    '''
    Translates between python types and backend/storage/transport types

    A single TypeDefinition can be used for multiple TypeEngines, by
    implementing :meth:`~TypeDefinition.bind` and returning different
    (load, dump) function tuples for each engine.

    For TypeDefinitions that are loaded/dumped the same for every engine,
    just implement :meth:`~TypeDefinition._load` and
    :meth:`~TypeDefinition._dump`.

    '''
    python_type = None
    backing_type = None

    def bind(self, engine, **config):
        '''
        Return a pair of (load, dump) functions for a specific engine.

        Some Types will load and dump values depending on certain config, or
        for different :class:`~TypeEngine`.

        By default, this function will return the functions
        :meth:`~TypeDefinition.load` and :meth:`~TypeDefinition._dump`.

        The default :meth:`~TypeDefintion._load` and
        :meth:`~TypeDefintion._dump` functions simply return the input value.

        Parameters
        ----------
        engine : :class:`~TypeEngine`
            The engine that will save these load, dump functions
        config : dictionary
            Optional configuration for creating the functions.

        Returns
        -------
        (load, dump) : (func, func) tuple
            Each function takes a value and context, and returns a single value
        '''
        return self._load, self._dump

    def _register(self, engine):
        '''
        Called when the type is registered with an engine.
        '''
        pass

    def _load(self, value, context):
        '''
        Engine-agnostic load function.  Implement this method for any
        TypeDefinition whose load function does not depend on the TypeEngine
        being used to load it.

        NOTE: This will not be available at runtime -
        TypeDefinitionMetaclass hides the reference at runtime to reduce the
        chance of incorrectly using an engine-agnostic load method when the
        TypeDefinition prefers an engine-specific load method.

        By default, returns :attr:`value` unchanged.

        '''
        return value

    def _dump(self, value, context):
        '''
        Engine-agnostic dump function.  Implement this method for any
        TypeDefinition whose dump function does not depend on the TypeEngine
        being used to dump it.

        NOTE: This will not be available at runtime -
        TypeDefinitionMetaclass hides the reference at runtime to reduce the
        chance of incorrectly using an engine-agnostic dump method when the
        TypeDefinition prefers an engine-specific dump method.

        By default, returns :attr:`value` unchanged.

        '''
        return value


def subclassof(obj, classinfo):
    ''' Wrap issubclass to only return True/False '''
    try:
        return issubclass(obj, classinfo)
    except TypeError:
        return False


def instanceof(obj, classinfo):
    ''' Wrap isinstance to only return True/False '''
    try:
        return isinstance(obj, classinfo)
    except TypeError:  # pragma: no cover
        # No coverage since we never call this without a class,
        # type, or tuple of classes, types, or such typles.
        return False


class Field:
    def __init__(self, *, typedef=None, **kwargs):
        self._model_name = None
        if typedef is None:
            self.typedef = typedef
        else:
            if subclassof(typedef, TypeDefinition):
                typedef = typedef()
            if instanceof(typedef, TypeDefinition):
                self.typedef = typedef
            else:
                raise TypeError(("Expected {} to be None, instance of "
                                 "TypeDefinition, or subclass of"
                                 "TypeDefinition".format(typedef)))
        super().__init__(**kwargs)

    @property
    def model_name(self):
        ''' Name of the model's attr that references self '''
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
    '''
    Generate a mapping of a list of objects indexed by the given attr.

    Parameters
    ----------
    objects : :class:`list`, iterable
    attr : string
        The attribute to index the list of objects by

    Returns
    -------
    dictionary : dict
        keys are the value of each object's attr, and values are from objects

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

    '''
    return {getattr(obj, attr): obj for obj in objects}


class ModelMetaclass(type, TypeDefinition):
    '''
    Track the order that ``Field`` attributes are declared, and
    insert a Meta object (class) in the class
    '''
    @classmethod
    def __prepare__(metaclass, name, bases):
        ''' Returns an OrderedDict so attribute order is preserved '''
        return collections.OrderedDict()

    def __new__(metaclass, name, bases, attrs):
        ''' Add a container class `Meta` to the class '''

        Meta = attrs.get('Meta', missing)
        if Meta is missing:
            class Meta:
                pass
            attrs['Meta'] = Meta
        if not isinstance(Meta, type):
            raise TypeError("Expected `Meta` to be a class object")

        cls = super().__new__(metaclass, name, bases, attrs)

        # Load and index fields by name
        # ----------------------------------------------------------
        fields = []
        for name, attr in attrs.items():
            if isinstance(attr, Field):
                fields.append(attr)
                # This will raise AttributeError if the field's
                # name is already set
                attr.model_name = name
        Meta.fields_by_model_name = index(fields, 'model_name')
        Meta.fields = fields

        return cls
