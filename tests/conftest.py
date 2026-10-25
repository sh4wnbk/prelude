"""Suite-wide guard: no test opens a network connection.

The narration tests replay recorded and schema-built responses from
`tests/golden/` rather than calling a model, and the EventFeed tests read
`data/raw/` off disk. So nothing in the suite has a reason to reach the
network, and a test that starts doing so has either grown a dependency on a
running service or is about to spend money on a watsonx call.

Asserting that by hand in each test would only cover the paths somebody
remembered. This blocks the two places a connection can actually be opened, for
every test, so the guarantee holds for tests nobody has written yet.

`scripts/record_narration_golden.py` is the one thing in the repo that does
call a model. It is a script, not a test, so it never passes through here.
"""

import socket

import pytest


class NetworkCallInTest(RuntimeError):
    """A test tried to open a connection."""


@pytest.fixture
def network_call_error():
    """The exception the guard raises, for a test that wants to assert on it.

    Handed over as a fixture rather than imported. pytest loads this file as
    top-level `conftest`, so a test importing `tests.conftest` gets a second,
    separate module object whose `NetworkCallInTest` is a different class, and
    `pytest.raises` on it does not catch what the guard actually threw. Asking
    for it by fixture means the test always gets the live one.
    """
    return NetworkCallInTest


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Fail any test that tries to reach the network.

    Both hooks matter. `urlopen` is what `app/narration_provider.py` calls, so
    blocking it gives the clearest message. `socket.socket.connect` is the
    floor underneath every other client library, so blocking it covers a
    backend added later that does not go through `urllib`.
    """

    def blocked(what):
        def refuse(*args, **kwargs):
            raise NetworkCallInTest(
                f"a test tried to open a network connection through {what} "
                f"with {args[:1]}. Tests replay responses from tests/golden/; "
                "see tests/conftest.py."
            )

        return refuse

    monkeypatch.setattr(
        "urllib.request.urlopen", blocked("urllib.request.urlopen")
    )
    monkeypatch.setattr(socket.socket, "connect", blocked("socket.connect"))
