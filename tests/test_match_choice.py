"""Acceptance tests for the fan's choice of match, Task 26.

Shawn found this on 2026-11-10: after a hard refresh the event list showed
Argentina vs England already selected, with the amber ring and the check, and
the header pill read "ARG vs ENG . LIVE" before anything had been chosen.
Neither was a bug in one screen. `DEFAULT_MATCH` in `app/web/match-content.js`
stood in for a fan's choice wherever a screen needed a match and the URL named
none, and the list's markup carried the selected style on card 1.

The rule these hold is one sentence: a match is the fan's to choose, so it
travels in the query string and nothing invents one. A screen that is about a
match and has none sends the fan to the list; the list and the scanner render
no match at all.

Four behaviours are checked in a browser rather than here, because reading the
files cannot see them, and the run is recorded in HANDOFF.md under Task 26: a
hard refresh with session storage cleared leaves both cards unselected and the
pill hidden; each screen that needs a match lands on the list; a deep link
with `?match=` opens that match; and a ticket code opens the match it names.
"""

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "app" / "web"
PICKER = WEB / "prelude_01_picker.html"
RENDERER = WEB / "match-content.js"
SCANNER = WEB / "prelude_05_scan.html"
TICKET = WEB / "prelude_06_ticket.html"
INDEX = WEB / "index.html"

#: The match the inline fallback copy on the other screens describes. It is
#: only ever a fallback for a failed fetch of matches.json, so the renderer
#: must not name it: `scripts/check_match_copy.py` is what holds that copy to
#: matches.json.
INLINE_COPY_MATCH = 3750191

#: The screens that are about one match, and so cannot be shown without one.
NEEDS_A_MATCH = [
    "prelude_02_live_seated.html",
    "prelude_03_moment_card.html",
    "prelude_04_moments.html",
    "prelude_06_ticket.html",
    "prelude_07_profile.html",
]

#: The two that are reached before a match is chosen.
NEEDS_NO_MATCH = ["prelude_01_picker.html", "prelude_05_scan.html"]

#: What the selected card carries and the unselected one does not.
SELECTED_MARKS = [
    "ring-1 ring-primary-container/40",
    "bg-primary-container rounded-r",
    "bg-primary-container text-on-primary-container shadow-sm",
]

#: The radio mark on an unselected card.
UNSELECTED_MARK = '<span class="w-2 h-2 rounded-full bg-secondary-container"></span>'

#: The radio mark on the selected one.
CHECK_GLYPH = '<span class="material-symbols-outlined text-[16px] font-bold">check</span>'


def picker():
    return PICKER.read_text(encoding="utf-8")


def renderer():
    return RENDERER.read_text(encoding="utf-8")


def card_tags(markup):
    """The two event cards, as their opening tags."""
    tags = re.findall(r'<div class="event-card [^>]*>', markup)
    assert len(tags) == 2, f"expected two event cards, found {len(tags)}"
    return tags


def card_blocks(markup):
    """Each event card's markup, from its opening tag to the next card."""
    starts = [m.start() for m in re.finditer(r'<div class="event-card ', markup)]
    assert len(starts) == 2
    ends = starts[1:] + [markup.index("<!-- CARD 3", starts[-1])]
    return [markup[a:b] for a, b in zip(starts, ends)]


class TestNoCardIsSelectedOnLoad:
    """The list ships with neither card selected, in one style."""

    def test_neither_card_carries_a_selected_mark(self):
        for tag, block in zip(card_tags(picker()), card_blocks(picker())):
            for mark in SELECTED_MARKS:
                assert mark not in block, f"{mark!r} is in the markup of {tag!r}"

    def test_the_two_cards_carry_the_same_class_string(self):
        classes = [re.search(r'class="([^"]*)"', tag).group(1)
                   for tag in card_tags(picker())]
        assert classes[0] == classes[1]

    def test_both_cards_say_they_are_not_checked(self):
        for tag in card_tags(picker()):
            assert 'aria-checked="false"' in tag
            assert 'role="radio"' in tag

    def test_both_radios_carry_the_unselected_mark(self):
        marks = re.findall(
            r'<div class="radio-indicator [^>]*>(.*?)</div>', picker())
        assert len(marks) == 2
        assert marks[0] == marks[1] == UNSELECTED_MARK

    def test_no_check_glyph_sits_in_the_markup(self):
        """The check is written once, in the script, and put on by a tap."""
        assert picker().count(CHECK_GLYPH) == 1
        assert CHECK_GLYPH not in picker().split("<script>")[0]

    def test_confirm_event_ships_disabled(self):
        tag = re.search(r'<button [^>]*id="confirm-btn"[^>]*>', picker()).group(0)
        assert " disabled " in tag
        assert "disabled:opacity-40" in tag


