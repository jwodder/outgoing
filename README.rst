.. image:: http://www.repostatus.org/badges/latest/wip.svg
    :target: http://www.repostatus.org/#wip
    :alt: Project Status: WIP — Initial development is in progress, but there
          has not yet been a stable, usable release suitable for the public.

.. image:: https://github.com/jwodder/outgoing/workflows/Test/badge.svg?branch=master
    :target: https://github.com/jwodder/outgoing/actions?workflow=Test
    :alt: CI Status

.. image:: https://codecov.io/gh/jwodder/outgoing/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/jwodder/outgoing

.. image:: https://img.shields.io/github/license/jwodder/outgoing.svg
    :target: https://opensource.org/licenses/MIT
    :alt: MIT License

`GitHub <https://github.com/jwodder/outgoing>`_
| `Issues <https://github.com/jwodder/outgoing/issues>`_

``outgoing`` provides a common interface to multiple different e-mail sending
methods (SMTP, sendmail, mbox, etc.).  Just construct a sender from a
configuration file or object, pass it an ``EmailMessage`` instance, and let the
magical internet daemons take care of the rest.

``outgoing`` itself provides support for only basic sending methods; additional
methods are provided by other packages (COMING SOON).


Installation
============
``outgoing`` requires Python 3.6 or higher.  Just use `pip
<https://pip.pypa.io>`_ for Python 3 (You have pip, right?) to install
``outgoing`` and its dependencies::

    python3 -m pip install git+https://github.com/jwodder/outgoing


Example
=======

.. code:: python

    from email.message import EmailMessage
    import outgoing

    # Construct an EmailMessage object the standard Python way:
    msg = EmailMessage
    msg["Subject"] = "Meet me"
    msg["To"] = "my.beloved@love.love"
    msg["From"] = "me@here.qq"
    msg.set_content(
        "Oh my beloved!\n"
        "\n"
        "Wilt thou dine with me on the morrow?\n"
        "\n"
        "We're having hot pockets.\n"
        "\n"
        "Love, Me\n"
    )

    # Construct a sender object based on the default config file.  (This
    # assumes you've already populated your config file as described below.
    # Alternatively, you can specify an explicit configuration by passing it to
    # the `outgoing.from_dict()` method.)
    with outgoing.from_config_file() as sender:

        # Now send that letter!
        sender.send(msg)


Usage
=====

Configuration File
------------------

``outgoing`` reads information on what sending method and parameters to use
from a TOML_ configuration file.  The default location of this file depends on
your OS:

.. _TOML: https://toml.io

=======  ====================================================================
Linux    ``~/.local/share/outgoing/outgoing.toml``
         or ``$XDG_DATA_HOME/outgoing/outgoing.toml``
macOS    ``~/Library/Application Support/outgoing/outgoing.toml``
Windows  ``C:\Users\<username>\AppData\Local\jwodder\outgoing\outgoing.toml``
=======  ====================================================================

To find the exact path on your system, after installing ``outgoing``, run::

    python3 -c "from outgoing import get_default_configpath; print(get_default_configpath())"

Within the configuration file, all of the ``outgoing`` settings are contained
within a table named "``outgoing``".  This table must include at least a
``method`` key giving the name of the sending method to use.  The rest of the
table depends on the method chosen.  Unknown or inapplicable keys in the table
are ignored.

File & directory paths in the configuration file may start with a tilde (``~``)
to refer to a path relative to the user's home directory.  Any relative paths
are resolved relative to the location of the configuration file.

``command`` method
~~~~~~~~~~~~~~~~~~

The ``command`` method sends an e-mail by passing it as input to a command
(e.g., ``sendmail``, sold separately).  The default command is ``sendmail -i
-t``.  A different command can be used by setting the ``command`` key to the
command as a string.  This string will be interpreted by the shell, and so
metacharacters like pipes and redirects have their special meanings.

Example ``command`` configuration:

.. code:: toml

    [outgoing]
    method = "command"
    command = "/usr/local/bin/mysendmail -i -t"


``smtp`` method
~~~~~~~~~~~~~~~

The ``smtp`` method sends an e-mail to a server over SMTP.  The configuration
keys for this method are:

============  =================================================================
``host``      The server to connect to
``ssl``       *(optional)* ``true``: Use SSL/TLS from the start to connect to
              the server; ``false`` (default): Don't use SSL/TLS;
              ``"starttls"``: Switch to SSL/TLS after connecting with the
              STARTTLS command
