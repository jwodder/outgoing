.. currentmodule:: outgoing

Changelog
=========

v0.6.3 (2025-11-16)
-------------------
- Support Python 3.14
- Drop support for Python 3.8 and 3.9
- Drop ``click`` and ``click-loglevel`` dependencies

v0.6.2 (2025-08-02)
-------------------
- Support Python 3.13
- Exclude click v8.2.2 from dependencies due to breakage caused by
  <https://github.com/pallets/click/issues/3024>

v0.6.1 (2024-05-08)
-------------------
- Support platformdirs v4.0
- Migrated from setuptools to hatch
- Drop support for Python 3.7

v0.6.0 (2023-10-30)
-------------------
- Support python-dotenv v1.0
- Always read JSON configuration files using UTF-8 encoding
- Always read files for the "file" password method using UTF-8 encoding
- Support Python 3.12
- Correct the default Linux config file location listed in the README
- Update pydantic to v2.0

v0.5.0 (2023-02-09)
-------------------
- Update ``platformdirs`` dependency to v3.  This is a **breaking** change on
  macOS, where the default configuration path changes from
  :file:`~/Library/Preferences/outgoing/outgoing.toml` back to
  :file:`~/Library/Application Support/outgoing/outgoing.toml`.

v0.4.0 (2022-10-25)
-------------------
- Drop support for Python 3.6
- Support Python 3.11
- Use `tomllib` on Python 3.11

v0.3.2 (2022-09-03)
-------------------
- Overload ``Password.__eq__`` so that instances continue to compare equal to
  ``pydantic.SecretStr`` instances even under pydantic 1.10

v0.3.1 (2022-01-02)
-------------------
- Support tomli 2.0

v0.3.0 (2021-10-31)
-------------------
- Support Python 3.10
- Replaced ``entrypoints`` dependency with ``importlib-metadata``
- Replaced ``appdirs`` dependency with ``platformdirs``.  This is a
  **breaking** change on macOS, where the default configuration path changes
  from :file:`~/Library/Application Support/outgoing/outgoing.toml` to
  :file:`~/Library/Preferences/outgoing/outgoing.toml`.

v0.2.5 (2021-09-27)
-------------------
- `outgoing.errors.UnsupportedEmailError` is now re-exported as
  `outgoing.UnsupportedEmailError` like all the other exception classes

v0.2.4 (2021-08-02)
-------------------
- Update for tomli 1.2.0

v0.2.3 (2021-07-04)
-------------------
- Read TOML files in UTF-8

v0.2.2 (2021-07-02)
-------------------
- Switch from toml to tomli

v0.2.1 (2021-05-12)
-------------------
- Support Click 8

v0.2.0 (2021-03-14)
-------------------
- Require the ``port`` field of ``SMTPSender`` to be non-negative
- Mark `Sender` as ``runtime_checkable`` and export it
- Gave the :command:`outgoing` command ``--section``, ``--no-section``, and
  ``--log-level`` options
- Added logging to built-in sender classes
- The :command:`outgoing` command now loads settings from :file:`.env` files
  and has an ``--env`` option

v0.1.0 (2021-03-06)
-------------------
Initial release
