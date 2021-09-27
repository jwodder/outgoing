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
