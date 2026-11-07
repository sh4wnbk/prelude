"""The frozen hero narrations still pass the grounding check against data/raw/.

`app/web/narrations.json` holds two kinds of frozen narration and this file
re-checks both. Under `slots` are the six the team wrote, one per
`hero.voice_for` key: the moment card shows the one for the listener's own
key under "Verified from play data" and `scripts/tts_hero.py` sends it to be
spoken, so those are the words a fan reads and hears. Beside them is the
per-goal narration `openai/gpt-oss-120b` wrote once, which stays as the
pipeline's own evidence.

**The six carry their authorship and it is checked here.** They were written
by the team and verified by the check, which is a different claim from model
output, so a frozen narration that lost either half of that could be taken
for something it is not. A test fails when one does.

That label is the reason this file exists. A frozen narration is checked once,
at the moment it is written, and then never again by the thing that froze it,
so anything that moves underneath it moves silently: the facts the check reads
are rebuilt from `data/raw/` on every run, and the rules it reads them by live
in `app/grounding.py`. A refetch that lands different events, a change to how a
buildup is cut, a new rule in the check, or a hand edit to the text would each
leave the app claiming the data proves something it no longer proves.

So the check is run again here, on the committed text, against the events on
disk. It is not a re-run of the model and costs nothing: the narration is read
from the file and only the verdict is recomputed.

**The tagged text is what is checked, and the shown text is held to it.** A
sentence with its citation stripped has nothing to be read against, so
`tagged_text` is the form the check passed and the form it passes here;
`text` is asserted to be exactly that with the tags taken off, which is what
stops the two drifting apart.
"""

import json
from pathlib import Path

import pytest

from app.grounding import check, strip_citations
from app.narration import GROUNDING_LABEL, MODEL

import scripts.authored_narrations as authored
from scripts.narrator_candidates import (
    narrator_for,
    opener_missing,
    places_missing,
    zones_said,
)

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
WEB = ROOT / "app" / "web"
NARRATIONS = WEB / "narrations.json"
CARD = WEB / "prelude_03_moment_card.html"
RENDERER = WEB / "match-content.js"
SCAN = ROOT / "scripts" / "scan_copy.py"

#: The match whose copy sits inline in the markup, shown before the renderer
#: runs. The same default `app/web/match-content.js` uses.
DEFAULT_MATCH = 3750191

#: The slot a listener with no side hears, which is the one the markup
#: carries and the one the renderer falls back to.
NEUTRAL_SLOT = "storyteller_neutral"

#: The two hero goals, by the match they are in and the clock they are at.
#: Literals, so a narrations.json that quietly pointed at a different moment
#: would be caught rather than checked against whatever it named.
HEROES = {
    "3750191": (54, 18),
    "3869685": (35, 22),
}


def frozen() -> dict:
    """The committed narrations, or a failure naming what is missing."""
    if not NARRATIONS.is_file():
        pytest.fail(
            f"{NARRATIONS.relative_to(ROOT)} does not exist. It is written by "
            "scripts/freeze_narrations.py --confirm, which is a paid watsonx "
            "run."
        )
    document = json.loads(NARRATIONS.read_text(encoding="utf-8"))
    return document["narrations"]


def make_feed():
    """The real feed over `data/raw/`.

    `data/raw/` is gitignored and rebuilt by `scripts/fetch_statsbomb.py`. A
    missing one fails rather than skips: this test is the only thing holding
    the frozen text to the data, and a skip would let it go green on a
    machine where it checked nothing.
    """
    if not RAW.is_dir():
        pytest.fail(
            "data/raw/ is absent, so the frozen narrations cannot be checked "
            "against the events. Run scripts/fetch_statsbomb.py."
        )
    from app.statsbomb_event_feed import StatsBombEventFeed

    return StatsBombEventFeed()


def facts_for(match_id: str):
    """The numbered facts for one hero goal, read from `data/raw/`."""
    from app.narration_prompt import facts_from_buildup

    feed = make_feed()
    clock = HEROES[match_id]
    found = [
        moment
        for moment in feed.defining_moments(int(match_id))
        if (moment.minute, moment.second) == clock
    ]
    assert len(found) == 1, (
        f"match {match_id} has {len(found)} goals at "
        f"{clock[0]}:{clock[1]:02d}; the hero is one"
    )
    return facts_from_buildup(feed.buildup(int(match_id), found[0]))


