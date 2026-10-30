"""The frozen hero narrations still pass the grounding check against data/raw/.

`app/web/narrations.json` holds a narration per hero goal that
`openai/gpt-oss-120b` wrote once and `scripts/freeze_narrations.py` kept
because `app/grounding.py` passed it. From then on those words are committed
copy: the moment card shows them under "Verified from play data" and
`scripts/tts_hero.py` sends them to be spoken.

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

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
NARRATIONS = ROOT / "app" / "web" / "narrations.json"

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
        assert entry["label"] == GROUNDING_LABEL

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
