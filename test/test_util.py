from pydantic import Field
from outgoing.util import OpenClosable


class OpenCloser(OpenClosable):
    calls: list[str] = Field(default_factory=list)

    def open(self) -> None:
        self.calls.append("open")

    def close(self) -> None:
        self.calls.append("close")


def test_openclosable() -> None:
    oc = OpenCloser()
    assert oc.model_dump() == {"calls": []}
    assert oc._context_depth == 0
    with oc as oc2:
        assert oc is oc2
        assert oc.calls == ["open"]
        assert oc._context_depth == 1
        with oc:
            assert oc.calls == ["open"]
            assert oc._context_depth == 2
            with oc:
                assert oc.calls == ["open"]
                assert oc._context_depth == 3
            assert oc.calls == ["open"]
            assert oc._context_depth == 2
        assert oc.calls == ["open"]
        assert oc._context_depth == 1
    assert oc.calls == ["open", "close"]
    assert oc._context_depth == 0
