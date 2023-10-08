Configuration
=============

.. _configfile:

The Configuration File
----------------------

``outgoing`` reads information on what sending method and parameters to use
from a TOML_ or JSON configuration file.  The default configuration file is
TOML, and its location depends on your OS:

.. _TOML: https://toml.io

=======  =======================================================================
Linux    :file:`~/.config/outgoing/outgoing.toml`
         or :file:`$XDG_CONFIG_HOME/outgoing/outgoing.toml`
macOS    :file:`~/Library/Application Support/outgoing/outgoing.toml`
Windows  :file:`%USERPROFILE%\\AppData\\Local\\jwodder\\outgoing\\outgoing.toml`
=======  =======================================================================

.. versionchanged:: 0.5.0

    Due to an upgrade to v3 of ``platformdirs``, the default configuration path
    on macOS changed from :file:`~/Library/Preferences/outgoing/outgoing.toml`
    to :file:`~/Library/Application Support/outgoing/outgoing.toml`.

To find the exact path on your system, after installing ``outgoing``, run::

    python3 -c "from outgoing import get_default_configpath; print(get_default_configpath())"

Within the configuration file, all of the ``outgoing`` settings are contained
within a table named "``outgoing``".  This table must include at least a
``method`` key giving the name of the sending method to use.  The rest of the
table depends on the method chosen (see below).  Unknown or inapplicable keys
in the table are ignored.

File & directory paths in the configuration file may start with a tilde (``~``)
to refer to a path in the user's home directory.  Any relative paths are
resolved relative to the directory containing the configuration file.

Sending Methods
---------------

``command``
~~~~~~~~~~~

The ``command`` method sends an e-mail by passing it as input to a command
(e.g., :command:`sendmail`, sold separately).

Configuration fields:

``command`` : string or list of strings (optional)
    Specify the command to run to send e-mail.  This can be either a single
    command string that will be interpreted by the shell or a list of command
    arguments that will be executed directly without any shell processing.  The
    default command is ``sendmail -i -t``.

    .. note::

        Relative paths in the command will not be resolved by ``outgoing``
        (unlike other paths in the configuration file), as it is not possible
        to reliably determine what is a path and what is not.

Example ``command`` configuration:

.. code:: toml

    [outgoing]
    method = "command"
    command = ["/usr/local/bin/mysendmail", "-i", "-t"]

Another sample configuration:

.. code:: toml

    [outgoing]
    method = "command"
    # A single string will be interpreted by the shell, so metacharacters like
    # pipes have their special meanings:
    command = "my-mail-munger | ~/some/dir/mysendmail"


``smtp``
~~~~~~~~

The ``smtp`` method sends an e-mail to a server over SMTP.

Configuration fields:

``host`` : string (required)
    The domain name or IP address of the server to connect to

``ssl`` : boolean or ``"starttls"`` (optional)
    - ``true``: Use SSL/TLS from the start of the connection
    - ``false`` (default): Don't use SSL/TLS
    - ``"starttls"``: After connecting, switch to SSL/TLS with the STARTTLS
      command

``port`` : integer (optional)
    The port on the server to connect to; the default depends on the value of
    ``ssl``:

    - ``true`` — 465
    - ``false`` — 25
    - ``"starttls"`` — 587

``username`` : string (optional)
    Username to log into the server with

``password`` : password (optional)
    Password to log into the server with; can be given as either a string or a
    password specifier (see ":ref:`passwords`")

``netrc`` : boolean or filepath (optional)
    If ``true``, read the username & password from ``~/.netrc`` instead of
    specifying them in the configuration file.  If a filepath, read the
    credentials from the given netrc file.  If ``false``, do not use a netrc
    file.

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


``mbox``
~~~~~~~~

The ``mbox`` method appends e-mails to an mbox file on the local machine.

Configuration fields:

``path`` : filepath (required)
    The location of the mbox file.  If the file does not exist, it will be
    created when the sender object is entered.

Example ``mbox`` configuration:

.. code:: toml

    [outgoing]
    method = "mbox"
    path = "~/MAIL/inbox"


``maildir``
~~~~~~~~~~~

The ``maildir`` method adds e-mails to a Maildir mailbox directory on the local
machine.

