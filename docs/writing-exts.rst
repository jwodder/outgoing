.. currentmodule:: outgoing

.. _writing-extensions:

Writing Extensions
==================

Writing Sending Methods
-----------------------

A sending method is implemented as a callable (usually a class) that accepts
the fields of a configuration structure as keyword arguments and returns a
:ref:`sender object <sender-objects>`.  The keyword arguments include the
``method`` field and also include a ``configpath`` key specifying a
`pathlib.Path` pointing to the configuration file (or `None` if `from_dict()`
was called without setting a ``configpath``).  Callables should accept any
keyword argument and ignore any that they do not recognize.

For example, given the following configuration:

.. code:: toml

    [outgoing]
    method = "foobar"
    server = "www.example.nil"
    password = { env = "SECRET_TOKEN" }
    comment = "I like e-mail!"

the callable registered for the "foobar" method will be called with the
following keyword arguments:

.. code:: python

    **{
        "method": "foobar",
        "server": "www.example.nil",
        "password": {"env": "SECRET_TOKEN"},
        "comment": "I like e-mail!",
        "configpath": Path("path/to/configfile"),
    }

If the configuration passed to a callable is invalid, the callable should raise
an `InvalidConfigError`.

Callables can resolve password fields by passing them to `resolve_password()`
or by using pydantic and the `Password` type.  Callables should resolve paths
relative to the directory containing ``configpath`` by using `resolve_path()`
or by using pydantic and the `Path`, `FilePath`, and/or `DirectoryPath` types.

The last step of writing a sending method is to package it in a Python project
and declare the callable as an entry point in the ``outgoing.senders`` entry
point group so that users can install & access it.  For example, if your
project is built using setuptools, and the callable is a ``FooSender`` class in
the ``foobar.senders`` module, and you want it to be usable by setting ``method
= "foo"``, add the following to your :file:`setup.py`:

.. code:: python

    setup(
        ...
        entry_points={
            "outgoing.senders": [
                "foo = foobar.senders:FooSender",
            ],
        },
        ...
    )


Writing Password Schemes
------------------------

A password scheme is implemented as a function that takes the ``value`` part of
a ``password = { scheme = value }`` entry as an argument and returns the
corresponding password as a `str`.  If the function additionally accepts
arguments named ``host``, ``username``, and/or ``configpath`` (either
explicitly or via ``**kwargs``), the corresponding values passed to
`resolve_password()` will be forwarded to the scheme function.

If the ``value`` structure is invalid, or if no password can be found, the
function should raise an `InvalidPasswordError`.

The last step of writing a password scheme is to package it in a Python project
and declare the function as an entry point in the ``outgoing.password_schemes``
entry point group so that users can install & access it.  For example, if your
project is built using setuptools, and the function is ``foo_scheme()`` in the
``foobar.passwords`` module, and you want it to be usable by writing ``password
= { foo = some-value }``, add the following to your :file:`setup.py`:

.. code:: python

    setup(
        ...
        entry_points={
            "outgoing.password_schemes": [
                "foo = foobar.passwords:foo_scheme",
            ],
        },
        ...
    )
