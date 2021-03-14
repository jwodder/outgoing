v0.2.0 (2021-03-14)
-------------------
- Require the `port` field of `SMTPSender` to be non-negative
- Mark `Sender` as `runtime_checkable` and export it
- Gave the `outgoing` command `--section`, `--no-section`, and `--log-level`
  options
- Added logging to built-in sender classes
- The `outgoing` command now loads settings from `.env` files and has an
  `--env` option

v0.1.0 (2021-03-06)
-------------------
Initial release
