"""Four lines the screens carried that claimed more than the code does.

A read-only review of the app, in `bob_sessions/phase6_review_app.md`, found
them; each was read against the repo before it was removed in Task 32.

| What it said | Why it was not true |
| ------------ | ------------------- |
| a badge reading "AT VENUE, GPS" on Live and on the ticket | `CLAUDE.md` names GPS presence as one of the three inputs and no code in this repo reads a position |
| a third button on the moment card offering to sync the audio live | the six recordings are committed files; there is no live audio |
| "Play data connected, AI narration ready" on the list and the ticket | nothing checks a connection, and the narration is frozen rather than becoming ready |
| the confirm button's two-step sequence | nothing was being synchronized and there is no venue feed |

`scripts/scan_copy.py` holds the five patterns, one per line of copy and two
for the button that said two things, so none of the words can come back. What
is here is the rest: the markup and the handlers that went with them, which a
string scan cannot see. The app still presents a match in progress, which is
the decision in `HANDOFF.md` under "The app is always live"; what these four
claimed was a sensor, a live feed and a connection, none of which the clock
and the LIVE tag say anything about.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "app" / "web"
SCREENS = sorted(WEB.glob("*.html"))
PICKER = WEB / "prelude_01_picker.html"
CARD = WEB / "prelude_03_moment_card.html"
TICKET = WEB / "prelude_06_ticket.html"

#: The line that replaced "Play data connected, AI narration ready". It names
#: the data and the medium and claims nothing about either one's state.
STATUS = "Play-by-play data · audio narration"


def read(path):
    return path.read_text(encoding="utf-8")


def matches():
    doc = json.loads(read(WEB / "matches.json"))
    return {entry["match_id"]: entry for entry in doc["matches"]}


class TestNoScreenClaimsAPosition:
    def test_no_screen_carries_the_badge(self):
        for path in SCREENS:
            assert "AT VENUE" not in read(path), path.name

    def test_no_screen_carries_the_icon_that_stood_beside_it(self):
        # `near_me` is the direction arrow. It was the badge's icon on both
        # screens and is on none of them now, so a row that kept the icon and
        # changed the words would fail here.
        for path in SCREENS:
            assert "near_me" not in read(path), path.name

    def test_the_ticket_names_the_venue_instead(self):
        # The row survived; what it asserts is the stadium, which is fixture
        # data, and not how the app came to know where the fan is.
        assert 'data-field="ticket_venue"' in read(TICKET)
        assert 'data-field="ticket_gps"' not in read(TICKET)

    def test_the_renderer_fills_the_renamed_field(self):
        assert 'setText("ticket_venue", match.live_seated.venue)' in read(TICKET)


class TestTheMomentCardOffersNoLiveSync:
    def test_the_button_is_gone(self):
        assert 'id="syncAction"' not in read(CARD)

    def test_its_handler_is_gone(self):
        assert "syncAction" not in read(CARD)

    def test_the_word_synced_is_gone_from_the_card(self):
        # The button's only effect was to write SYNCED over its own label.
        assert "SYNCED" not in read(CARD)

    def test_the_deck_is_two_buttons_wide(self):
        assert '<div class="grid grid-cols-2 gap-space-xs w-full">' in read(CARD)

    def test_the_deck_holds_two_buttons(self):
        deck = read(CARD).split('class="grid grid-cols-2')[1].split("<script")[0]
        assert deck.count("<button") == 2

    def test_the_two_that_are_left(self):
        assert 'id="replayAction"' in read(CARD)
        assert 'id="shareAction"' in read(CARD)


class TestConfirmingGoesStraightToTheMatch:
    def test_the_button_calls_the_renamed_handler(self):
        tag = re.search(r'<button [^>]*id="confirm-btn"[^>]*>', read(PICKER)).group(0)
        assert 'onclick="confirmEvent()"' in tag

    def test_nothing_on_the_screen_is_on_a_timer(self):
        # The sequence was two nested setTimeouts, 800 ms and then 700 ms.
        # Nothing else on this screen uses one, so the absence is the check.
        assert "setTimeout" not in read(PICKER)

    def test_the_handler_opens_live_for_the_chosen_match(self):
        body = read(PICKER).split("function confirmEvent()")[1].split("\n  }")[0]
        assert "Prelude.resetMoment(selectedMatch)" in body
        assert "Prelude.url('prelude_02_live_seated.html', selectedMatch)" in body

    def test_the_handler_refuses_with_no_card_picked(self):
        body = read(PICKER).split("function confirmEvent()")[1].split("\n  }")[0]
        assert "if (selectedMatch === null) return;" in body

    def test_nothing_rewrites_the_buttons_label(self):
        # The label was reset on every selection because the sequence used to
        # overwrite it. Nothing writes it now, so the markup's own words stand.
        assert "btn-text').innerText" not in read(PICKER)
        assert 'id="btn-text">CONFIRM EVENT<' in read(PICKER)


class TestTheStatusLineClaimsNoState:
    def test_both_matches_carry_the_new_line(self):
        for match_id, entry in matches().items():
            assert entry["picker"]["status"] == STATUS, match_id

    def test_the_list_carries_it_inline_for_both_cards(self):
        assert read(PICKER).count(STATUS) == 2

    def test_the_ticket_carries_it_inline(self):
        assert STATUS in read(TICKET)

    def test_no_screen_or_copy_file_says_the_old_line(self):
        copy_files = SCREENS + sorted(WEB.glob("*.json")) + sorted(WEB.glob("*.js"))
        for path in copy_files:
            text = read(path)
            assert "Play data connected" not in text, path.name
            assert "AI narration ready" not in text, path.name


class TestTheTwoPillsNameTheDataRatherThanItsState:
    """Shawn's decision of 2026-11-14, and the end of Task 32's second
    "Found, not fixed" line.

    Live's pill read "PLAY DATA CONNECTED" and the Moments cards read
    "AI AUDIO NARRATION, PLAY DATA SYNC". They were near neighbours of the
    four lines above and were left standing because Shawn had named four.
    Nothing checks a connection and nothing synchronises: the play data is a
    file in this repo and the recordings are six more. Both lines name the
    data now, in the words the list card already used for it.
    """

    #: What each pill says instead.
    LIVE_PILL = "PLAY-BY-PLAY DATA"
    MOMENTS_PILL = "AI AUDIO NARRATION · PLAY-BY-PLAY DATA"

    def test_the_live_pill(self):
        assert self.LIVE_PILL in read(WEB / "prelude_02_live_seated.html")

    def test_the_moments_pill_on_both_cards(self):
        assert read(WEB / "prelude_04_moments.html").count(self.MOMENTS_PILL) == 2

    def test_it_is_the_same_phrase_the_list_card_uses(self):
        """"Play-by-play data" is already the first half of the status line
        on the list and the ticket, so the app now says one thing about what
        it holds."""
        assert STATUS.lower().startswith(self.LIVE_PILL.lower())

    def test_no_screen_or_copy_file_says_either_old_line(self):
        copy_files = SCREENS + sorted(WEB.glob("*.json")) + sorted(WEB.glob("*.js"))
        for path in copy_files:
            text = read(path)
            assert "PLAY DATA CONNECTED" not in text, path.name
            assert "PLAY DATA SYNC" not in text, path.name

    def test_the_scan_holds_both_of_them(self):
        """A string scan is what stops the words coming back, and this is
        what stops the patterns being dropped from it."""
        scan = read(ROOT / "scripts" / "scan_copy.py")
        assert r'r"PLAY DATA CONNECTED"' in scan
        assert r'r"PLAY DATA SYNC"' in scan
