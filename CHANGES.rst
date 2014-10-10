0.2.0
-----
* **Breaking Change** ModelMetaclass will always try to first copy any parent's
  metadata, and then update the copy with any entries for the class being
  created.  This means a Model's children will by default use its TypEngine,
  instead of creating their own.


0.1.0
-----
* First public release
