.. currentmodule:: outgoing

Core Python API
===============

Functions
---------

``outgoing`` provides the following functions for constructing e-mail sender
objects.  Once you have a sender object, simply use it in a context manager to
open it up, and then call its ``send()`` method with each
`email.message.EmailMessage` object you want to send.  See :ref:`examples` for
examples.

.. autofunction:: from_config_file
.. autofunction:: from_dict
.. autofunction:: get_default_configpath


.. _sender-objects:

Sender Objects
--------------

.. autoclass:: Sender()
    :special-members: __enter__, __exit__

In addition to the base protocol, ``outgoing``'s built-in senders are
reentrant__ and reusable__ as context managers, and their ``send()`` methods
can be called outside of a context.

__ https://docs.python.org/3/library/contextlib.html#reentrant-context-managers
__ https://docs.python.org/3/library/contextlib.html#reusable-context-managers


Exceptions
----------

.. autoexception:: Error
    :show-inheritance:
.. autoexception:: InvalidConfigError
    :show-inheritance:
.. autoexception:: InvalidPasswordError
    :show-inheritance:
.. autoexception:: MissingConfigError
    :show-inheritance:
.. autoexception:: NetrcLookupError
    :show-inheritance:
.. autoexception:: UnsupportedEmailError
    :show-inheritance:
