r"""The hero recordings the site ships: three listeners, two matches, six MP3s.

`hero.voice_for` in `app/web/matches.json` already says which recording each
listener hears: `mate_scored` for a fan of the side that scored,
`mate_conceded` for a fan of the side that conceded, `storyteller_neutral` for
a fan with no side. `scripts/write_headers.py` computes those keys and the
moment card's player looks its answer up in `hero.audio`. This script is what
fills that map: one file per key per match, under
`app/web/assets/audio/<match_id>_<key>.mp3`.

**The header is the orchestrator's and the narration is the one this
listener reads.** The header comes through `openings` in
`scripts/write_headers.py`, with no listener name in it. The narration is
read from `app/web/narrations.json` under `slots`, one per
`hero.voice_for` key: six narrations written by the team and verified by the
grounding check, which the moment card shows by the same lookup this script
records them by. So a fan hears the words they just read, in the voice their
own narrator speaks.

It used to be one narration per goal spoken three ways, and before that
`template_narration`, the fallback assembled out of the numbered facts, which
is what the hero samples in `scripts/tts_samples.py` still speak: those are
for judging the voices, where the words only have to be representative.

Nothing is generated here. The frozen file is read, so a recording is still
reproducible, and `tests/test_frozen_narrations.py` is what holds the words
in it to the data rather than this script. The samples are WAV and live
outside the repo. These are MP3 and are committed, because the site serves
them: a WAV of a twenty second narration is an order of magnitude larger than
the MP3 of it.

**The character count is printed before anything is sent**, three ways, and
`--budget` is set on the one IBM charges for. IBM counts SSML toward the
character count and does not count whitespace, so a request costs its
submitted length less its spaces: `billed_characters` in `app/tts.py` is that
figure, with the submitted length above it and the spoken text below it.
Nothing is sent without `--confirm`, and a run over the budget is refused.

**A refusal keeps what it already wrote.** The free allowance is a monthly
character count, so a run can be refused part way through. Each file is
written as its response arrives, the error is printed with the status the
service sent, and `--map` then writes `hero.audio` from the files that are
actually on disk, so a partial run leaves a map that matches it.

Run it:

    .\.venv-prelude\Scripts\python.exe -I scripts\tts_hero.py --plan
    .\.venv-prelude\Scripts\python.exe -I scripts\tts_hero.py --confirm
    .\.venv-prelude\Scripts\python.exe -I scripts\tts_hero.py --map

Standard library only.
"""

import argparse
import json
import sys
import urllib.error
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
# `scripts/write_headers.py` builds the header and `scripts/tts_samples.py`
# builds the narration, and doing either a second time here would be a second
# place for that construction to be wrong. The scripts directory is not on the
# path under `-I`, so it is added explicitly rather than by accident.
sys.path.insert(0, str(Path(__file__).resolve().parent))

# The pronunciation table holds IPA and this script prints the text it built.
# A Windows console is cp1252 by default, which cannot encode "liːd".
#
# Both streams, and stderr is not an afterthought: the service's own refusal
# comes back as a JSON body that this prints to stderr, and a body holding one
# character cp1252 cannot encode would fail inside the error handler. The
# bodies seen so far are ASCII, so this is a guard rather than a fix.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from app.tts import (  # noqa: E402
    MP3_ACCEPT,
    SpeechRequest,
    WatsonTextToSpeech,
    billed_characters,
    without_markup,
)
from write_headers import openings  # noqa: E402

#: The site's copy, and where the recordings go beside it. The path written
#: into `hero.audio` is relative to `app/web/`, which is what the player
#: fetches against and what `tests/test_narration_player.py` resolves.
MATCHES = ROOT / "app" / "web" / "matches.json"

#: The frozen narrations, written by `scripts/freeze_narrations.py`. The same
#: file the moment card reads, so what a fan hears and what they see under
#: the grounding label are one text rather than two that have to agree.
NARRATIONS = ROOT / "app" / "web" / "narrations.json"
AUDIO_DIR = ROOT / "app" / "web" / "assets" / "audio"
AUDIO_HREF = "assets/audio"

