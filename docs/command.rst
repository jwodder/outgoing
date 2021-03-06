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
