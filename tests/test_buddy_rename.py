"""The partisan persona is "buddy" all the way through, written before Bob's Task 13.

Task 12 renamed what fans see to "The Buddy" and kept the id `mate`. Shawn's
call on 2026-10-30: rename the id too, before the hero recordings exist,
because their filenames are built from it (`3750191_mate_scored.mp3` would be
named after a word the app no longer uses). `docs/bob_brief.md` carries the
brief as Task 13.

The past is not renamed. `scripts/narration_eval.py` writes the report of runs
made while the persona was called the Mate, and those runs keep their name;
so do `docs/narration_eval.md`, `HANDOFF.md`'s history and `bob_sessions/`.
"""

import json
import re
from pathlib import Path

from app.personas import PERSONAS

ROOT = Path(__file__).resolve().parent.parent
MATE = re.compile(r"\bmate\b", re.IGNORECASE)

#: Live code and data, where the name has to be the current one.
LIVE = (
    sorted((ROOT / "app").glob("*.py"))
    + sorted((ROOT / "app" / "web").glob("*.js"))
    + sorted((ROOT / "app" / "web").glob("*.json"))
    + sorted((ROOT / "app" / "web").glob("*.html"))
    + [p for p in sorted((ROOT / "scripts").glob("*.py"))
       if p.name != "narration_eval.py"]
    + [p for p in sorted((ROOT / "tests").glob("test_*.py"))
       if p.name != "test_buddy_rename.py"]
)


def test_the_persona_ids():
    assert [p.id for p in PERSONAS] == ["caller", "storyteller", "buddy"]


def test_the_contract_constant():
    from app import orchestrator_contract
    assert orchestrator_contract.BUDDY == "buddy"
    assert not hasattr(orchestrator_contract, "MATE")


def test_the_recording_keys():
    doc = json.loads((ROOT / "app" / "web" / "matches.json").read_text(encoding="utf-8"))
    for entry in doc["matches"]:
        assert entry["hero"]["voice_for"]["team_a"] == "buddy_scored"
        assert entry["hero"]["voice_for"]["team_b"] == "buddy_conceded"


def test_no_live_file_says_mate():
    found = []
    for path in LIVE:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if MATE.search(line):
                found.append(f"{path.relative_to(ROOT)}:{number}: {line.strip()}")
    assert not found, "\n".join(found)
