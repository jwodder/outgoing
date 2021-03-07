.. currentmodule:: outgoing

Utilities for Extension Authors
===============================

.. autofunction:: lookup_netrc
.. autofunction:: resolve_password
.. autofunction:: resolve_path
.. autoclass:: OpenClosable
    :show-inheritance:

Pydantic Types & Models
-----------------------

The senders built into ``outgoing`` make heavy use of pydantic_ for validating
& processing configuration, and some of the custom types & models used are also
of general interest to anyone writing an ``outgoing`` extension that also uses
pydantic.

.. _pydantic: https://github.com/samuelcolvin/pydantic

.. autoclass:: Path()
.. autoclass:: FilePath()
.. autoclass:: DirectoryPath()
.. autoclass:: Password()
    :no-undoc-members:
.. autoclass:: StandardPassword()
    :no-undoc-members:
.. autoclass:: NetrcConfig()