def slot_facts(match_id: str):
    """The facts for one hero goal, with the names and teams on them.

    The six the team wrote say "MacAllister" and "France's half", so the
    recorded nicknames and the fixture's two teams have to be on the facts or
    the check reads a name it does not hold. The per-goal narration above
    names every player in full and needs neither, which is why there are two
    builders here.
    """
    from app.narration_prompt import facts_from_buildup
    from app.recorded_names import recorded_nicknames, recorded_teams

    feed = make_feed()
    clock = HEROES[match_id]
    found = [
        moment
        for moment in feed.defining_moments(int(match_id))
        if (moment.minute, moment.second) == clock
    ]
    assert len(found) == 1
    return facts_from_buildup(
        feed.buildup(int(match_id), found[0]),
        recorded_nicknames(int(match_id)),
        recorded_teams(int(match_id)),
    )


def missing_authorship(slot) -> str:
    """Why a frozen narration cannot be read as the team's writing.

    Empty when it can. Both halves are asked for: who wrote it, and the
    sentence a reader is owed beside it. A frozen narration that lost either
    could be taken for model output, which is the one thing the disclosure
    exists to prevent.
    """
    if slot.get("author") != authored.AUTHOR:
        return "the author is {!r} and not {!r}".format(
            slot.get("author"), authored.AUTHOR
        )
    if slot.get("authorship") != authored.AUTHORSHIP:
        return "the authorship is {!r} and not {!r}".format(
            slot.get("authorship"), authored.AUTHORSHIP
        )
    return ""


def voice_for(match_id: str) -> dict:
    """The keys this match sends a listener to, off `app/web/matches.json`."""
    doc = json.loads((WEB / "matches.json").read_text(encoding="utf-8"))
    match = next(
        one for one in doc["matches"] if str(one["match_id"]) == match_id
    )
    return match["hero"]["voice_for"]


class TestTheSixTheTeamWroteAreFrozen:
    """The six under `slots`, each with its authorship and its verdict.

    These are the narrations the moment card shows and `scripts/tts_hero.py`
    speaks, one per `hero.voice_for` key. They were written by the team and
    not by a model, so two things are held here: the authorship a reader is
    owed, and the check still passing on these exact words in the persona and
    for the listening side the slot is written for.
    """

    def slots(self, match_id: str) -> dict:
        return frozen()[match_id].get("slots") or {}

    def every_slot(self):
        for match_id in sorted(HEROES):
            for key, slot in sorted(self.slots(match_id).items()):
                yield match_id, key, slot

    def test_every_listener_has_a_narration(self):
        for match_id in sorted(HEROES):
            keys = sorted(set(voice_for(match_id).values()))
            assert sorted(self.slots(match_id)) == keys

    def test_there_are_six_of_them_and_no_two_are_alike(self):
        texts = [slot["text"] for _m, _k, slot in self.every_slot()]
        assert len(texts) == 6
        assert len(set(texts)) == 6

    def test_each_one_is_the_one_in_the_authored_source(self):
        """The frozen copy is not a second place the words can be edited:
        `scripts/authored_narrations.py` holds them and the freeze reads
        them."""
        for match_id, key, slot in self.every_slot():
            assert slot["text"] == authored.AUTHORED[(int(match_id), key)]

    def test_every_one_carries_its_authorship(self):
        for match_id, key, slot in self.every_slot():
            why = missing_authorship(slot)
            assert not why, "match {} slot {}: {}".format(match_id, key, why)

    def test_a_narration_that_lost_its_authorship_is_caught(self):
        """So the test above is not passing on an assertion nobody made."""
        _match_id, _key, slot = next(self.every_slot())
        stripped = {
            field: value
            for field, value in slot.items()
            if field != "authorship"
        }
        assert "the authorship is" in missing_authorship(stripped)
        assert "the author is" in missing_authorship(
            dict(slot, author="openai/gpt-oss-120b")
        )

    def test_the_check_still_passes_on_every_one(self):
        """The verdict, recomputed. This is the test the label rests on."""
        for match_id in sorted(HEROES):
            facts = slot_facts(match_id)
            for key, slot in sorted(self.slots(match_id).items()):
                result = check(
                    slot["text"],
                    facts,
                    persona=narrator_for(key),
                    side=slot["listener_side"],
                )
                assert result.grounded, (
                    "the frozen {} narration for match {} no longer passes "
                    "the grounding check, so it may not carry {!r}: {}".format(
                        key, match_id, GROUNDING_LABEL, result.summary
                    )
                )
                assert result.checked == slot["check"]["claims_checked"], (
                    "match {} slot {} was frozen on {} claim(s) and the "
                    "check now reads {}".format(
                        match_id,
                        key,
                        slot["check"]["claims_checked"],
                        result.checked,
                    )
                )

    def test_each_one_still_places_the_move_and_opens_on_a_name(self):
        """The two acceptance rules, held on the frozen copy as well: the
        freeze refuses a narration either one turns down, and this is what
        says so after the fact."""
        for match_id in sorted(HEROES):
            facts = slot_facts(match_id)
            for key, slot in sorted(self.slots(match_id).items()):
                assert places_missing(slot["text"], facts) == ""
                assert opener_missing(slot["text"], facts) == ""
                assert slot["places"] == list(zones_said(slot["text"], facts))

    def test_the_per_goal_narration_is_still_beside_them(self):
        """The six sit beside the one a model wrote rather than over it: it is
        the pipeline's own evidence and `docs/narration_runs/` is the rest."""
        for match_id in sorted(HEROES):
            entry = frozen()[match_id]
            assert entry["text"]
            assert entry["source"] == MODEL
            assert entry["model"]


