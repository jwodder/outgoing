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

Sender objects support, at minimum, the following protocol:

- They can be used as context managers, and their ``__enter__`` methods return
  ``self``.

- Within its own context, calling a sender's ``send(msg:
  email.message.EmailMessage)`` method sends the given e-mail.

In addition, ``outgoing``'s built-in senders are reentrant__ and reusable__ as
context managers, and their ``send()`` methods can be called outside of a
context.

__ https://docs.python.org/3/library/contextlib.html#reentrant-context-managers
__ https://docs.python.org/3/library/contextlib.html#reusable-context-managers


Exceptions
----------

.. autoexception:: outgoing.errors.Error
    :show-inheritance:
.. autoexception:: outgoing.errors.InvalidConfigError
    :show-inheritance:
.. autoexception:: outgoing.errors.InvalidPasswordError
    :show-inheritance:
.. autoexception:: outgoing.errors.MissingConfigError
    :show-inheritance:
.. autoexception:: outgoing.errors.NetrcLookupError
    :show-inheritance:
.. autoexception:: outgoing.errors.UnsupportedEmailError
    :show-inheritance:
