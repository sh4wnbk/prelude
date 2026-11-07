r"""A read-only HTTP view of what this repo already holds.

watsonx Orchestrate needs a stable public URL to call, and GitHub Pages serves
files rather than answers. This is the smallest thing that closes that gap: a
GET-only FastAPI service that reads `app/web/matches.json`,
`app/web/narrations.json`, `app/web/narrators.json` and, through Bob's
`app/statsbomb_event_feed.py`, the events in `data/raw/`. It computes nothing a
screen does not already show.

**It holds no state and writes nothing.** The free tier it is deployed on
spins the service down after fifteen minutes without traffic and hands back a
filesystem rebuilt from the build, so anything written at runtime is gone on
the next wake. Nothing here writes.

**It needs no credentials and makes no paid call.** It does not import
`app/tts.py` or any watsonx backend, and it reads no environment variable, so
there is no key for a deploy to carry and nothing to meter. The narration it
serves was frozen into `app/web/narrations.json` and the recordings were made
once; `tests/test_api.py` holds both halves of that.

**The commit reaches it as a file, not as an environment variable.** Render
publishes the deployed commit to the build, and `render.yaml` writes it to
`build/commit.txt`. `/health` reads that file when it is there. Reading
`RENDER_GIT_COMMIT` here would make this module an environment reader, which
is the one thing the deploy checklist does not want to have to audit.

The endpoints:

    GET /health
    GET /moments?match=<id>
    GET /buildup?match=<id>&listener=team_a|team_b|neutral&narrator=<id>

Run it locally:

    .\.venv-prelude\Scripts\python.exe -I -m uvicorn app.api:app
"""

import json
from pathlib import Path
from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.grounding import GROUNDING_LABEL
from app.statsbomb_event_feed import StatsBombEventFeed

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "app" / "web"

MATCHES_FILE = WEB / "matches.json"
NARRATIONS_FILE = WEB / "narrations.json"
NARRATORS_FILE = WEB / "narrators.json"

#: Written by `render.yaml`'s build command from the commit Render deployed.
#: Absent locally, and absent on any build that did not write it, in which
#: case `/health` answers without a commit rather than guessing one.
BUILD_COMMIT_FILE = ROOT / "build" / "commit.txt"

#: Where the recordings are served from. The site is the same deploy a fan
#: opens, so a caller that follows one of these URLs hears the file the moment
#: card plays. `hero.audio` holds paths relative to `app/web/`, which is what
#: the Pages workflow uploads, so joining the two gives the public URL.
PAGES_BASE = "https://sh4wnbk.github.io/prelude/"

#: The three answers to "Who are you with". The same three values
#: `app/web/match-content.js` stores, and the only ones the slot rule knows.
Listener = Literal["team_a", "team_b", "neutral"]

#: The form a match id arrives in: digits, and nothing else.
#:
#: `match` was an integer parameter until 2026-11-07. watsonx Orchestrate
#: serialises an integer tool argument as a float, so the first live test
#: called `/buildup` with `match=3.869685e+06`. The 422 that came back was
#: correct and no use to anybody: the service cannot accept that value, and
#: the agent had no way to learn what it should have sent. So the parameter
#: takes a string of digits, which Orchestrate passes through unchanged, and
#: the conversion to an integer happens inside the endpoint.
#:
#: The pattern refuses a float, a signed number and a word, and it reaches the
#: caller: the 422 body names the pattern and echoes what was sent, which is
#: the whole of what an agent needs to send the next call correctly. It also
#: reaches `orchestrate/prelude_tools.yaml`, whose `match` parameter carries
#: the same type and the same pattern;
#: `tests/test_orchestrate_spec.py::TestTheParameters` reads the type out of
#: `app.openapi()` and holds the two together.
MATCH_PATTERN = r"^[0-9]+$"

#: What the parameter's own description tells a caller. An agent choosing an
#: argument reads this before it reads a 422.
MATCH_DESCRIPTION = (
    "StatsBomb match id, written as digits only: 3869685, not 3.869685e+06, "
    "and not a team name or a year."
)

#: `match`, on both endpoints, spelled once.
MatchId = Annotated[
    str, Query(pattern=MATCH_PATTERN, description=MATCH_DESCRIPTION)
]


