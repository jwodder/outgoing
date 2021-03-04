import email
from email import policy
from email.message import EmailMessage
from typing import IO, cast


def msg_factory(fp: IO[bytes]) -> EmailMessage:
    return cast(EmailMessage, email.message_from_binary_file(fp, policy=policy.default))
