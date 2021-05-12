.. currentmodule:: outgoing

Changelog
=========

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
