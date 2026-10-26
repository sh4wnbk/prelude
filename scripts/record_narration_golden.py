r"""Record a real Ollama response into tests/golden/, for the tests to replay.

`tests/test_narration_provider.py` must not open a socket, so it replays a
recorded response instead of calling a model. This script is what records one.
It is run by hand and is not part of the test suite; `scripts/narrate_once.py`
is the other script that calls a model, and it records nothing.

It needs a local Ollama server with the development model pulled:

    ollama pull granite4:micro
    .\.venv-prelude\Scripts\python.exe -I scripts\record_narration_golden.py

What it writes is the one request that was sent and the one response that came
back, both verbatim, plus a provenance block saying it is a recording. The
replaying test rebuilds the request from `OllamaProvider.payload` and asserts
it matches the recorded one, so a change to the request body fails the test
rather than quietly invalidating the recording.

There is no equivalent recorder for watsonx. That would mean a paid call
against live credentials, which `CLAUDE.md` puts out of reach, so
`tests/golden/watsonx_text_generation.json` is built from IBM's published
schema and says so in its own provenance block. The citations are in
`docs/narration.md`.
"""

import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.narration_provider import OLLAMA_HOST, OllamaProvider, post  # noqa: E402

GOLDEN = ROOT / "tests" / "golden" / "ollama_development_model.json"

# Fixed, so a re-recording is comparable to the one before it. This exercises
# the transport and the response shape, not narration quality: nothing in the
# repo builds a narration prompt yet.
PROMPT = "Reply with one short sentence about a football match."


def server_version(host: str) -> str:
    """The server's own version, so the recording says what produced it.

    Read over HTTP rather than from `ollama --version`, because the executable
    is not always on PATH and the server is what answered the call anyway.
    """
    try:
        with urllib.request.urlopen(f"{host}/api/version", timeout=10) as answer:
            return json.loads(answer.read().decode("utf-8")).get("version", "unknown")
    except (OSError, ValueError) as exc:
        return f"unknown ({exc})"


def main() -> int:
    captured: dict[str, object] = {}

    def recording_transport(url, body, headers):
        """The real transport, keeping both sides of the exchange."""
        response = post(url, body, headers)
        captured["request"] = {
            "url": url,
            "headers": dict(headers),
            "payload": json.loads(body.decode("utf-8")),
        }
        captured["response"] = response
        return response

    feed = OllamaProvider(transport=recording_transport)
    print(f"calling {feed.url} with {feed.model}, options {feed.options}")
    print("a CPU-only generation takes a while; waiting")

    narration = feed.narrate(PROMPT)

    GOLDEN.parent.mkdir(parents=True, exist_ok=True)
    GOLDEN.write_text(
        json.dumps(
            {
                "provenance": {
                    "kind": "recording",
                    "source": "a live call to a local Ollama server",
                    "recorded_by": "scripts/record_narration_golden.py",
                    "recorded_at": datetime.now(timezone.utc)
                    .replace(microsecond=0)
                    .isoformat(),
                    "ollama_version": server_version(feed.host or OLLAMA_HOST),
                },
                "prompt": PROMPT,
                "request": captured["request"],
                "response": captured["response"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print(f"\nwrote {GOLDEN.relative_to(ROOT)}")
    print(f"{narration.model} returned {len(narration.text)} characters")
    return 0


if __name__ == "__main__":
    sys.exit(main())
