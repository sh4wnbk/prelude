r"""Record one real speech exchange, so a test can replay it.

`tests/golden/ollama_development_model.json` is a recording of a real Ollama
exchange and `tests/test_narration_provider.py` replays it. This is the same
thing for the speech backend, and it exists for the same reason: a backend
tested only against a response written by hand is a backend tested against
what its author expected.

**What it records, and what it does not.**

| Recorded | Why |
| -------- | --- |
| the request `app/tts.py` built | a recording is worth nothing if the replay sends something else |
| the response's length and SHA-256 | the whole response, identified without being stored |
| the first `HEADER_BYTES` bytes of the response | the RIFF header and the start of the audio, which is the part a test can read |

**It does not record the audio.** Around 90 KB of speech in the repo would
prove nothing a test could check: `app/tts.py` returns the bytes the service
sent without examining them, so what a replay has to assert is that it returns
exactly what it was handed, and a hundred bytes do that as well as a hundred
thousand. The header slice is still a real recording of a real response, and
the fixture says in its own provenance block exactly what it is.

**It records no credential.** `SpeechRequest` carries the path, the query and
the body and not the host, because `TTS_URL` holds an instance id, and its
`Authorization` header is `REDACTED` because the real one is built inside
`send` and never leaves it.

**It costs one call.** The text is short and fixed, and the plan prints its
length two ways before anything is sent: the submitted length and the spoken
text alone, with what IBM bills between them. Nothing is sent without
`--confirm`.

Run it:

    .\.venv-prelude\Scripts\python.exe -I scripts\record_tts_golden.py --plan
    .\.venv-prelude\Scripts\python.exe -I scripts\record_tts_golden.py --confirm

Standard library only.
"""

import argparse
import base64
import hashlib
import json
import sys
import urllib.error
from datetime import date
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# The pronunciation table holds IPA and this script prints the request it
# built. A Windows console is cp1252 by default, which cannot encode "liːd",
# so printing the request would raise instead of printing it.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.orchestrator_contract import NEUTRAL, STORYTELLER  # noqa: E402
from app.tts import WatsonTextToSpeech, without_markup  # noqa: E402

#: Where the fixture goes, beside the other two goldens.
GOLDEN = ROOT / "tests" / "golden" / "tts_synthesize.json"

#: The text to record. Short, fixed, and chosen to carry one pronunciation:
#: "lead" is why `app/pronunciation.py` exists, so the recorded request is one
#: that shows the markup actually reaching the service.
HEADER = "Argentina take the lead."
NARRATION = "Maradona shot."

#: The persona and situation recorded. The Storyteller is what a listener with
#: no side gets by default, from `default_persona` in `app/orchestrator.py`,
#: so this is the shipped path rather than a corner of it.
PERSONA = STORYTELLER
SITUATION = NEUTRAL

#: How much of the response body is kept. Enough for the RIFF header, the
#: `fmt ` chunk, the `LIST` chunk the service sends and the start of the
#: audio, which is every part of it a test has anything to say about.
HEADER_BYTES = 128


def plan(backend: WatsonTextToSpeech) -> int:
    """Print the request and what it costs, and return the submitted length."""
    request = backend.request_for(HEADER, NARRATION, PERSONA, SITUATION)
    print("one call, {} in the {} situation".format(PERSONA, SITUATION))
    print("  path:  {}".format(request.path))
    print("  query: {}".format(request.query))
    print("  text:  {}".format(request.text))
    print("  {} characters submitted, markup counted".format(
        request.billable_characters
    ))
    print("  {} characters spoken, markup not counted".format(
        len(without_markup(request.text))
    ))
    return request.billable_characters


def record(backend: WatsonTextToSpeech) -> dict:
    """Send the one request and build the fixture."""
    request = backend.request_for(HEADER, NARRATION, PERSONA, SITUATION)
    audio = backend.send(request)
    return {
        "provenance": {
            "what": (
                "a real exchange with IBM Watson Text to Speech, recorded by "
                "scripts/record_tts_golden.py"
            ),
            "recorded": date.today().isoformat(),
            "is_a_recording": True,
            "response_body_is": (
                "the first {} bytes of the response, which is the RIFF "
                "header and the start of the audio".format(HEADER_BYTES)
            ),
            "response_is_not": (
                "the whole response. app/tts.py returns the bytes the service "
                "sent without examining them, so what a replay asserts is "
                "that it returns exactly what it was handed, and the audio "
                "itself would add nothing a test could check"
            ),
            "holds_no_credential": (
                "the host is not in the request, because TTS_URL carries an "
                "instance id, and the Authorization header is redacted "
                "because the real one is built inside send and never leaves it"
            ),
            "persona": PERSONA,
            "situation": SITUATION,
            "header": HEADER,
            "narration": NARRATION,
        },
        "request": request.as_recorded(),
        "response": {
            "bytes": len(audio),
            "sha256": hashlib.sha256(audio).hexdigest(),
            "head_base64": base64.b64encode(audio[:HEADER_BYTES]).decode(
                "ascii"
            ),
            "head_bytes": min(HEADER_BYTES, len(audio)),
        },
    }


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--plan",
        action="store_true",
        help="print the request and its cost, and make no call",
    )
    parser.add_argument(
        "--confirm", action="store_true", help="send it; this is the paid path"
    )
    parser.add_argument("--out", type=Path, default=GOLDEN)
    args = parser.parse_args(argv)

    backend = WatsonTextToSpeech()
    plan(backend)
    if args.plan or not args.confirm:
        print()
        print("nothing was sent. --confirm is what sends it.")
        return 0

    print()
    try:
        fixture = record(backend)
    except urllib.error.HTTPError as failure:
        detail = failure.read().decode("utf-8", "replace").strip()
        print("HTTP {} {}: {}".format(failure.code, failure.reason, detail),
              file=sys.stderr)
        return 1
    args.out.write_text(
        json.dumps(fixture, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print("the service sent {} bytes, sha256 {}".format(
        fixture["response"]["bytes"], fixture["response"]["sha256"][:16]
    ))
    print("recorded {} of them to {}".format(
        fixture["response"]["head_bytes"], args.out
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