class TestTheFrozenNarrationsAreStillGrounded:
    """The committed words, re-checked against the events on disk."""

    def test_both_heroes_are_frozen(self):
        assert sorted(frozen()) == sorted(HEROES)

    @pytest.mark.parametrize("match_id", sorted(HEROES))
    def test_the_check_still_passes(self, match_id):
        """The verdict, recomputed. This is the test the label rests on."""
        entry = frozen()[match_id]
        result = check(entry["tagged_text"], facts_for(match_id))
        assert result.grounded, (
            f"the frozen narration for match {match_id} no longer passes the "
            f"grounding check, so it may not carry "
            f"{GROUNDING_LABEL!r}: {result.summary}"
        )

    @pytest.mark.parametrize("match_id", sorted(HEROES))
    def test_the_recorded_verdict_matches_a_fresh_one(self, match_id):
        """The claim count too, not only the pass.

        A narration that still passes on fewer claims is one the check has
        stopped reading as closely, and `grounded` alone would not say so.
        """
        entry = frozen()[match_id]
        result = check(entry["tagged_text"], facts_for(match_id))
        assert result.checked == entry["check"]["claims_checked"], (
            f"match {match_id} was frozen on "
            f"{entry['check']['claims_checked']} claim(s) and the check now "
            f"reads {result.checked}"
        )
        assert entry["check"]["grounded"] is True
        assert entry["check"]["failures"] == []

    @pytest.mark.parametrize("match_id", sorted(HEROES))
    def test_the_shown_text_is_the_checked_text(self, match_id):
        """What the card shows is the passed text with its tags off.

        Nothing else may be shown under the label: the check passed the tagged
        form, and a `text` edited on its own would be unchecked copy wearing a
        verdict reached on other words.
        """
        entry = frozen()[match_id]
        assert entry["text"] == strip_citations(entry["tagged_text"])

    @pytest.mark.parametrize("match_id", sorted(HEROES))
    def test_the_model_wrote_it(self, match_id):
        """Not the template fallback.

        `scripts/tts_hero.py` used to speak `template_narration`, and the
        point of freezing was to replace it with words a model wrote. A
        `source` of "template" here would mean that quietly came back.
        """
        entry = frozen()[match_id]
        assert entry["source"] == MODEL
        assert entry["model"]
        # The permission to carry the grounding label, recorded as a boolean.
        # The words themselves are not in this file: `scripts/scan_copy.py`
        # refuses the label in a copy file, because nothing there can place it
        # over narration.
        assert entry["labelled"] is True

    @pytest.mark.parametrize("match_id", sorted(HEROES))
    def test_every_cited_fact_is_recorded_with_its_event(self, match_id):
        """A reader can follow any cited fact back to a record in data/raw/.

        The numbers are checked against the facts rebuilt from the events
        rather than against the file's own copy of them, so a fact list that
        renumbered underneath the narration is caught here.
        """
        entry = frozen()[match_id]
        facts = facts_for(match_id)
        by_number = {fact.number: fact for fact in facts.facts}
        assert entry["cited_facts"], "a narration cites at least one fact"
        for record in entry["cited_facts"]:
            fact = by_number.get(record["number"])
            assert fact is not None, (
                f"match {match_id} cites fact {record['number']}, which the "
                f"buildup no longer has"
            )
            assert record["event_id"] == fact.beat.event_id
            assert record["text"] == fact.text

    @pytest.mark.parametrize("match_id", sorted(HEROES))
    def test_the_citations_cover_the_sentences(self, match_id):
        """Every sentence of the narration cited something.

        `citations_by_sentence` is the audit trail a reader follows line by
        line, so an empty entry in it is a sentence nothing points at.
        """
        entry = frozen()[match_id]
        by_sentence = entry["citations_by_sentence"]
        assert by_sentence
        cited = set()
        for number, cites in by_sentence.items():
            assert cites, f"sentence {number} of match {match_id} cites nothing"
            cited.update(cites)
        assert cited == {record["number"] for record in entry["cited_facts"]}


