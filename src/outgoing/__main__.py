from email import message_from_bytes, policy
from email.message import EmailMessage
from typing import IO, List, Optional
import click
from . import __version__, from_config_file, get_default_configpath
from .errors import Error


@click.command()
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
    show_default=True,
)
@click.option("message", type=click.File("rb"), nargs=-1)
@click.pass_context
def main(ctx: click.Context, message: List[IO[bytes]], config: Optional[str]) -> None:
    """
    Common interface for different e-mail methods.

    Visit <https://github.com/jwodder/outgoing> for more information.
    """

    if not message:
        message = [click.get_binary_stream("stdin")]
    try:
        with from_config_file(config, fallback=False) as sender:
            for fp in message:
                msg = message_from_bytes(fp.read(), policy=policy.default)
            assert isinstance(msg, EmailMessage)
            sender.send(msg)
    except Error as e:
        ctx.fail(str(e))


if __name__ == "__main__":
    main()
