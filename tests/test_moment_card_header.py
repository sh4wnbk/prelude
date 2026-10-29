"""Acceptance tests for the header on the moment card, written before it exists.

The orchestrator's header says what the goal did to the score, and it is the
same line for every listener. The app is a static site, so nothing in the
browser can run `app/orchestrator.py`. Because the header does not depend on
the listener, it does not need to: `scripts/write_headers.py` computes it once
per match and writes it into `app/web/matches.json`, and the moment card reads
it from there. `docs/bob_brief.md` carries the brief as Task 6.

**Bob built Task 6 in `aab7093`.** The script is still looked up by path at
call time, so if it ever goes missing that is one named failure per test that
needs it, and the rest of the suite runs.

The expected headers are literals. They were produced by running the built
orchestrator over `data/raw/` on 2026-10-29, and their last sentence changed
from "Here's the buildup." to "Here's how it happened." for Task 7, when
`HEADER_TAIL` did. They are written out so that a
wrong script and a wrong orchestrator cannot agree with each other in silence.
The greeting is "tonight" for both matches because the kickoff in
`app/web/matches.json`, which `scripts/check_match_copy.py` checks against the
match index, is 19:00 for 1986 and 17:00 for 2022, both at or after
`EVENING_CUTOFF`.
"""

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "app" / "web"
MATCHES = WEB / "matches.json"
SCRIPT = ROOT / "scripts" / "write_headers.py"
MOMENT_CARD = WEB / "prelude_03_moment_card.html"
RENDERER = WEB / "match-content.js"

#: The hero goal of each match, and the opening its moment card shows.
EXPECTED = {
    3750191: {
        "greeting": "tonight",
        "header": "Argentina extend the lead. Argentina 2, England 0. "
                  "Here's how it happened.",
    },
    3869685: {
        "greeting": "tonight",
        "header": "Argentina extend the lead. Argentina 2, France 0. "
                  "Here's how it happened.",
    },
}

#: The heading the card carried before the orchestrator existed. It tells the
#: fan they were absent, which the opener rule in `docs/VOICE.md` keeps out.
OLD_HEADING = "You stepped away. Here’s the buildup you missed."


def script():
    """`scripts/write_headers.py` as a module, or fail saying it is not built."""
    if not SCRIPT.exists():
        pytest.fail(
            "scripts/write_headers.py does not exist yet. It is Task 6 in "
            "docs/bob_brief.md."
        )
    spec = importlib.util.spec_from_file_location("write_headers", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(*arguments):
    if not SCRIPT.exists():
        pytest.fail(
            "scripts/write_headers.py does not exist yet. It is Task 6 in "
            "docs/bob_brief.md."
        )
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        cwd=ROOT, capture_output=True, text=True,
    )


def heroes():
    doc = json.loads(MATCHES.read_text(encoding="utf-8"))
    return {entry["match_id"]: entry["hero"] for entry in doc["matches"]}


class TestTheOpeningInMatchesJson:
    def test_the_1986_hero_carries_its_opening(self):
        assert heroes()[3750191].get("opening") == EXPECTED[3750191]

    def test_the_2022_hero_carries_its_opening(self):
        assert heroes()[3869685].get("opening") == EXPECTED[3869685]


class TestTheScript:
    def test_it_computes_what_the_orchestrator_says(self):
        assert script().openings() == EXPECTED

    def test_check_passes_on_the_committed_file(self):
        result = run("--check")
        assert result.returncode == 0, result.stdout + result.stderr

    def test_check_fails_when_a_header_drifts(self, tmp_path):
        copy = tmp_path / "matches.json"
        shutil.copy(MATCHES, copy)
        doc = json.loads(copy.read_text(encoding="utf-8"))
        for entry in doc["matches"]:
            entry["hero"]["opening"] = {"greeting": "today", "header": "Wrong."}
        copy.write_text(json.dumps(doc), encoding="utf-8")
        result = run("--check", "--path", str(copy))
        assert result.returncode == 1, result.stdout + result.stderr

    def test_check_writes_nothing(self, tmp_path):
        copy = tmp_path / "matches.json"
        shutil.copy(MATCHES, copy)
        before = copy.read_bytes()
        run("--check", "--path", str(copy))
        assert copy.read_bytes() == before


class TestTheMomentCard:
    def test_the_heading_is_the_header_field(self):
        markup = MOMENT_CARD.read_text(encoding="utf-8")
        assert 'data-field="hero_header"' in markup

    def test_the_inline_heading_is_the_1986_header(self):
        """The inline copy is what shows before the renderer runs, and it is
        the default match's, as with every other field on the card."""
        markup = MOMENT_CARD.read_text(encoding="utf-8")
        assert EXPECTED[3750191]["header"] in markup

    def test_the_old_heading_is_gone(self):
        markup = MOMENT_CARD.read_text(encoding="utf-8")
        assert OLD_HEADING not in markup

    def test_the_renderer_fills_the_header(self):
        renderer = RENDERER.read_text(encoding="utf-8")
        assert '"hero_header"' in renderer
        assert "opening.header" in renderer