#: The billed characters a run may cost before `--budget` refuses it.
#:
#: **Raised from 2,000 to 3,000 for Task 7.** The Task 6 narrations cost 1,959
#: and cleared 2,000 by 41 characters, which was close enough that one more
#: pronunciation entry on a word either of them says would have pushed the run
#: over. Task 7 asks for fuller narrations, which tell the whole move and name
#: every player who touched the ball, so they are longer: the candidates in
#: `scripts/hero_candidates.py` run 1,488 to 1,605 billed characters for one
#: match, where the frozen pair cost 918 and 1,041.
#:
#: It is a guard against a run that is unexpectedly large rather than a
#: forecast of the next one. The monthly Lite allowance is 10,000 characters,
#: so this is a fraction of it, and `--budget` takes a number for a run that
#: is meant to be bigger.
DEFAULT_BUDGET = 3500


@dataclass(frozen=True)
class Recording:
    """One file to write, and the request that would produce it."""

    match_id: int
    key: str
    persona_id: str
    situation: str
    listener: str
    header: str
    narration: str
    request: SpeechRequest

    @property
    def filename(self) -> str:
        return "{}_{}.mp3".format(self.match_id, self.key)

    @property
    def href(self) -> str:
        return "{}/{}".format(AUDIO_HREF, self.filename)

    @property
    def path(self) -> Path:
        return AUDIO_DIR / self.filename


def listener_label(match: dict, allegiance: str) -> str:
    """Which fan hears this recording, in the words the two sides are told
    apart by: the team's name rather than the key."""
    if allegiance == "team_a":
        return "supporting {}".format(match["home_team"])
    if allegiance == "team_b":
        return "supporting {}".format(match["away_team"])
    return "no side"


def frozen_narrations() -> dict[tuple[int, str], dict]:
    """The frozen narration per `hero.voice_for` key, by match and key.

    **One narration per listener, not one per goal.** Each slot of each hero
    goal has its own text under `slots`, written by the team and verified by
    the grounding check, and the moment card shows the one for the listener's
    own key. So the recording a fan hears and the words they read are the
    same piece of writing, and that is what this speaks.
    """
    if not NARRATIONS.is_file():
        raise SystemExit(
            "{} does not exist, so there are no narrations to speak. Run "
            "scripts/freeze_narrations.py --authored --confirm, which calls "
            "no model.".format(NARRATIONS.relative_to(ROOT))
        )
    doc = json.loads(NARRATIONS.read_text(encoding="utf-8"))
    found: dict[tuple[int, str], dict] = {}
    for match_id, entry in doc["narrations"].items():
        for key, slot in (entry.get("slots") or {}).items():
            found[(int(match_id), key)] = slot
    return found


def recordings(backend: WatsonTextToSpeech) -> tuple[Recording, ...]:
    """Every recording the site needs, with the request each one would send.

    The keys are read out of `hero.voice_for` rather than rebuilt here:
    `scripts/write_headers.py --check` is the gate that holds that field to
    what the orchestrator and the delivery table decide, and a second
    derivation here could disagree with the one the browser reads.
    """
    doc = json.loads(MATCHES.read_text(encoding="utf-8"))
    heroes = openings()
    narrations = frozen_narrations()
    built = []
    for match in doc["matches"]:
        match_id = match["match_id"]
        hero = match["hero"]
        header = heroes[match_id]["header"]
        seen = set()
        for allegiance, key in hero["voice_for"].items():
            if key in seen:
                # Two listeners can be sent to one recording, and then it is
                # one file and one call rather than the same audio twice.
                continue
            seen.add(key)
            slot = narrations.get((match_id, key))
            if slot is None:
                raise SystemExit(
                    "no frozen narration for match {} slot {}; a recording "
                    "of another listener's telling is not what this "
                    "ships".format(match_id, key)
                )
            if not slot.get("check", {}).get("grounded"):
                raise SystemExit(
                    "the frozen {} narration for match {} is not recorded as "
                    "grounded, so it is not a narration this app may "
                    "speak".format(key, match_id)
                )
            narration = slot["text"]
            persona_id, situation = key.rsplit("_", 1)
            built.append(
                Recording(
                    match_id=match_id,
                    key=key,
                    persona_id=persona_id,
                    situation=situation,
                    listener=listener_label(match, allegiance),
                    header=header,
                    narration=narration,
                    request=backend.request_for(
                        header, narration, persona_id, situation
                    ),
                )
            )
    return tuple(built)


