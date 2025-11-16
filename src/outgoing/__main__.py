from __future__ import annotations
import argparse
from dataclasses import dataclass
from email import message_from_binary_file, policy
from email.message import EmailMessage
import logging
from pathlib import Path
import sys
from dotenv import find_dotenv, load_dotenv
from . import (
    DEFAULT_CONFIG_SECTION,
    __version__,
    from_config_file,
    get_default_configpath,
)
from .errors import Error

LOG_LEVELS = ["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


@dataclass
class Command:
    config: Path
    env: str | None
    log_level: int
    section: str | None
    messages: list[str]

    @classmethod
    def from_args(cls, argv: list[str] | None = None) -> Command:
        parser = argparse.ArgumentParser(
            description=(
                "Common interface for different e-mail methods.\n"
                "\n"
                "Visit <https://github.com/jwodder/outgoing> for more information."
            ),
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        default_config = get_default_configpath()
        parser.add_argument(
            "-c",
            "--config",
            type=Path,
            default=default_config,
            help=(
                "Specify the outgoing configuration file to use"
                f"  [default: {default_config}]"
            ),
        )
        parser.add_argument(
            "-E",
            "--env",
            help="Load environment variables from given .env file",
        )
        parser.add_argument(
            "-l",
            "--log-level",
            type=parse_log_level,
            default="INFO",
            help="Set logging level  [default: INFO]",
            metavar="[" + "|".join(LOG_LEVELS) + "]",
        )
        parser.add_argument(
            "-s",
            "--section",
            default=DEFAULT_CONFIG_SECTION,
            help=(
                "Read configuration from the given key/section of the config file"
                f"  [default: {DEFAULT_CONFIG_SECTION}]"
            ),
            metavar="KEY",
        )
        parser.add_argument(
            "--no-section",
            dest="section",
            action="store_const",
            const=None,
            help="Read configuration from the root of the config file",
        )
        parser.add_argument(
            "-V", "--version", action="version", version=f"%(prog)s {__version__}"
        )
        parser.add_argument(
            "messages",
            nargs="*",
            default=["-"],
            help=(
                "Files containing MIME e-mail documents to send; if not"
                " specified, input is read from stdin"
            ),
        )
        args = parser.parse_args(argv)
        return cls(
            config=args.config,
            env=args.env,
            log_level=args.log_level,
            section=args.section,
            messages=args.messages,
        )

    def run(self) -> int:
        if self.env is None:
            self.env = find_dotenv(usecwd=True)
        load_dotenv(self.env)
        logging.basicConfig(
            format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
            level=self.log_level,
        )
        try:
            with from_config_file(
                self.config, section=self.section, fallback=False
            ) as sender:
                for path in self.messages:
                    if path == "-":
                        fp = sys.stdin.buffer
                    else:
                        fp = open(path, "rb")
                    with fp:
                        # <https://github.com/python/typeshed/issues/13273>
                        msg = message_from_binary_file(fp, policy=policy.default)  # type: ignore[arg-type]
                    assert isinstance(msg, EmailMessage)
                    sender.send(msg)
        except Error as e:
            print(e, file=sys.stderr)
            return 1
        return 0


def main(argv: list[str] | None = None) -> int:
    return Command.from_args(argv).run()


def parse_log_level(level: str) -> int:
    """
    Convert a log level name (case-insensitive) or number to its numeric value
    """
    try:
        return int(level)
    except ValueError:
        levelup = level.upper()
        if levelup in LOG_LEVELS:
            ll = getattr(logging, levelup)
            assert isinstance(ll, int)
            return ll
        else:
            raise ValueError(f"Invalid log level: {level!r}")


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
