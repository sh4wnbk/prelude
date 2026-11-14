"""The claim count on the moment card, beside the label it stands on.

"Verified from play data" is a yes. It says the claims in these words trace
back to the records and it does not say how many claims that was, so a reader
has no way to tell a sentence with one traceable name in it from a telling
that traced twenty-three separate assertions. The count is the second number,
and the app already had it: `app/grounding.py` returns `checked` on every
verdict, and `scripts/freeze_narrations.py` writes it into
`app/web/narrations.json` as `slots.<key>.check.claims_checked` beside the
words it was reached on.

**It is read from the file and never typed.** A number typed beside the label
would be a claim about the check that the check did not make, so the renderer
reads it out of the frozen record, and
`tests/test_frozen_narrations.py::TestTheSixTheTeamWroteAreFrozen` re-runs the
real check against `data/raw/` and holds every one of the six to the count
recorded for it. That test is what makes the number true; this one is about it
reaching the card and never arriving without the label.

**All three appear in one step or none of them does.** The words, the label and
the count come out of one record, and `showNarration` is the only thing that
reveals any of them. A slot with no text, or with no usable count, shows
nothing at all: the label with nothing behind it is the state this exists to
remove. `tests/browser/test_the_label_waits.py` asks that of every frame a
`MutationObserver` recorded, not only of the state the card settled in.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "app" / "web"
CARD = WEB / "prelude_03_moment_card.html"
RENDERER = WEB / "match-content.js"
NARRATIONS = WEB / "narrations.json"

#: The three `hero.voice_for` keys, one narration each per hero goal.
SLOTS = ("buddy_scored", "buddy_conceded", "storyteller_neutral")

#: The words the count is written into, as the renderer builds them.
TAIL = " checked against the play data"


def card() -> str:
    return CARD.read_text(encoding="utf-8")


def renderer() -> str:
    return RENDERER.read_text(encoding="utf-8")


def js_function(name: str) -> str:
    """One function out of the renderer, braces matched.

    A test that searched the whole file could not tell the reveal inside
    `showNarration` from a second reveal somewhere else, which is the thing
    worth knowing here.
    """
    source = renderer()
    start = source.index("function %s(" % name)
    depth = 0
    for i in range(source.index("{", start), len(source)):
        if source[i] == "{":
            depth += 1
        elif source[i] == "}":
            depth -= 1
            if depth == 0:
                return source[start:i + 1]
    raise AssertionError("%s is not brace balanced" % name)


def slots() -> dict:
    doc = json.loads(NARRATIONS.read_text(encoding="utf-8"))
    return {
        match_id: entry["slots"]
        for match_id, entry in doc["narrations"].items()
    }


class TestEverySlotRecordsACount:
    """The six the card can show, and the count each one carries.

    `tests/test_frozen_narrations.py` re-checks these numbers against
    `data/raw/`. What is asked here is that one exists for every slot the
    renderer can reach, so no listener gets the label with no count beside it.
    """

    def test_both_matches_carry_all_three_slots(self):
        for match_id, by_slot in slots().items():
            assert set(by_slot) == set(SLOTS), match_id

    def test_every_slot_records_a_count(self):
        for match_id, by_slot in slots().items():
            for key in SLOTS:
                count = by_slot[key]["check"]["claims_checked"]
                assert isinstance(count, int) and not isinstance(count, bool)
                assert count > 0, (match_id, key)

    def test_every_count_belongs_to_a_grounded_verdict(self):
        # A count off a refused narration would be a number of claims the
        # check could not all trace, standing under a label saying it could.
        for match_id, by_slot in slots().items():
            for key in SLOTS:
                assert by_slot[key]["check"]["grounded"] is True, (match_id, key)
                assert by_slot[key]["check"]["failures"] == [], (match_id, key)

    def test_the_count_agrees_with_the_verdict_summary(self):
        # `GroundingResult.summary` writes the same number out in prose, so a
        # record whose two halves disagree is one that was edited by hand.
        for match_id, by_slot in slots().items():
            for key in SLOTS:
                verdict = by_slot[key]["check"]
                assert verdict["summary"] == (
                    "grounded: %d claim(s) all traced to the data"
                    % verdict["claims_checked"]
                ), (match_id, key)


class TestTheCardShipsItHiddenAndEmpty:
    def test_the_card_carries_the_field(self):
        assert 'data-field="hero_claims"' in card()

    def test_it_ships_hidden(self):
        tag = re.search(r'<p[^>]*data-field="hero_claims"[^>]*>', card())
        assert tag, "no claim count element on the card"
        assert 'style="display:none"' in tag.group(0)

    def test_it_ships_empty(self):
        assert 'data-field="hero_claims" style="display:none"></p>' in card()

    def test_no_number_is_typed_into_the_markup(self):
        # The count is the check's own verdict. A number sitting in the markup
        # would be read by a fan before the file it came from had been
        # fetched, and would be the 1986 count on the 2022 card.
        assert TAIL not in card()
        for by_slot in slots().values():
            for key in SLOTS:
                count = by_slot[key]["check"]["claims_checked"]
                assert "%d claims" % count not in card(), key

    def test_it_sits_in_the_block_that_reserves_the_space(self):
        block = card().split('data-field="hero_narration_block"')[1]
        block = block[:block.index("<!-- Audio Narration Player")]
        for field in ("hero_narration", "hero_label", "hero_claims"):
            assert 'data-field="%s"' % field in block, field

    def test_it_sits_under_the_label(self):
        markup = card()
        assert markup.index('data-field="hero_label"') < markup.index(
            'data-field="hero_claims"'
        ), "the count is above the label it is about"


class TestTheWordsTheRendererBuilds:
    def test_the_line_is_built_in_one_place(self):
        assert renderer().count("function claimsLine(") == 1
        assert renderer().count("claimsLine(") == 2, (
            "claimsLine is defined once and called once"
        )

    def test_the_plural_reading(self):
        body = js_function("claimsLine")
        assert '" claims"' in body
        assert TAIL in body

    def test_the_singular_reading(self):
        # No frozen slot is at one claim, and a count of one is still a count
        # a file could record, so the line reads as English rather than
        # relying on the number staying above one.
        body = js_function("claimsLine")
        assert 'claims === 1 ? " claim" : " claims"' in body

    def test_the_line_claims_nothing_the_check_did_not(self):
        # "checked against the play data" is what `GroundingResult.checked`
        # counts: claims pulled out of these words and traced to a record.
        # Anything stronger would be a verdict the count does not carry.
        body = js_function("claimsLine").lower()
        for word in ("proven", "confirmed", "accurate", "correct", "true"):
            assert word not in body, word

    def test_the_label_itself_is_not_written_here(self):
        # `GROUNDING_LABEL` is spelled in `app/grounding.py` and in the card's
        # markup and nowhere else, which `scripts/scan_copy.py` enforces for
        # the copy files. The count is a different sentence.
        assert "Verified from play data" not in renderer()


class TestTheGuardOnShowingIt:
    def test_the_count_is_read_from_the_fetched_slot(self):
        body = js_function("claimsChecked")
        assert "slot.check.claims_checked" in body

    def test_a_missing_or_unusable_count_is_refused(self):
        body = js_function("claimsChecked")
        assert 'typeof count === "number"' in body
        assert "isFinite(count)" in body
        assert "count > 0" in body
        assert "count === Math.round(count)" in body
        assert "null" in body

    def test_the_reveal_is_guarded_on_the_count_as_well_as_the_text(self):
        body = js_function("renderNarration")
        assert "var claims = claimsChecked(slot);" in body
        assert "if (slot && slot.text && claims !== null) {" in body

    def test_showNarration_takes_the_count_as_an_argument(self):
        # Not read from the document a second time: the words and the number
        # reach the card in one call, so there is no window in which one has
        # arrived and the other has not.
        assert "function showNarration(text, claims) {" in renderer()
        assert "showNarration(slot.text, claims);" in renderer()

    def test_the_reveal_fills_it_before_showing_it(self):
        body = js_function("showNarration")
        fill = body.index("counted.textContent = claimsLine(claims);")
        show = body.index('counted.style.removeProperty("display")')
        assert fill < show, "the count is shown before the number is in it"

    def test_the_reveal_shows_all_three_and_releases_the_button(self):
        body = js_function("showNarration")
        assert body.count("removeProperty") == 3
        assert "announceNarration();" in body

    def test_nothing_else_in_the_renderer_reaches_the_field(self):
        source = renderer()
        outside = source.replace(js_function("showNarration"), "")
        assert "hero_claims" not in outside, (
            "the count is reached from somewhere other than showNarration"
        )

    def test_the_failing_fetch_arm_shows_nothing(self):
        body = js_function("renderNarration")
        catch = body[body.index(".catch("):]
        assert "showNarration" not in catch
        assert "removeProperty" not in catch


class TestTheBlockStillReservesTheTallest:
    """The count made the block taller, so the reservation was re-measured.

    The six measure 260, 286 and 312 px at 390 px wide with the words, the
    label and the count on screen. 19.5rem is the tallest, and
    `tests/browser/test_the_fan_hears_their_own.py` reads the rendered height
    in Chromium rather than trusting this number.
    """

    def test_the_block_reserves_the_tallest(self):
        block = re.search(
            r'<div[^>]*data-field="hero_narration_block"[^>]*>', card()
        )
        assert block, "the three are in no block of their own"
        assert "min-height:19.5rem" in block.group(0)

    def test_the_old_reservation_is_gone(self):
        assert "16.75rem" not in card()
