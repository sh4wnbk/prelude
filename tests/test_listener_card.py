"""Acceptance tests for the "Who are you with" card, written before it exists.

After a fan enters a match, the Live screen asks who they are with and,
optionally, what to call them. The answer stays on the phone. It decides the
persona later on; today it only adds the name to the end of the moment card's
header, "...Here's how it happened, Olivia.", which is where Shawn put it on
2026-10-29. `docs/bob_brief.md` carries the brief as Task 9.

These read the files rather than drive a browser, so they pin the copy, the
storage keys, where the script is loaded and what it must never do. The card's
behaviour is checked in a real browser after it is built.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "app" / "web"
CARD = WEB / "listener-card.js"
RENDERER = WEB / "match-content.js"
LIVE = WEB / "prelude_02_live_seated.html"


def card():
    if not CARD.exists():
        pytest.fail(
            "app/web/listener-card.js does not exist yet. It is Task 9 in "
            "docs/bob_brief.md."
        )
    return CARD.read_text(encoding="utf-8")


def renderer():
    return RENDERER.read_text(encoding="utf-8")


class TestTheCardCopy:
    def test_the_question_uses_the_greeting_word(self):
        """"Who are you with tonight?", with the word read from
        `hero.opening.greeting` rather than written in."""
        text = card()
        assert "Who are you with " in text
        assert "opening.greeting" in text

    def test_the_neutral_choice(self):
        assert "Just here for the game" in card()

    def test_the_name_field_label(self):
        assert "What should we call you?" in card()

    def test_the_name_field_is_marked_optional(self):
        assert 'placeholder="Optional"' in card()

    def test_the_button(self):
        assert ">Continue<" in card()

    def test_the_teams_come_from_the_match(self):
        text = card()
        assert "home_team" in text
        assert "away_team" in text


class TestWhereItIsLoaded:
    def test_the_live_screen_loads_it(self):
        assert '<script src="listener-card.js?v=__V__"></script>' in LIVE.read_text(
            encoding="utf-8"
        )

    def test_no_other_screen_loads_it(self):
        for page in sorted(WEB.glob("*.html")):
            if page == LIVE:
                continue
            assert "listener-card.js" not in page.read_text(encoding="utf-8"), page.name


class TestTheAnswerStaysOnThePhone:
    def test_the_allegiance_is_stored_per_match(self):
        assert '"prelude.listener."' in renderer()

    def test_the_name_is_stored_once(self):
        assert '"prelude.name"' in renderer()

    def test_the_allegiance_values_are_the_contracts(self):
        """`team_a`, `team_b` and `neutral` are the values in
        `app/orchestrator_contract.py`, so a stored answer can be handed to the
        orchestrator's rules unchanged."""
        text = card()
        for value in ('"team_a"', '"team_b"', '"neutral"'):
            assert value in text

    def test_the_card_sends_nothing_anywhere(self):
        text = card()
        for call in ("fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket"):
            assert call not in text

    def test_the_name_never_goes_into_markup_as_html(self):
        """The name is typed by the fan, so it is set as text, never parsed."""
        for text in (card(), renderer()):
            for line in text.splitlines():
                if "innerHTML" in line:
                    assert not re.search(r"name", line, re.IGNORECASE), line


class TestTheNameInTheHeader:
    def test_the_renderer_exposes_the_join(self):
        assert "headerWithName" in renderer()

    def test_the_join_is_used_for_the_header(self):
        assert re.search(r'setText\("hero_header",\s*headerWithName\(', renderer())


    def test_the_name_is_never_a_replacement_string(self):
        """`replace()` reads "$&" in its replacement as the matched text, so a
        fan called "Jo $& Smith" came out "Jo . Smith" when the name went in
        as the replacement. Bob's Task 9 did that, and a browser run caught
        it; the name is joined as a plain string now."""
        body = renderer().split("function headerWithName", 1)[1].split("\n  }", 1)[0]
        for call in re.findall(r"\.replace\((.*?)\)\s*[+;]", body):
            assert "name" not in call, call


class TestTheBadge:
    def test_the_state_badge_does_not_wrap(self):
        live = LIVE.read_text(encoding="utf-8")
        badge = re.search(r'<span class="([^"]*)" data-field="state_badge">', live)
        assert badge and "whitespace-nowrap" in badge.group(1).split()
