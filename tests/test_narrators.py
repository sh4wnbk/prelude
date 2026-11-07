"""Acceptance tests for "Your narrator" on Profile, written before it existed.

The three personas become visible to the fan as narrators. Shawn's decisions on
2026-10-30: the heading is "Your narrator", the partisan persona is "The Buddy"
with id `buddy`, and choosing a narrator is not live yet. Profile shows the
three, marks the one the fan's answer picked, and tapping another shows that it
is coming soon. `docs/bob_brief.md` carries the brief as Task 12.

**Choosing a narrator is live now.** Task 14 in the same brief gave a fan the
choice, with the side rule as the default until they make one, so the note is
about the one narrator that is still coming soon rather than about every
narrator the fan did not get. What that task settles is in
`tests/test_narrator_picker.py`. What stays here is what Task 12 settled and
the picker does not move: the name, the list written from the personas, the
heading, a card being marked, and Change as an outline.

The list the browser shows is written from `app/personas.py` by a script, as
the header and `voice_for` are written by `scripts/write_headers.py`, so the
names and descriptions have one home.
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from app.personas import PERSONAS, persona

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "app" / "web"
NARRATORS = WEB / "narrators.json"
SCRIPT = ROOT / "scripts" / "write_narrators.py"
PROFILE = WEB / "prelude_07_profile.html"
RENDERER = WEB / "match-content.js"

EXPECTED = [
    {"id": "caller", "name": "The Caller",
     "profile": "Quick play-by-play, keeping up with the move."},
    {"id": "storyteller", "name": "The Storyteller",
     "profile": "Calm documentary, unhurried and even."},
    {"id": "buddy", "name": "The Buddy",
     "profile": "Warm, from the next seat."},
]

#: The note under the one narrator that has no recordings. Until Task 14 this
#: was a tail appended to any narrator the fan tapped and could not have,
#: ending "For now, Prelude picks your narrator from who you're with.". A fan
#: picks their own now, so the sentence that said otherwise is gone.
CALLER_NOTE = "The Caller is coming soon."


def narrators():
    if not NARRATORS.exists():
        pytest.fail(
            "app/web/narrators.json does not exist yet. It is Task 12 in "
            "docs/bob_brief.md."
        )
    return json.loads(NARRATORS.read_text(encoding="utf-8"))


def run(*arguments):
    if not SCRIPT.exists():
        pytest.fail(
            "scripts/write_narrators.py does not exist yet. It is Task 12 in "
            "docs/bob_brief.md."
        )
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        cwd=ROOT, capture_output=True, text=True,
    )


class TestTheName:
    def test_the_partisan_narrator_is_the_buddy(self):
        assert persona("buddy").name == "The Buddy"

    def test_the_id_is_buddy(self):
        assert [p.id for p in PERSONAS] == ["caller", "storyteller", "buddy"]


class TestTheList:
    def test_it_is_what_the_personas_say(self):
        assert narrators() == {"narrators": EXPECTED}

    def test_check_passes_on_the_committed_file(self):
        result = run("--check")
        assert result.returncode == 0, result.stdout + result.stderr

    def test_check_fails_when_it_drifts(self, tmp_path):
        copy = tmp_path / "narrators.json"
        shutil.copy(narrators() and NARRATORS, copy)
        copy.write_text(json.dumps({"narrators": EXPECTED[:2]}), encoding="utf-8")
        result = run("--check", "--path", str(copy))
        assert result.returncode == 1, result.stdout + result.stderr


class TestTheProfileScreen:
    def test_the_heading(self):
        assert ">Your narrator</span>" in PROFILE.read_text(encoding="utf-8")

    def test_the_list_container(self):
        assert 'data-field="narrator_list"' in PROFILE.read_text(encoding="utf-8")

    def test_the_message_container(self):
        assert re.search(r'data-field="narrator_note"[^>]*hidden', PROFILE.read_text(
            encoding="utf-8"))


class TestTheRenderer:
    def test_it_reads_the_list(self):
        assert "narrators.json" in RENDERER.read_text(encoding="utf-8")

    def test_it_marks_the_current_narrator(self):
        """Which narrator is current is `Prelude.slotFor`'s answer since
        Task 14, and `tests/test_narrator_picker.py` holds that lookup.
        What is checked here is that a card is still marked at all."""
        text = RENDERER.read_text(encoding="utf-8")
        assert 'aria-current="true"' in text or "'aria-current', 'true'" in text \
            or '"aria-current", "true"' in text

    def test_the_coming_soon_note(self):
        assert CALLER_NOTE in RENDERER.read_text(encoding="utf-8")

    def test_no_markup_from_data(self):
        """Names and descriptions are set as text."""
        body = RENDERER.read_text(encoding="utf-8").split("function renderNarrators", 1)
        assert len(body) == 2, "no renderNarrators function"
        section = body[1].split("\n  function ", 1)[0]
        assert "innerHTML" not in section


class TestTheChangeButton:
    """With the current narrator shown as an amber card, a filled amber Change
    competes with it, so Change becomes an outline: Shawn's call on
    2026-10-30, option B from the comparison on Profile."""

    def button(self):
        found = re.search(r'<button class="([^"]*)" id="profileChange"',
                          PROFILE.read_text(encoding="utf-8"))
        assert found, "no Change button"
        return found.group(1).split()

    def test_it_is_an_outline(self):
        classes = self.button()
        for name in ("bg-transparent", "border", "border-primary-container",
                     "text-primary-container"):
            assert name in classes, name

    def test_it_is_no_longer_filled(self):
        classes = self.button()
        for name in ("bg-primary-container", "text-on-primary", "shadow-lg"):
            assert name not in classes, name