class TestOnlyTheFanSelectsACard:
    def test_the_selection_starts_from_the_url_and_nowhere_else(self):
        assert "let selectedMatch = Prelude.chosenMatch;" in picker()

    def test_the_selected_style_is_written_once(self):
        """Both style sets are named, so a tap is the only way into one."""
        text = picker()
        assert "const SELECTED = {" in text
        assert "const UNSELECTED = {" in text
        for mark in SELECTED_MARKS:
            assert text.count(mark) == 1, mark

    def test_a_match_the_list_does_not_carry_is_not_a_choice(self):
        assert "if (!card) selectedMatch = null;" in picker()

    def test_confirming_nothing_does_nothing(self):
        assert "if (selectedMatch === null) return;" in picker()

    def test_confirm_follows_the_selection(self):
        assert "confirmBtn.disabled = selectedMatch === null;" in picker()


class TestTheChipNamesNoMatchBeforeAChoice:
    def test_the_lists_pill_ships_hidden(self):
        pill = re.search(r'<div class="inline-flex[^>]*data-field="chip_pill"[^>]*>',
                         picker())
        assert pill, "no chip pill on the list"
        assert 'style="display:none"' in pill.group(0)

    def test_the_lists_caption_is_empty(self):
        assert 'data-field="chip"></span>' in picker()

    def test_the_list_names_no_match_in_its_header(self):
        doc = json.loads((WEB / "matches.json").read_text(encoding="utf-8"))
        for entry in doc["matches"]:
            assert f'{entry["label"]} · LIVE' not in picker()

    def test_the_renderer_shows_the_pill_once_a_match_is_chosen(self):
        text = renderer()
        assert "function renderChip" in text
        assert 'var pill = field("chip_pill");' in text
        assert 'pill.style.removeProperty("display")' in text

    @pytest.mark.parametrize("name", [
        "prelude_02_live_seated.html", "prelude_03_moment_card.html",
        "prelude_04_moments.html", "prelude_07_profile.html"])
    def test_the_match_screens_keep_their_inline_caption(self, name):
        """Those screens are about one match by the time they can be reached,
        so their pill is the inline fallback the rest of their copy is."""
        markup = (WEB / name).read_text(encoding="utf-8")
        assert 'data-field="chip">ARG vs ENG · LIVE</span>' in markup
        assert 'data-field="chip_pill"' not in markup


class TestAScreenWithNoMatchGoesToTheList:
    def required(self):
        block = re.search(r"var MATCH_REQUIRED = \{(.*?)\};", renderer(), re.S)
        assert block, "no MATCH_REQUIRED in the renderer"
        return block.group(1)

    @pytest.mark.parametrize("name", NEEDS_A_MATCH)
    def test_the_screen_is_listed_as_needing_one(self, name):
        assert f'"{name}": true' in self.required()

    @pytest.mark.parametrize("name", NEEDS_NO_MATCH)
    def test_the_screens_reached_first_are_not_listed(self, name):
        assert name not in self.required()

    def test_it_is_read_before_the_markup_is_parsed(self):
        text = renderer()
        assert "var SENT_TO_PICKER = !CHOSEN_MATCH && needsMatch();" in text
        assert "if (SENT_TO_PICKER) goToPicker();" in text
        assert "if (SENT_TO_PICKER) return;" in text

    def test_the_list_replaces_the_screen_rather_than_stacking_on_it(self):
        block = re.search(r"function goToPicker\(\) \{(.*?)\n  \}", renderer(), re.S)
        assert block, "no goToPicker in the renderer"
        assert "window.location.replace(" in block.group(1)
        assert "prelude_01_picker.html" in block.group(1)

    def test_a_match_this_app_does_not_hold_goes_to_the_list_too(self):
        assert "if (needsMatch()) goToPicker();" in renderer()

    @pytest.mark.parametrize("name", NEEDS_A_MATCH + NEEDS_NO_MATCH)
    def test_every_screen_loads_the_renderer_that_does_this(self, name):
        markup = (WEB / name).read_text(encoding="utf-8")
        assert '<script src="match-content.js?v=__V__"></script>' in markup