class TestTheNarrationOnTheMomentCard:
    """Where the frozen narration shows, and what sits beside it.

    `CLAUDE.md` allows "Verified from play data" only over narration whose
    claims trace back to the event data. The frozen narration is the strongest
    thing on the card by that measure, because a test re-runs the check on it,
    so the label belongs beside it. `scripts/scan_copy.py` enforces the
    placement as a tree walk; these tests hold the order a reader sees.
    """

    def card(self) -> str:
        return CARD.read_text(encoding="utf-8")

    def test_the_card_has_a_narration_field(self):
        assert 'data-field="hero_narration"' in self.card()

    def test_the_inline_narration_is_the_frozen_neutral_1986_text(self):
        """The copy shown before the renderer runs is the default match's,
        as with every other field on this card, and it is the neutral slot's:
        the inline copy stands before the fan has said who they are with, and
        that is the key `renderNarration` falls back to."""
        slots = frozen()[str(DEFAULT_MATCH)]["slots"]
        assert slots[NEUTRAL_SLOT]["text"] in self.card()

    def test_the_other_listeners_tellings_are_not_in_the_markup(self):
        """One inline copy, and it is the one a fan with no answer reads.
        The other two arrive from narrations.json when the renderer runs."""
        slots = frozen()[str(DEFAULT_MATCH)]["slots"]
        for key, slot in slots.items():
            if key == NEUTRAL_SLOT:
                continue
            assert slot["text"] not in self.card()

    def test_the_renderer_picks_the_narration_by_the_listeners_key(self):
        """The card shows what the fan hears: the same lookup
        `app/web/narration-player.js` uses to pick the recording, so the text
        under the label and the voice reading it are one piece of writing."""
        renderer = RENDERER.read_text(encoding="utf-8")
        player = (WEB / "narration-player.js").read_text(encoding="utf-8")
        for source in (renderer, player):
            assert "voice_for" in source
            assert "listenerFor" in source or "Prelude.listenerFor" in source
        assert "slots" in renderer
        assert NEUTRAL_SLOT in renderer

    def test_the_narration_sits_under_the_header(self):
        markup = self.card()
        assert markup.index('data-field="hero_header"') < markup.index(
            'data-field="hero_narration"'
        )

    def test_the_grounding_label_sits_beside_the_narration(self):
        """One label on the card, after the narration and before the quote.

        It used to sit at the foot of the card beside the quote. A second copy
        of it would not be a second guarantee, so the one label moved to the
        narration rather than being duplicated.
        """
        markup = self.card()
        assert markup.count(GROUNDING_LABEL) == 1
        assert markup.index('data-field="hero_narration"') < markup.index(
            GROUNDING_LABEL
        )
        assert markup.index(GROUNDING_LABEL) < markup.index(
            'data-field="hero_quote"'
        )

    def test_the_quote_block_is_still_there(self):
        """Kept: it does not conflict with the narration.

        The quote names the same players in the same order as the facts the
        narration cites, so the two say the same thing in different registers.
        """
        assert 'data-field="hero_quote"' in self.card()

    def test_the_renderer_fills_the_narration_for_the_chosen_match(self):
        """Otherwise the 2022 card would show the 1986 narration."""
        renderer = RENDERER.read_text(encoding="utf-8")
        assert "narrations.json" in renderer
        assert '"hero_narration"' in renderer

    def test_the_scan_knows_the_narration_field_holds_narration(self):
        """`scripts/scan_copy.py` passes a label only where it shares a card
        with a field it knows holds narration. A new narration field that was
        not added to that list would make a correct placement a violation, and
        a reader fixing the gate by moving the label would make it a real one.
        """
        source = SCAN.read_text(encoding="utf-8")
        line = next(
            one for one in source.splitlines()
            if one.startswith("NARRATION_FIELDS")
        )
        assert "hero_narration" in line