def _read(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _load_matches() -> dict[int, dict]:
    return {entry["match_id"]: entry for entry in _read(MATCHES_FILE)["matches"]}


def _load_narrator_names() -> dict[str, str]:
    return {n["id"]: n["name"] for n in _read(NARRATORS_FILE)["narrators"]}


# Repo content, read once. These files change when a commit changes them, and
# a commit is a new deploy, so re-reading them per request would buy nothing
# and would cost a judge the wait on a service that has just woken up.
MATCHES = _load_matches()
NARRATIONS = _read(NARRATIONS_FILE)["narrations"]
NARRATOR_NAMES = _load_narrator_names()

FEED = StatsBombEventFeed()


def slot_for(
    voice_for: dict[str, str],
    listener: str,
    narrator: str | None = None,
) -> str | None:
    """The slot a listener hears, which is `Prelude.slotFor` in Python.

    The rule is one rule and it lives in two languages, so the seven rows in
    `tests/slot_rows.json` are read by `tests/test_api.py` for this function
    and by `tests/test_narrator_picker.py` for the browser's copy. Changing
    one of the two without the other fails both files.

    With no narrator chosen the listener's own side decides, which is the
    default the app shipped with. A chosen narrator is heard when one of the
    two slots in reach is theirs: the side's own slot, or the neutral one.
    When neither is, the side's slot stands, so a fan who picks a narrator
    with no recording for their answer still hears the telling written for
    them.
    """
    if not voice_for:
        return None
    fallback = voice_for.get(listener) or voice_for.get("neutral")
    if not narrator:
        return fallback
    for key in (voice_for.get(listener), voice_for.get("neutral")):
        if key and key.startswith(narrator + "_"):
            return key
    return fallback


def display_minute(minute: int) -> int:
    """The minute as the app captions it.

    StatsBomb floors the clock, so its minute 54 falls in the 55th minute of
    play. `scripts/check_match_copy.py` holds every minute in `matches.json`
    to the same rule.
    """
    return minute + 1


def _match_or_404(match: int) -> dict:
    entry = MATCHES.get(match)
    if entry is None:
        raise HTTPException(
            status_code=404,
            detail=f"unknown match {match}. This service serves {sorted(MATCHES)}.",
        )
    return entry


def _is_hero(entry: dict, moment) -> bool:
    """Whether `moment` is the goal the moment card and the recordings tell.

    Matched on the clock, the scorer and the team, which is what
    `matches.json` records under `hero.event` and what a `Moment` carries.
    """
    hero = entry["hero"]["event"]
    return (
        moment.minute == hero["minute"]
        and moment.second == hero["second"]
        and moment.player == hero["player"]
        and moment.team == hero["team"]
    )


def build_commit() -> str | None:
    """The commit this build came from, or `None` when nothing wrote it."""
    try:
        return BUILD_COMMIT_FILE.read_text(encoding="utf-8").strip() or None
    except OSError:
        return None


app = FastAPI(
    title="Prelude",
    summary="Read-only access to the moments and the narration the app serves.",
    version="0.1.0",
)

# A browser calling this from the Pages site is a different origin, and so is
# Orchestrate. Nothing here is private and nothing here is writable, so GET is
# open to everyone and no other method is allowed through.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    """Alive, and which commit is answering."""
    body = {"status": "ok"}
    commit = build_commit()
    if commit:
        body["commit"] = commit
    return body


@app.get("/moments")
def moments(match: MatchId) -> dict:
    """Every goal of the match, from Bob's EventFeed, in the order they fell.

    `narrated` is true for the one goal the app tells, which is the goal the
    six frozen narrations and the six recordings were made for. The other
    goals are in the data and have no narration, and saying so is what the
    field is for.

    `match` arrives as digits and is an integer from here on; `MATCH_PATTERN`
    records why it is not an integer at the edge.
    """
    match_id = int(match)
    entry = _match_or_404(match_id)
    home, away = entry["home_team"], entry["away_team"]

    scored = {home: 0, away: 0}
    goals = []
    for moment in FEED.defining_moments(match_id):
        if moment.team in scored:
            scored[moment.team] += 1
        goals.append(
            {
                "scorer": moment.player,
                "team": moment.team,
                "display_minute": display_minute(moment.minute),
                "score_after": {"home": scored[home], "away": scored[away]},
                "narrated": _is_hero(entry, moment),
            }
        )

    return {
        "match_id": match_id,
        "home_team": home,
        "away_team": away,
        "goals": goals,
    }


@app.get("/buildup")
def buildup(
    match: MatchId,
    listener: Listener = Query(...),
    narrator: str | None = Query(None),
) -> dict:
    """The narration this listener hears for the match's narrated goal.

    The words, the authorship and the recording all come off one slot, so the
    text a caller shows and the file it plays are one piece of writing. That
    is the same bargain the moment card makes.

    `label` carries "Verified from play data" only when the frozen slot says
    the words earned it. All six do, because nothing else was frozen; it is
    read off the record rather than attached here, because `CLAUDE.md` allows
    the phrase over checked narration and over nothing else.

    `match` arrives as digits and is an integer from here on; `MATCH_PATTERN`
    records why it is not an integer at the edge.
    """
    match_id = int(match)
    entry = _match_or_404(match_id)
    hero = entry["hero"]

    slot = slot_for(hero["voice_for"], listener, narrator)
    frozen = NARRATIONS.get(str(match_id), {}).get("slots", {}).get(slot)
    if slot is None or frozen is None:
        raise HTTPException(
            status_code=404,
            detail=f"match {match_id} has no frozen narration for slot {slot!r}",
        )

    body = {
        "match_id": match_id,
        "listener": listener,
        "slot": slot,
        "narrator": NARRATOR_NAMES.get(frozen["narrator"], frozen["narrator"]),
        "text": frozen["text"],
        "authorship": frozen["authorship"],
        "audio_url": PAGES_BASE + hero["audio"][slot],
    }
    if frozen.get("labelled"):
        body["label"] = GROUNDING_LABEL
    return body
