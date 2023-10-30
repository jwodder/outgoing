.. currentmodule:: outgoing

Utilities for Extension Authors
===============================

.. autofunction:: lookup_netrc
.. autofunction:: resolve_password
.. autofunction:: resolve_path
.. autoclass:: OpenClosable
    :show-inheritance:
    :exclude-members: model_config, model_fields, model_post_init

Pydantic Types & Models
-----------------------

The senders built into ``outgoing`` make heavy use of pydantic_ for validating
& processing configuration, and some of the custom types & models used are also
of general interest to anyone writing an ``outgoing`` extension that also uses
pydantic.

.. _pydantic: https://github.com/samuelcolvin/pydantic

.. class:: Path

    Converts its input to `pathlib.Path` instances, including expanding tildes.
    If there is a field named ``configpath`` declared before the `Path` field
    and its value is non-`None`, then the value of the `Path` field will be
    resolved relative to the parent directory of the ``configpath`` field;
    otherwise, it will be resolved relative to the current directory.

.. class:: FilePath

    Like `Path`, but the path must exist and be a file

.. class:: DirectoryPath

    Like `Path`, but the path must exist and be a directory

.. autoclass:: Password()
    :no-undoc-members:

.. autoclass:: StandardPassword()
    :no-undoc-members:

.. autoclass:: NetrcConfig()
    :exclude-members: model_config, model_fields
