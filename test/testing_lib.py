from email.message import EmailMessage
from typing import Iterable, Optional
import pytest


def assert_emails_eq(
    msg1: EmailMessage,
    msg2: EmailMessage,
    extra_headers: Optional[Iterable[str]] = None,
) -> None:
    __tracebackhide__ = True
    headers = ["Subject", "From", "To", "CC", "BCC"]
    if extra_headers is not None:
        headers.extend(extra_headers)
    for h in headers:
        if msg1[h] != msg2[h]:
            pytest.fail(f"{h} headers differ: {msg1[h]!r} vs. {msg2[h]!r}")
    assert_mimes_eq(msg1, msg2)


def assert_mimes_eq(msg1: EmailMessage, msg2: EmailMessage) -> None:
    __tracebackhide__ = True
    ct1 = msg1.get_content_type()
    ct2 = msg2.get_content_type()
    if ct1 != ct2:
        pytest.fail(f"Content-Types differ: {ct1!r} vs. {ct2!r}")
    if msg1.is_multipart() != msg1.is_multipart():
        if msg1.is_multipart():
            pytest.fail("Left message is multipart but right message is not")
        else:
            pytest.fail("Right message is multipart but left message is not")
    if msg1.is_multipart():
        parts1 = list(msg1.iter_parts())
        parts2 = list(msg2.iter_parts())
        if len(parts1) != len(parts2):
            pytest.fail(
                f"Left message has more parts ({len(parts1)}) than right"
                f" message ({len(parts2)})"
            )
        for p1, p2 in zip(parts1, parts2):
            assert isinstance(p1, EmailMessage)
            assert isinstance(p2, EmailMessage)
            assert_mimes_eq(p1, p2)
    else:
        body1 = msg1.get_content()
        body2 = msg2.get_content()
        if body1 != body2:
            pytest.fail(f"Contents differ: {body1!r} vs. {body2!r}")
