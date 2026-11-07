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

The last fixture here is not a guard. `slot_rows` is the slot rule's table,
which two test files read because the rule itself is written twice.
"""

import json
import socket
from pathlib import Path

import pytest

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


#: The addresses the guard below lets through. asyncio wakes its own event
#: loop through a socket pair, and on Windows CPython builds one by connecting
#: a socket to a listening socket on `127.0.0.1`
#: (`socket._fallback_socketpair`). `tests/test_api.py` runs the FastAPI
#: application in process, which starts an event loop, so refusing this would
#: mean no test could reach the API at all.
#:
#: It is not a hole in the guarantee the guard is for. Nothing in this repo
#: serves on a port, and watsonx, Watson Text to Speech and StatsBomb are all
#: somewhere else, so a loopback connection cannot reach any of them. Every
#: other address still refuses, and so does `urlopen`, whatever it is given.
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})

#: Kept before the guard replaces it, so a loopback connection can still be
#: made by the real method.
_REAL_CONNECT = socket.socket.connect


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

    The one address it lets through is loopback, for the reason recorded on
    `LOOPBACK_HOSTS`: an event loop has to be able to wake itself, and no
    service this repo talks to is on this machine.
    """

    def blocked(what):
        def refuse(*args, **kwargs):
            raise NetworkCallInTest(
                f"a test tried to open a network connection through {what} "
                f"with {args[:1]}. Tests replay responses from tests/golden/; "
                "see tests/conftest.py."
            )

        return refuse

    def connect(self, address, *args, **kwargs):
        host = address[0] if isinstance(address, tuple) else None
        if host in LOOPBACK_HOSTS:
            return _REAL_CONNECT(self, address, *args, **kwargs)
        raise NetworkCallInTest(
            "a test tried to open a network connection through socket.connect "
            f"with {address!r}. Tests replay responses from tests/golden/; "
            "see tests/conftest.py."
        )

    monkeypatch.setattr(
        "urllib.request.urlopen", blocked("urllib.request.urlopen")
    )
    monkeypatch.setattr(socket.socket, "connect", connect)


SLOT_ROWS = Path(__file__).resolve().parent / "slot_rows.json"


@pytest.fixture
def slot_rows():
    """The seven rows of the slot rule, from `tests/slot_rows.json`.

    The rule is written twice, once for the browser in
    `app/web/match-content.js` and once for the hosted API in `app/api.py`,
    so the table it answers lives in neither suite. `tests/test_api.py` runs
    each row through the Python copy and through `GET /buildup`;
    `tests/test_narrator_picker.py` reads each row against `hero.voice_for`
    and `hero.audio` in `app/web/matches.json`, which is what the browser's
    copy indexes. Handed over as a fixture for the reason
    `network_call_error` is: both files get this one object rather than their
    own parse of it.
    """
    with SLOT_ROWS.open(encoding="utf-8") as handle:
        return json.load(handle)["rows"]
