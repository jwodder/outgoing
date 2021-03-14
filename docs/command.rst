.. index:: outgoing (command)

Command-Line Program
====================

::

    outgoing [<options>] [<msg-file> ...]

You can use ``outgoing`` to send fully-composed e-mails directly from the
command line with the :command:`outgoing` command.  Save your e-mail as a
complete :mimetype:`message/rfc822` document and then run ``outgoing
path/to/email/file`` to send it using the configuration in the default config
file (or specify another config file with the ``--config`` option).  Multiple
files can be passed to the command at once to send multiple e-mails.  If no
files are specified on the command line, the command reads an e-mail from
standard input.

Options
-------

.. program:: outgoing

.. option:: -c <file>, --config <file>

    Specify a :ref:`configuration file <configfile>` to use instead of the
    default configuration file

.. option:: -s <key>, --section <key>

    .. versionadded:: 0.2.0

    Read the configuration from the given table or key in the configuration
    file; defaults to "``outgoing``"

.. option:: --no-section

    .. versionadded:: 0.2.0

    Read the configuration fields from the top level of the configuration file
    instead of expecting them to all be contained below a certain table/key
