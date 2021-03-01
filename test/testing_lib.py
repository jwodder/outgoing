import email
from email import policy
from email.message import EmailMessage
from typing import IO, cast


def msg_factory(fp: IO[bytes]) -> EmailMessage:
    return cast(EmailMessage, email.message_from_binary_file(fp, policy=policy.default))


test_email1 = EmailMessage()
test_email1["Subject"] = "Meet me"
test_email1["To"] = "my.beloved@love.love"
test_email1["From"] = "me@here.qq"
test_email1.set_content(
    "Oh my beloved!\n"
    "\n"
    "Wilt thou dine with me on the morrow?\n"
    "\n"
    "We're having hot pockets.\n"
    "\n"
    "Love, Me\n"
)

test_email2 = EmailMessage()
test_email2["Subject"] = "No."
test_email2["To"] = "me@here.qq"
test_email2["From"] = "my.beloved@love.love"
test_email2.set_content(
    "Hot pockets?  Thou disgusteth me.\n\nPineapple pizza or RIOT.\n"
)
