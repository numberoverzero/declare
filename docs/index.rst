declare - Scaffolding for frameworks
=================================================

declare is a library for creating declarative systems.  Its intended audience
includes both library authors and end users - models can be subclassed and put
to use immediately, or dynamically created to quickly scaffold out a framework.



Code lives here: https://github.com/numberoverzero/declare

User Guide
----------

.. toctree::
    :maxdepth: 2
    :glob:

    topics/getting_started
    topics/models
    topics/fields
    topics/types
    topics/conditions

API Reference
-------------

.. automodule:: declare
    :members:
    :undoc-members:
    :show-inheritance:

    declare

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