class TestNothingStandsInForAChoice:
    def test_the_renderer_names_no_match_in_its_code(self):
        """The leading block comment says which match the inline copy is, and
        that is a note about the markup, not a value this file acts on."""
        code = renderer().split("*/", 1)[1]
        assert str(INLINE_COPY_MATCH) not in code

    def test_the_default_constant_is_gone(self):
        text = renderer()
        assert "DEFAULT_MATCH" not in text
        assert "defaultMatch" not in text

    def test_the_chosen_match_is_null_until_there_is_one(self):
        assert 'var CHOSEN_MATCH = Number(queryValue("match")) || null;' in renderer()

    def test_a_link_carries_the_match_only_when_there_is_one(self):
        block = re.search(r"function url\(path, matchId\) \{(.*?)\n  \}",
                          renderer(), re.S)
        assert block, "no url() in the renderer"
        body = block.group(1)
        assert "var id = matchId || CHOSEN_MATCH;" in body
        assert 'if (id) parts.push("match=" + id);' in body

    def test_what_the_screens_read_is_the_choice(self):
        assert "matchId: CHOSEN_MATCH, chosenMatch: CHOSEN_MATCH" in renderer()

    @pytest.mark.parametrize("name", ["seenKey", "ticketKey"])
    def test_the_session_keys_fall_back_to_the_choice(self, name):
        pattern = r"function " + name + r"\(matchId\) \{(.*?)\n  \}"
        block = re.search(pattern, renderer(), re.S)
        assert block, f"no {name}() in the renderer"
        assert "matchId || CHOSEN_MATCH" in block.group(1)


class TestDeepLinksStillWork:
    def test_the_renderer_reads_the_match_from_the_query_string(self):
        assert 'queryValue("match")' in renderer()

    def test_a_link_given_a_match_carries_that_one(self):
        """Prelude.url(path, id) is how a screen sends the fan to a match
        that is not the one it is on, which is the whole ticket flow."""
        assert "var id = matchId || CHOSEN_MATCH;" in renderer()


class TestTheTicketFlowStillWorks:
    def test_a_ticket_link_opens_the_ticket_screen_on_its_match(self):
        text = INDEX.read_text(encoding="utf-8")
        assert "prelude_06_ticket.html?v=__V__&match=' + parts[1]" in text

    def test_the_scanner_passes_the_match_it_read(self):
        text = SCANNER.read_text(encoding="utf-8")
        assert 'Prelude.url("prelude_06_ticket.html", ticket.match_id)' in text
        assert '"prelude_06_ticket.html?match=" + ticket.match_id' in text

    def test_entering_the_match_carries_it(self):
        text = TICKET.read_text(encoding="utf-8")
        assert 'Prelude.url("prelude_02_live_seated.html", matchId)' in text

    def test_edit_details_returns_to_the_list_on_that_match(self):
        text = TICKET.read_text(encoding="utf-8")
        assert ('Prelude.url("prelude_01_picker.html", matchId) + "&manual=1"'
                in text)

    def test_the_list_selects_the_match_a_returning_fan_is_on(self):
        text = picker()
        assert "'.event-card[data-match=\"' + selectedMatch + '\"]'" in text
        assert "if (card) selectEvent(card.id);" in text

    def test_manual_entry_hands_over_the_match_it_was_given(self):
        text = (WEB / "manual-entry.js").read_text(encoding="utf-8")
        assert 'Prelude.url("prelude_06_ticket.html", match.match_id)' in text