``port``      *(optional)* The port on the server to connect to; the default
              depends on the value of ``ssl``: ``true`` — 465, ``false`` — 25,
              ``"starttls"`` — 587
``username``  *(optional)* Username to log into the server with
``password``  *(optional)* Password to log into the server with; can be given
              as either a string or a password specified (see "Passwords_")
``netrc``     *(optional)* If ``true``, read the username & password from
              ``~/.netrc`` instead of specifying them in the configuration
              file; if a string, read them from the given netrc file
============  =================================================================

Example ``smtp`` configuration:

.. code:: toml

    [outgoing]
    method = "smtp"
    host = "mx.example.com"
    ssl = "starttls"
    username = "myname"
    password = { "file" = "~/secrets/smtp-password" }

Another sample configuration:

.. code:: toml

    [outgoing]
    method = "smtp"
    host = "mail.nil"
    port = 1337
    ssl = true
    # Read username & password from the "mail.nil" entry in this netrc file:
    netrc = "~/secrets/net.rc"


``mbox`` method
~~~~~~~~~~~~~~~

The ``mbox`` method appends e-mails to an mbox file on the local machine.  It
requires a ``path`` key giving the location of the mbox file to use.

Example ``mbox`` configuration:

.. code:: toml

    [outgoing]
    method = "mbox"
    path = "~/MAIL/inbox"


``null`` method
~~~~~~~~~~~~~~~

Goes nowhere, does nothing, ignores all configuration keys.

Example ``null`` configuration:

.. code:: toml

    [outgoing]
    # Just send my e-mails into a black hole
    method = "null"


Passwords
---------

When a sending method (either one built into ``outgoing`` or one provided by an
extension) calls for a password, API key, or other secret, there are several
ways to specify the value.

Using a string, naturally, supplies the value of that string as the password:

.. code:: toml

    password = "hunter2"

Alternatively, a password can be read from a file by specifying a table with a
single ``file`` key and the filepath as the value:

.. code:: toml

    password = { file = "path/to/file" }

The entire contents of the file, minus any leading or trailing whitespace, will
then be used as the password.  As with paths elsewhere in the configuration
file, the path may start with a tilde, and relative paths are resolved relative
to the location of the configuration file.

A password can also be read from an environment variable by specifying a table
with a single ``env`` key and the name of the environment variable as the
value:

.. code:: toml

    password = { env = "PROTOCOL_PASSWORD" }

Extension packages can define additional password provider methods.


Python API
----------

Outgoing provides the following functions for constructing e-mail senders:

.. code:: python

    outgoing.from_config_file(
        path: Optional[AnyPath] = None,
        section: Optional[str] = outgoing.DEFAULT_CONFIG_SECTION,
        fallback: bool = True,
    ) -> Sender

Read configuration from the table/field ``section`` (default "``outgoing``") in
the file at ``path`` (default: the path returned by
``outgoing.get_default_configpath()``) and construct a sender object from the
specification.  The file may be either TOML or JSON.  If ``section`` is
``None``, the entire file, rather than only a single field, is used as the
configuration.  If ``fallback`` is true, the file is not the default config
file, and the file either does not exist or does not contain the given section,
fall back to reading from the default section of the default config file.

.. code:: python

    outgoing.from_dict(
        data: Dict[str, Any],
        configpath: Optional[AnyPath] = None,
    ) -> Sender

Construct a sender object using the given ``data`` as the configuration.  If
``configpath`` is given, any paths in the ``data`` will be resolved relative to
it; otherwise, they will be resolved relative to the current directory.

---

Once you have a sender object from one of the above functions, simply put it in
a context manager to open it up, and then call its ``send()`` method for each
``email.message.EmailMessage`` object you want to send.  See the example at the
top of the file for an example.


Command-Line Program
--------------------

You can use ``outgoing`` to send fully-composed e-mails directly from the
command line with the ``outgoing`` command.  Save your e-mail as a complete
``message/rfc822`` document and then run ``outgoing path/to/email/file`` to
send it using the configuration in the default config file (or specify another
config file with the ``--config`` option).  Multiple files can be passed to the
command at once to send multiple e-mails.  If no files are specified on the
command line, the command reads an e-mail from standard input.


Writing Extensions
==================

DOCUMENTATION COMING SOON