def plan(all_recordings: Sequence[Recording]) -> tuple[int, int, int]:
    """Print every recording and what the run costs. Returns the three totals.

    The middle one is the price; the other two bound it.
    """
    print("{} recordings, {} calls".format(
        len(all_recordings), len(all_recordings)
    ))
    print()
    for one in all_recordings:
        print("  {}: {}, {}".format(one.filename, one.persona_id, one.listener))
    print()
    for index, one in enumerate(all_recordings, start=1):
        print("  call {}: {}".format(index, one.request.query))
        print("    {}".format(one.request.text))
        print("    {} submitted, {} billed, {} spoken".format(
            one.request.billable_characters,
            one.request.billed_characters,
            len(without_markup(one.request.text)),
        ))
    submitted = sum(one.request.billable_characters for one in all_recordings)
    billed = billed_characters([one.request for one in all_recordings])
    spoken = sum(
        len(without_markup(one.request.text)) for one in all_recordings
    )
    print()
    print("  {} characters submitted, markup and whitespace counted".format(
        submitted
    ))
    print("  {} characters billed, markup counted and whitespace not: this "
          "is the price".format(billed))
    print("  {} characters spoken, markup not counted".format(spoken))
    return submitted, billed, spoken


def run(backend: WatsonTextToSpeech,
        all_recordings: Sequence[Recording]) -> list[Recording]:
    """Send one request per recording and write each file as it arrives.

    Returns the recordings that were written. An HTTP error stops the run and
    is re-raised to the caller, which reports it: the allowance is monthly and
    a refusal part way through is the shape a limit arrives in.
    """
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    for one in all_recordings:
        audio = backend.send(one.request)
        one.path.write_bytes(audio)
        written.append(one)
        print("  {}: {} bytes".format(one.filename, len(audio)), flush=True)
    return written


def write_map() -> dict:
    """Write `hero.audio` from the files that are on disk, and report it.

    Driven by what exists rather than by what was asked for, so a run that was
    refused part way through leaves a map pointing only at real files, which
    is what `tests/test_narration_player.py::TestTheAudioMap` holds it to and
    what leaves the player's button disabled for a listener with no recording.
    """
    doc = json.loads(MATCHES.read_text(encoding="utf-8"))
    report = {}
    for match in doc["matches"]:
        hero = match["hero"]
        audio = {}
        for key in sorted(set(hero["voice_for"].values())):
            filename = "{}_{}.mp3".format(match["match_id"], key)
            if (AUDIO_DIR / filename).is_file():
                audio[key] = "{}/{}".format(AUDIO_HREF, filename)
        hero["audio"] = audio
        report[match["match_id"]] = audio
    MATCHES.write_text(
        json.dumps(doc, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return report


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--plan",
        action="store_true",
        help="print the recordings and the character count, and make no call",
    )
    parser.add_argument(
        "--confirm", action="store_true", help="send them; this is the paid path"
    )
    parser.add_argument(
        "--map",
        action="store_true",
        help="write hero.audio from the files on disk, and make no call",
    )
    parser.add_argument(
        "--budget",
        type=int,
        default=DEFAULT_BUDGET,
        help="refuse to send if the billed count is above this "
             "(default {})".format(DEFAULT_BUDGET),
    )
    args = parser.parse_args(argv)

    if args.map and not args.confirm:
        for match_id, audio in write_map().items():
            print("  {}: {}".format(match_id, json.dumps(audio)))
        return 0

    backend = WatsonTextToSpeech(accept=MP3_ACCEPT)
    all_recordings = recordings(backend)
    _submitted, billed, _spoken = plan(all_recordings)
    if args.plan or not args.confirm:
        print()
        print("nothing was sent. --confirm is what sends it.")
        return 0
    if billed > args.budget:
        print()
        print("{} billed characters is over the budget of {}; nothing was "
              "sent".format(billed, args.budget), file=sys.stderr)
        return 1

    print()
    print("sending {} calls, {} billed characters:".format(
        len(all_recordings), billed
    ))
    try:
        written = run(backend, all_recordings)
    except urllib.error.HTTPError as refused:
        body = refused.read().decode("utf-8", errors="replace")
        print()
        print("the service refused: HTTP {} {}".format(
            refused.code, refused.reason
        ), file=sys.stderr)
        print(body, file=sys.stderr)
        print("whatever was written before this is kept; --map writes the "
              "map from the files on disk", file=sys.stderr)
        return 1
    print()
    print("{} files in {}".format(len(written), AUDIO_DIR))
    print()
    for match_id, audio in write_map().items():
        print("  {}: {}".format(match_id, json.dumps(audio)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