Configuration fields:

``path`` : directory path (required)
    The location of the Maildir mailbox.  If the directory does not exist, it
    will be created when the sender object is entered.

``folder`` : string (optional)
    A folder within the Maildir mailbox in which to place e-mails


``mh``
~~~~~~

The ``mh`` method adds e-mails to an MH mailbox directory on the local machine.

Configuration fields:

``path`` : directory path (required)
    The location of the MH mailbox.  If the directory does not exist, it will
    be created when the sender object is entered.

``folder`` : string or list of strings (optional)
    A folder within the Maildir mailbox in which to place e-mails; can be
    either the name of a single folder or a path through nested folders &
    subfolders

Example configuration:

.. code:: toml

    [outgoing]
    method = "mh"
    path = "~/mail"
    # Place e-mails inside the "work" folder inside the "important" folder:
    folder = ["important", "work"]


``mmdf``
~~~~~~~~

The ``mmdf`` method adds e-mails to an MMDF mailbox file on the local machine.

Configuration fields:

``path`` : filepath (required)
    The location of the MMDF mailbox.  If the file does not exist, it will be
    created when the sender object is entered.


``babyl``
~~~~~~~~~

The ``babyl`` method adds e-mails to a Babyl mailbox file on the local machine.

Configuration fields:

``path`` : filepath (required)
    The location of the Babyl mailbox.  If the file does not exist, it will be
    created when the sender object is entered.


``null``
~~~~~~~~

Goes nowhere, does nothing, ignores all configuration keys.

Example ``null`` configuration:

.. code:: toml

    [outgoing]
    # Just send my e-mails into a black hole
    method = "null"


.. _passwords:

Passwords
---------

When a sending method calls for a password, API key, or other secret, there are
several ways to specify the value.

Using a string, naturally, supplies the value of that string as the password:

.. code:: toml

    password = "hunter2"

Alternatively, passwords may instead be looked up in external resources.  This
is done by setting the value of the password field to a table with a single
key-value pair, where the key identifies the password lookup scheme and the
value is either a string or a sub-table, depending on the scheme.

The builtin password schemes are as follows.  Extension packages can define
additional password schemes.


``base64``
~~~~~~~~~~

For slightly more security than a plaintext password, a password can be stored
in base64 by specifying a table with a single ``base64`` key and the encoded
password as the value:

.. code:: toml

    password = { base64 = "aHVudGVyMg==" }

Base64 passwords must decode to UTF-8 text.


``file``
~~~~~~~~

A password can be read from a file by specifying a table with a single ``file``
key and the filepath as the value:

.. code:: toml

    password = { file = "path/to/file" }

The entire contents of the file, minus any leading or trailing whitespace, will
then be used as the password.  As with paths elsewhere in the configuration
file, the path may start with a tilde, and relative paths are resolved relative
to the directory containing the configuration file.


``env``
~~~~~~~

A password can be read from an environment variable by specifying a table with
a single ``env`` key and the name of the environment variable as the value:

.. code:: toml

    password = { env = "PROTOCOL_PASSWORD" }


``dotenv``
~~~~~~~~~~

Passwords can be read from a key in a :file:`.env`-style file as supported by
python-dotenv_ like so:

.. _python-dotenv: https://github.com/theskumar/python-dotenv

.. code:: toml

    password = { dotenv = { key = "NAME_OF_KEY_IN_FILE", file = "path/to/file" } }

The ``file`` path is resolved following the same rules as other paths.  If the
``file`` field is omitted, the given key will be looked up in a file named
``.env`` in the same directory as the configuration file.


``keyring``
~~~~~~~~~~~

Passwords can be retrieved from the system keyring using keyring_.  The basic
format is:

.. _keyring: https://github.com/jaraco/keyring

.. code:: toml

    password = { keyring = { service = "host_or_service_name", username = "your_username" } }

If the ``service`` key is omitted, the value will default to the sending
method's host value, if it has one; likewise, an omitted ``username`` will
default to the username for the sending method, if there is one.  A specific
keyring backend can be specified with the ``backend`` key, and the directory
from which to load the backend can be specified with the ``keyring-path`` key.
