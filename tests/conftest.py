"""Suite-wide guards: no test opens a connection, and none reads the real
credentials file.

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

The second guard is about credentials rather than the network. It is documented
on the fixture below.
"""

import socket

import pytest

import app.orchestrator  # noqa: F401 — patches app.orchestrator_contract functions
from app.credentials import ENV_FILE_VARIABLE


@pytest.fixture(autouse=True)
def no_real_credentials(monkeypatch, tmp_path):
    """Point every test at a credentials file that does not exist.

    The live file is outside the repo and holds real keys, so no test may read
    it. One code path would have: a missing-credential report asks
    `app.credentials.describe` which file it looked in, and the default is the
    real one. The report carries variable names and never values, so nothing
    would have leaked, but opening it at all is what the rule forbids.

    Pointing `PRELUDE_ENV_FILE` at an absent path under pytest's own temporary
    directory means a test that loads credentials gets the process environment
    and nothing else, whichever path reached the loader. The path is outside
    the repo, which the loader requires.
    """
    monkeypatch.setenv(ENV_FILE_VARIABLE, str(tmp_path / "absent.env"))


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
