"""Acceptance tests for the Profile screen, written before it exists.

Once a fan has answered "Who are you with", nothing in the app let them change
it: the answer lasts the tab's session, and a refresh keeps it. Shawn found
that on 2026-10-29. The Profile screen shows the answer for the match and the
name, with a Change button that reopens the card, and the person icon in every
header now leads to it. `docs/bob_brief.md` carries the brief as Task 10.

Two behaviours are checked in a browser rather than here, because reading the
file cannot see them: reopened, the card presses the current choice and fills
the name; and after Continue, the Profile screen shows the new answer.

The persona cards are not part of this screen yet. A persona is a voice, and no
voice is chosen until Phase 5, so a picker today would offer a choice that
changes nothing.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "app" / "web"
PROFILE = WEB / "prelude_07_profile.html"
CARD = WEB / "listener-card.js"
RENDERER = WEB / "match-content.js"
LINK = 'href="prelude_07_profile.html?v=__V__"'

#: Every screen with a header, which is every screen but the root redirect.
HEADED = [
    "prelude_01_picker.html",
    "prelude_02_live_seated.html",
    "prelude_03_moment_card.html",
    "prelude_04_moments.html",
    "prelude_05_scan.html",
    "prelude_06_ticket.html",
]

#: The screens with the bottom nav.
NAVVED = HEADED[:4]


def profile():
    if not PROFILE.exists():
        pytest.fail(
            "app/web/prelude_07_profile.html does not exist yet. It is Task 10 "
            "in docs/bob_brief.md."
        )
    return PROFILE.read_text(encoding="utf-8")


def profile_tab(markup):
    """The bottom nav's Profile item, as its opening tag."""
    tag = re.search(r'<a [^>]*data-path="profile"[^>]*>', markup)
    assert tag, "no Profile item in the nav"
    return tag.group(0)


class TestTheProfileScreen:
    def test_it_loads_the_renderer(self):
        assert '<script src="match-content.js?v=__V__"></script>' in profile()

    def test_it_does_not_load_the_card(self):
        assert "listener-card.js" not in profile()

    def test_its_label(self):
        assert ">PROFILE</span>" in profile()

    def test_the_name_row(self):
        text = profile()
        assert ">Name</span>" in text
        assert 'data-field="profile_name">Not set<' in text

    def test_the_side_row(self):
        text = profile()
        assert ">With</span>" in text
        assert 'data-field="profile_with">Not set<' in text

    def test_the_change_button(self):
        assert re.search(r'<button [^>]*id="profileChange"[^>]*>Change</button>', profile())

    def test_change_reopens_the_card_on_live(self):
        text = profile()
        assert "Prelude.url('prelude_02_live_seated.html') + '&ask=1'" in text

    def test_its_own_tab_is_current(self):
        tab = profile_tab(profile())
        assert 'aria-current="page"' in tab
        assert LINK in tab

    def test_no_verified_label(self):
        assert "Verified from play data" not in profile()


class TestTheNavLeadsToIt:
    @pytest.mark.parametrize("name", NAVVED)
    def test_the_profile_tab_is_a_link(self, name):
        tab = profile_tab((WEB / name).read_text(encoding="utf-8"))
        assert LINK in tab
        assert "aria-disabled" not in tab
        assert 'tabindex="-1"' not in tab
        assert "pointer-events-none" not in tab
        assert "opacity-40" not in tab


class TestThePersonIconLeadsToIt:
    @pytest.mark.parametrize("name", HEADED)
    def test_the_icon_is_a_link(self, name):
        markup = (WEB / name).read_text(encoding="utf-8")
        assert '<div class="w-8 h-8 rounded-full bg-primary' not in markup
        assert re.search(r'<a aria-label="Profile" class="w-8 h-8 rounded-full bg-primary[^"]*" '
                         + re.escape(LINK) + ">", markup)


class TestTheRenderer:
    def test_it_fills_the_profile(self):
        text = RENDERER.read_text(encoding="utf-8")
        assert "function renderProfile" in text
        assert '"profile_name"' in text
        assert '"profile_with"' in text

    def test_it_names_the_neutral_answer(self):
        assert '"Just here for the game"' in RENDERER.read_text(encoding="utf-8")

    def test_it_says_not_set(self):
        assert '"Not set"' in RENDERER.read_text(encoding="utf-8")


class TestTheCardReopens:
    def test_it_opens_when_asked(self):
        text = CARD.read_text(encoding="utf-8")
        assert '"ask"' in text

    def test_it_clears_the_ask_after_continue(self):
        assert "replaceState" in CARD.read_text(encoding="utf-8")
