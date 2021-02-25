`outgoing`: Python module for abstracting e-mail sending

- Sending methods to support:
    - sendmail
        - config option: command — shell command (`shell=True`; defaults to
          `sendmail -i -t`)
    - SMTP
        - config options:
            - host
            - username
            - password
            - port (optional)
            - ssl - bool or "starttls"
    - mbox
        - config option: path
    - Maildir
        - config options:
            - path
            - mailbox (optional?)
    - MH mailbox
        - config options:
            - path
            - mailbox (optional?)
    - Babyl mailbox?
    - MMDF mailbox?
    - IMAP?
    - Sendgrid (plugin)
    - Mailgun (plugin)
    - Mail Chimp? (plugin)
    - Gmail (plugin)
    - Amazon? (plugin)

- Include a command-line entry point that reads an e-mail from standard input
  and sends it

- API:
    - Each supported sending method is implemented as an entry point that is a
      callable that takes a configuration `dict` and returns a sender object.
      The `dict` will contain a "method" key giving the name of the sending
      method used to look up the entry point.  Unless the entry point supports
      multiple methods at once, it should generally be ignored.  The functions
      should also ignore unknown/extra fields.
        - The callable should (must?) also accept a `configpath` parameter
          giving the location of the file from which the config was read so
          that relative paths inside the config can be resolved

    - Sender objects must support the following:
        - use as a context manager
        - a `send(msg: EmailMessage) -> Any` method (for calling within the
          context manager; calling outside the manager is undefined)

    - The library provides the following functions for constructing senders:
        - `sender_from_dict(d: dict, configpath=None)`
            - The `dict` must contain a "method" key
        - `sender_from_file(filename, section='outgoing')` — Reads the given
          file (format determined based on file extension), selects the given
          section/subdict, looks up the method, and passes the config to
          `sender_from_dict()`
            - Add an option for falling back to the default config file?

    - The library provides the following function for use by sender authors:

            resolve_password(
                spec: Union[dict, str],
                host=None,
                username=None,
                configpath=None,
            ) -> str

        where `spec` is the value of a "password" field from the configuration,
        `host` and `username` (if specified) are the host & username given in
        the outgoing configuration (for use as default values for those fields
        if the password resolution needs them and they're not in `spec`), and
        `configpath` is the path to the configuration file

        - Some sending methods (e.g., sendgrid) do not take a `host`
          configuration option but still pass a fixed string (e.g.,
          `api.sendgrid.com` or whatever) as the `host` value to
          `resolve_password()`

    - Exceptions:
        - [invalid config]
            - Sender entrypoints can also raise ValueErrors and TypeErrors;
              these are converted into the invalid config error type by the
              `sender_from_*` functions
        - [unknown sending method]
        - [unknown password provider]
        - [invalid password spec]
        - [invalid e-mail/e-mail structure not supported by sending method]
        - [sending error?]

- Configuration is read from a TOML file, so that type information is available
    - The "password" field can then be supplied as either a string (for the
      actual password) or a dict with one key, giving the name of the provider
      method, e.g.:

        - `password = { keyring = {} }`
        - `password = { keyring = { service = "foo", username = "bar" } }`
        - `password = { keyring = { service = "foo", username = "bar", backend = "foo.bar", keyring-path = "quux/baz" } }`
        - `password = { file = "~/path/to/file" }`
        - `password = { env = "ENV_VAR" }`
        - `password = { netrc = {} }`
        - `password = { netrc = { file = "~/path/to/file", machine = "bar.com",
          login = "foo" } }`
            - Call the arguments `host` and `username` instead so that they
              align with the arguments to the `resolve_password()` function?

    - Also support JSON and/or YAML?  Support YAML via an extra?
    - Support defining more password providers through entry points

- Should the config file support multiple "profiles"?

- cf. `marrow.mailer`? `mailshake`?
