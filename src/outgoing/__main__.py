from __future__ import annotations
from email import message_from_binary_file, policy
from email.message import EmailMessage
import logging
from typing import Any, IO, Optional
import click
from click_loglevel import LogLevel
from dotenv import find_dotenv, load_dotenv
from . import (
    DEFAULT_CONFIG_SECTION,
    __version__,
    from_config_file,
    get_default_configpath,
)
from .errors import Error

NO_SECTION = object()


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(
    __version__,
    "-V",
    "--version",
    message="%(prog)s %(version)s",
)
@click.option(
    "-c",
    "--config",
    type=click.Path(dir_okay=False),
    default=get_default_configpath(),
    help="Specify the outgoing configuration file to use",
    show_default=True,
)
@click.option(
    "-E",
    "--env",
    type=click.Path(exists=True, dir_okay=False),
    help="Load environment variables from given .env file",
)
@click.option(
    "-l",
    "--log-level",
    type=LogLevel(),
    default="INFO",
    help="Set logging level",
    show_default=True,
)
@click.option(
    "-s",
    "--section",
    help=(
        "Read configuration from the given key/section of the config file"
        f"  [default: {DEFAULT_CONFIG_SECTION}]"
    ),
    metavar="KEY",
    type=click.UNPROCESSED,
)
@click.option(
    "--no-section",
    "section",
    flag_value=NO_SECTION,
    type=click.UNPROCESSED,
    help="Read configuration from the root of the config file",
)
@click.argument("message", type=click.File("rb"), nargs=-1)
@click.pass_context
def main(
    ctx: click.Context,
    message: list[IO[bytes]],
    config: Optional[str],
    section: Any,
    log_level: int,
    env: Optional[str],
) -> None:
    """
    Common interface for different e-mail methods.

    Visit <https://github.com/jwodder/outgoing> for more information.
    """
    if env is None:
        # dotenv's default behavior doesn't play well with
        # click.testing.CliRunner, so we have to force the library to start
        # searching at the current directory.
        env = find_dotenv(usecwd=True)
    load_dotenv(env)
    logging.basicConfig(
        format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        level=log_level,
    )
    sectname: Optional[str]
    if section is NO_SECTION:
        sectname = None
    elif section is None:
        sectname = DEFAULT_CONFIG_SECTION
    else:
        assert isinstance(section, str)
        sectname = section
    if not message:
        message = [click.get_binary_stream("stdin")]
    try:
        with from_config_file(config, section=sectname, fallback=False) as sender:
            for fp in message:
                with fp:
                    msg = message_from_binary_file(fp, policy=policy.default)
                assert isinstance(msg, EmailMessage)
                sender.send(msg)
    except Error as e:
        ctx.fail(str(e))


if __name__ == "__main__":
    main()  # pragma: no cover
