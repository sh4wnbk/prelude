"""Tests for the candidate run in `scripts/hero_candidates.py`.

No model is called and no connection is opened: every test here reads the
event data off disk and measures narration written in the test, or the two
narrations already frozen in `app/web/narrations.json`. `tests/conftest.py`
fails the suite if anything reaches the network.

What this script adds over `scripts/freeze_narrations.py` is the reporting:
which recorded players a candidate names, and what the three recordings of its
match would be billed for speaking it. Both are numbers Shawn chooses on, so
both are pinned here.

**The test that matters most is the three Peters.** Three of the four England
players in the 1986 buildup are called Peter, so coverage measured on any word
of a name would read a narration naming Peter Shilton as naming Beardsley and
Reid too, and a thin narration would score as a full one. The frozen 1986
narration names Beardsley and Shilton and does not name Reid, and that is
pinned below rather than left to a live run to notice.

The expected values are read out of `data/raw/` and written down as literals,
the way `tests/test_grounding.py` does it.
"""

import json
from pathlib import Path

import pytest

from app.grounding import strip_citations
from app.narration_prompt import facts_from_buildup, touched_the_ball
from app.statsbomb_event_feed import StatsBombEventFeed
from app.tts import speech_text
from scripts.tts_hero import DEFAULT_BUDGET
from scripts.hero_candidates import (
    DEFAULT_OUT,
    HEROES,
    alongside_billed,
    goals_to_run,
    merged,
    odd_characters,
    refreshed,
    DEFAULT_PER_GOAL,
    billed_for_match,
    coverage,
    distinctive_parts,
    main,
    moment_at,
    named_players,
    review,
)

ROOT = Path(__file__).resolve().parent.parent
NARRATIONS = ROOT / "app" / "web" / "narrations.json"

MATCH_1986 = 3750191
MATCH_2022 = 3869685

GOAL_1986 = (54, 18)
HERO_2022 = (35, 22)

# What the three recordings of each match are billed for the frozen narration,
# and the total, which `HANDOFF.md` records as the price of the run that
# scripts/tts_hero.py --plan reported: 1,959 billed characters, which cleared
# the budget of 2,000 that Task 7 then raised to 3,000. Read off the frozen
# text rather than restated from the doc.
BILLED_1986 = 918
BILLED_2022 = 1041
BILLED_BOTH = 1959


@pytest.fixture(scope="module")
def feed():
    return StatsBombEventFeed()


@pytest.fixture(scope="module")
def frozen():
    return json.loads(NARRATIONS.read_text(encoding="utf-8"))["narrations"]


def facts_for(feed, match_id, clock):
    return facts_from_buildup(
        feed.buildup(match_id, moment_at(feed, match_id, *clock))
    )


class TestDistinctiveParts:
    """A player is matched on the words of their name that are theirs alone."""

    def test_the_three_peters_are_told_apart(self, feed):
        facts = facts_for(feed, MATCH_1986, GOAL_1986)
        parts = distinctive_parts(facts)
        assert parts["Peter Beardsley"] == frozenset({"beardsley"})
        assert parts["Peter Reid"] == frozenset({"reid"})
        assert parts["Peter Shilton"] == frozenset({"shilton"})
        for player in ("Peter Beardsley", "Peter Reid", "Peter Shilton"):
            assert "peter" not in parts[player]

    def test_the_two_terrys_are_told_apart(self, feed):
        facts = facts_for(feed, MATCH_1986, GOAL_1986)
        parts = distinctive_parts(facts)
        assert parts["Terry Butcher"] == frozenset({"butcher"})
        assert parts["Terry Fenwick"] == frozenset({"fenwick"})

    def test_every_recorded_player_gets_something_to_match_on(self, feed):
        for match_id, clock in ((MATCH_1986, GOAL_1986), (MATCH_2022, HERO_2022)):
            facts = facts_for(feed, match_id, clock)
            parts = distinctive_parts(facts)
            recorded = {fact.beat.player for fact in facts.facts}
            assert set(parts) == recorded
            for player, mine in parts.items():
                assert mine, player

    def test_parts_are_folded_so_an_accent_is_not_needed(self, feed):
        """The check folds accents away and so does this, because a narration
        spelling Alvarez without one still names him."""
        facts = facts_for(feed, MATCH_2022, HERO_2022)
        parts = distinctive_parts(facts)
        assert "alvarez" in parts["Julián Álvarez"]


class TestNamedPlayers:
    def test_a_narration_naming_one_peter_names_only_him(self, feed):
        facts = facts_for(feed, MATCH_1986, GOAL_1986)
        named = named_players("Peter Shilton was dribbled past.", facts)
        assert named == ("Peter Shilton",)

    def test_a_surname_is_enough(self, feed):
        facts = facts_for(feed, MATCH_1986, GOAL_1986)
        assert named_players("Maradona shot.", facts) == (
            "Diego Armando Maradona",
        )

    def test_it_reads_through_the_punctuation(self, feed):
        facts = facts_for(feed, MATCH_1986, GOAL_1986)
        assert "Diego Armando Maradona" in named_players(
            "Then came Maradona, who shot.", facts
        )

    def test_the_players_come_back_in_the_recorded_order(self, feed):
        """The order of the move, not the order the narration mentions them,
        so two candidates are read against one list."""
        facts = facts_for(feed, MATCH_2022, HERO_2022)
        named = named_players(
            "Di María shot. Molina passed. Messi passed.", facts
        )
        assert named == (
            "Nahuel Molina Lucero",
            "Lionel Andrés Messi Cuccittini",
            "Ángel Fabián Di María Hernández",
        )

    def test_a_narration_naming_nobody_names_nobody(self, feed):
        facts = facts_for(feed, MATCH_2022, HERO_2022)
        assert named_players("The ball went in.", facts) == ()


class TestTheFrozenNarrationsScoreAsTheyWereDescribed:
    """The two narrations Task 6 froze, measured by this script.

    `HANDOFF.md` says what is wrong with them: the 2022 one names three of the
    five players who touched the ball and leaves out Messi and Alvarez,
    neither says the shot scored, and every sentence carries a clock. If this
    script does not report that, it is not measuring what Shawn is choosing
    on.
    """

    def test_the_2022_narration_misses_messi_and_alvarez(self, feed, frozen):
        facts = facts_for(feed, MATCH_2022, HERO_2022)
        entry = frozen[str(MATCH_2022)]
        cover = coverage(entry["text"], entry["tagged_text"], facts)
        assert len(cover["players_who_touched_the_ball"]) == 5
        assert cover["touched_not_named"] == (
            "Lionel Andrés Messi Cuccittini",
            "Julián Álvarez",
        )
        assert len(cover["touched_and_named"]) == 3

    def test_neither_frozen_narration_says_it_scored(self, feed, frozen):
        for match_id, clock in ((MATCH_1986, GOAL_1986), (MATCH_2022, HERO_2022)):
            facts = facts_for(feed, match_id, clock)
            entry = frozen[str(match_id)]
            cover = coverage(entry["text"], entry["tagged_text"], facts)
            assert cover["says_scored"] is False

    def test_every_sentence_of_both_carries_a_clock(self, feed, frozen):
        for match_id, clock in ((MATCH_1986, GOAL_1986), (MATCH_2022, HERO_2022)):
            facts = facts_for(feed, match_id, clock)
            entry = frozen[str(match_id)]
            cover = coverage(entry["text"], entry["tagged_text"], facts)
            assert cover["clocks"] == cover["sentences"]

    def test_the_1986_narration_names_no_player_who_touched_it_but_the_scorer(
        self, feed, frozen
    ):
        """It opens on a defender being beaten, so the two passes into the
        move are not in it."""
        facts = facts_for(feed, MATCH_1986, GOAL_1986)
        entry = frozen[str(MATCH_1986)]
        cover = coverage(entry["text"], entry["tagged_text"], facts)
        assert cover["touched_and_named"] == ("Diego Armando Maradona",)
        assert cover["touched_not_named"] == (
            "José Luis Cuciuffo",
            "Héctor Adolfo Enrique",
        )

    def test_reid_is_not_counted_as_named(self, feed, frozen):
        """The three Peters test, on the real text: the narration names
        Beardsley and Shilton and never mentions Reid."""
        facts = facts_for(feed, MATCH_1986, GOAL_1986)
        entry = frozen[str(MATCH_1986)]
        named = named_players(entry["text"], facts)
        assert "Peter Beardsley" in named
        assert "Peter Shilton" in named
        assert "Peter Reid" not in named


class TestBilledCharacters:
    """The price, which is what `scripts/tts_hero.py --budget` is set on."""

    def test_the_frozen_run_is_the_price_the_handoff_records(self, feed, frozen):
        """1,959 billed characters for the six recordings, which is the figure
        tts_hero.py --plan reported. Read off the frozen text here, so the two
        counts have to agree."""
        billed = {
            match_id: billed_for_match(match_id, frozen[str(match_id)]["text"])
            for match_id in (MATCH_1986, MATCH_2022)
        }
        assert billed[MATCH_1986] == BILLED_1986
        assert billed[MATCH_2022] == BILLED_2022
        assert sum(billed.values()) == BILLED_BOTH

    def test_it_counts_three_recordings_and_not_one(self, feed, frozen):
        """Every listener of a match hears the same narration in a different
        voice, so a candidate costs three requests."""
        text = frozen[str(MATCH_2022)]["text"]
        doc = json.loads(
            (ROOT / "app" / "web" / "matches.json").read_text(encoding="utf-8")
        )
        match = next(
            one for one in doc["matches"] if one["match_id"] == MATCH_2022
        )
        keys = set(match["hero"]["voice_for"].values())
        assert len(keys) == 3
        assert billed_for_match(MATCH_2022, text) > 2 * len(text)

    def test_whitespace_is_not_billed(self, feed, frozen):
        """IBM counts markup toward the character count and whitespace not, so
        the price sits below the submitted length by exactly the spaces in it.

        Padding the narration itself cannot be used to show this: `speech_text`
        refuses text that `strip_citations` would change, and that normalises
        runs of whitespace, so a padded narration is rejected before it is
        priced.
        """
        text = frozen[str(MATCH_2022)]["text"]
        doc = json.loads(
            (ROOT / "app" / "web" / "matches.json").read_text(encoding="utf-8")
        )
        match = next(
            one for one in doc["matches"] if one["match_id"] == MATCH_2022
        )
        header = match["hero"]["opening"]["header"]
        submitted = 0
        spaces = 0
        for key in sorted(set(match["hero"]["voice_for"].values())):
            persona_id, situation = key.rsplit("_", 1)
            spoken = speech_text(header, text, persona_id, situation)
            submitted += len(spoken)
            spaces += len(spoken) - len("".join(spoken.split()))
        assert spaces > 0
        assert billed_for_match(MATCH_2022, text) == submitted - spaces

    def test_a_longer_narration_costs_more(self, feed):
        short = "Maradona shot."
        longer = (
            "Peter Beardsley was dribbled past. Terry Butcher was dribbled "
            "past. Maradona shot."
        )
        assert billed_for_match(MATCH_1986, longer) > billed_for_match(
            MATCH_1986, short
        )


class TestTheRecordingBudget:
    """`--budget` in `scripts/tts_hero.py`, which Task 7 raised.

    The budget is the one guard between a run and the monthly allowance, and
    its default is the number a run uses when nobody passes one, so it is
    worth a test rather than only a docstring.
    """

    def test_the_default_is_three_thousand(self):
        """Raised from 2,000 for Task 7: the fuller narrations are longer, and
        the Task 6 pair cleared 2,000 by only 41 characters."""
        assert DEFAULT_BUDGET == 3000

    def test_the_frozen_run_still_fits_under_it(self, feed, frozen):
        """Raising a budget must not be what makes the current run pass: it
        passed under 2,000 too, at 1,959."""
        billed = sum(
            billed_for_match(match_id, frozen[str(match_id)]["text"])
            for match_id in (MATCH_1986, MATCH_2022)
        )
        assert billed == BILLED_BOTH
        assert billed <= DEFAULT_BUDGET

    def test_a_fuller_pair_of_narrations_can_still_exceed_it(self, feed):
        """Why the number is worth reading before freezing: a candidate that
        tells the whole move costs about 1,500 for its match, so two of them
        land near 3,000 rather than comfortably under it. The arithmetic is
        done here on text written in the test, not on a live run."""
        full_1986 = (
            "Jos\u00e9 Luis Cuciuffo recovered the ball, carried the ball and "
            "passed at 54:02. H\u00e9ctor Adolfo Enrique received the ball, "
            "carried the ball and passed. Diego Armando Maradona received the "
            "ball and carried the ball. Diego Armando Maradona dribbled past "
            "Peter Beardsley. Diego Armando Maradona dribbled past Terry "
            "Butcher. Diego Armando Maradona dribbled past Terry Fenwick. "
            "Diego Armando Maradona dribbled past Peter Shilton. Diego "
            "Armando Maradona shot and scored."
        )
        full_2022 = (
            "Nahuel Molina Lucero passed at 35:12. Alexis Mac Allister "
            "received the ball and passed. Lionel Andr\u00e9s Messi "
            "Cuccittini received the ball, carried the ball and passed. "
            "Juli\u00e1n \u00c1lvarez received the ball, carried the ball and "
            "passed. Alexis Mac Allister received the ball and passed. "
            "\u00c1ngel Fabi\u00e1n Di Mar\u00eda Hern\u00e1ndez received the "
            "ball. \u00c1ngel Fabi\u00e1n Di Mar\u00eda Hern\u00e1ndez shot "
            "with his left foot from open play and scored."
        )
        together = billed_for_match(MATCH_1986, full_1986) + billed_for_match(
            MATCH_2022, full_2022
        )
        assert together > BILLED_BOTH
        assert together > DEFAULT_BUDGET


class TestCoverage:
    def test_it_counts_the_sentences_carrying_a_clock(self, feed):
        facts = facts_for(feed, MATCH_2022, HERO_2022)
        tagged = (
            "[1] Nahuel Molina Lucero passed at 35:12.\n"
            "[2] Alexis Mac Allister received the ball.\n"
            "[13] Ángel Fabián Di María Hernández scored."
        )
        cover = coverage(
            "Nahuel Molina Lucero passed at 35:12. Alexis Mac Allister "
            "received the ball. Ángel Fabián Di María "
            "Hernández scored.",
            tagged,
            facts,
        )
        assert cover["sentences"] == 3
        assert cover["clocks"] == 1
        assert cover["says_scored"] is True

    def test_it_reports_the_facts_the_candidate_cited(self, feed):
        facts = facts_for(feed, MATCH_2022, HERO_2022)
        tagged = "[1] Molina passed.\n[13] Di María scored."
        cover = coverage("Molina passed. Di María scored.", tagged, facts)
        assert cover["cited_facts"] == (1, 13)

    def test_a_full_telling_names_everyone_who_touched_the_ball(self, feed):
        """The shape Task 7 asks for, scored by this script: five of five."""
        facts = facts_for(feed, MATCH_2022, HERO_2022)
        text = (
            "Nahuel Molina Lucero passed at 35:12. Alexis Mac Allister "
            "received the ball. Lionel Andrés Messi Cuccittini passed. "
            "Julián Álvarez passed. Alexis Mac Allister passed. "
            "Ángel Fabián Di María Hernández scored."
        )
        cover = coverage(text, "[13] " + text, facts)
        assert cover["touched_not_named"] == ()
        assert len(cover["touched_and_named"]) == len(touched_the_ball(facts))


class TestWhichGoalsRun:
    """`--match`, so one goal can be rerun while the other is settled."""

    def test_no_match_given_runs_both(self):
        assert goals_to_run([]) == HEROES

    def test_one_match_runs_one_goal(self):
        assert [hero[1] for hero in goals_to_run([MATCH_1986])] == [MATCH_1986]

    def test_the_order_is_the_hero_order_not_the_argument_order(self):
        both = goals_to_run([MATCH_2022, MATCH_1986])
        assert [hero[1] for hero in both] == [MATCH_1986, MATCH_2022]

    def test_a_match_that_is_not_a_hero_is_refused(self):
        with pytest.raises(SystemExit) as raised:
            goals_to_run([999])
        assert "not one of the hero goals" in str(raised.value)


class TestTheCounterpartsPrice:
    """`--alongside`, which turns a settled goal into an allowance."""

    def test_it_reads_the_billed_count_off_the_candidate(self, tmp_path, frozen):
        text = frozen[str(MATCH_2022)]["text"]
        path = tmp_path / "hero_candidates_2026-10-30.json"
        path.write_text(
            json.dumps(
                {
                    "model": "m",
                    "provider": "p",
                    "generated_on": "2026-10-30",
                    "goals": [
                        {
                            "match_id": MATCH_2022,
                            "candidates": [{"slot": 4, "text": text}],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        match_id, slot, billed = alongside_billed("3869685=4", path)
        assert (match_id, slot) == (MATCH_2022, 4)
        # Recomputed from the text, not read out of the file, so it is the
        # same arithmetic scripts/tts_hero.py will do on the day.
        assert billed == billed_for_match(MATCH_2022, text)

    @pytest.mark.parametrize("value", ["3869685", "3869685=4=1", "x=4"])
    def test_a_malformed_argument_is_refused(self, value, tmp_path):
        with pytest.raises(SystemExit):
            alongside_billed(value, tmp_path / "nothing.json")

    def test_a_missing_file_is_refused(self, tmp_path):
        with pytest.raises(SystemExit) as raised:
            alongside_billed("3869685=4", tmp_path / "nothing.json")
        assert "does not exist" in str(raised.value)

    def test_a_slot_that_is_not_there_is_refused(self, tmp_path):
        path = tmp_path / "hero_candidates_2026-10-30.json"
        path.write_text(
            json.dumps(
                {
                    "goals": [
                        {
                            "match_id": MATCH_2022,
                            "candidates": [{"slot": 4, "text": "x"}],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        with pytest.raises(SystemExit) as raised:
            alongside_billed("3869685=9", path)
        assert "has no candidate 9" in str(raised.value)


class TestMergingARerunIntoTheDocument:
    """The bug this exists for, and it cost real data once.

    The candidates document is named by the day. On 2026-10-30 a run narrated
    both goals and then a rerun of the 1986 goal alone wrote the same filename
    again, so the file held 1986 only and the five 2022 candidates were gone:
    their `tagged_text` with them, which is the only copy of the citations the
    model wrote and the thing a freeze re-reads. A rerun now carries across
    every goal it did not narrate.
    """

    def goal(self, match_id, slots, **extra):
        one = {
            "match_id": match_id,
            "year": 1986 if match_id == MATCH_1986 else 2022,
            "candidates": [{"slot": slot} for slot in slots],
        }
        one.update(extra)
        return one

    def test_a_goal_this_run_did_not_narrate_is_carried_across(
        self, tmp_path, capsys
    ):
        path = tmp_path / "hero_candidates_2026-10-30.json"
        path.write_text(
            json.dumps(
                {"goals": [self.goal(MATCH_2022, [1, 2, 3, 4, 5])]}
            ),
            encoding="utf-8",
        )
        out = merged([self.goal(MATCH_1986, [1, 2])], path)
        assert [one["match_id"] for one in out] == [MATCH_1986, MATCH_2022]
        carried = next(
            one for one in out if one["match_id"] == MATCH_2022
        )
        assert len(carried["candidates"]) == 5

    def test_a_goal_this_run_did_narrate_replaces_its_older_self(
        self, tmp_path
    ):
        path = tmp_path / "hero_candidates_2026-10-30.json"
        path.write_text(
            json.dumps({"goals": [self.goal(MATCH_1986, [1, 2])]}),
            encoding="utf-8",
        )
        out = merged([self.goal(MATCH_1986, [7, 8, 9])], path)
        assert len(out) == 1
        assert [one["slot"] for one in out[0]["candidates"]] == [7, 8, 9]

    def test_no_file_yet_means_nothing_to_carry(self, tmp_path):
        goals = [self.goal(MATCH_1986, [1])]
        assert merged(goals, tmp_path / "nothing.json") == goals

    def test_a_bare_list_from_the_first_run_is_still_read(self, tmp_path):
        """The shape the very first run wrote, before the document had
        provenance. A rerun must not drop its goals either."""
        path = tmp_path / "hero_candidates_2026-10-30.json"
        path.write_text(
            json.dumps([self.goal(MATCH_2022, [1, 2])]), encoding="utf-8"
        )
        out = merged([self.goal(MATCH_1986, [1])], path)
        assert [one["match_id"] for one in out] == [MATCH_1986, MATCH_2022]

    def test_the_carried_goal_keeps_its_own_provenance(self, tmp_path):
        """A merged document holds goals from two runs, so a reader and the
        freeze can tell which model wrote which."""
        path = tmp_path / "hero_candidates_2026-10-30.json"
        path.write_text(
            json.dumps(
                {
                    "goals": [
                        self.goal(
                            MATCH_2022,
                            [1],
                            generated_on="2026-10-30",
                            model="openai/gpt-oss-120b",
                        )
                    ]
                }
            ),
            encoding="utf-8",
        )
        out = merged(
            [self.goal(MATCH_1986, [1], generated_on="2026-10-31")], path
        )
        carried = next(one for one in out if one["match_id"] == MATCH_2022)
        assert carried["generated_on"] == "2026-10-30"
        assert carried["model"] == "openai/gpt-oss-120b"


class TestOddCharacters:
    """Characters a model reached for that nothing in the pipeline asked for.

    Two candidates have arrived carrying one and neither was visible. Both
    passed the grounding check, correctly, and both would have been sent to
    the speech service as written.
    """

    def test_a_narrow_no_break_space_is_reported(self):
        """Candidate 5 of the 1986 rerun put one inside "Terry Butcher"."""
        found = odd_characters("Terry Butcher")
        assert [name for _, name in found] == ["NARROW NO-BREAK SPACE"]

    def test_a_non_breaking_hyphen_is_reported(self):
        """The 4,299-character candidate wrote "fifty-four" with one."""
        found = odd_characters("fifty‑four")
        assert [name for _, name in found] == ["NON-BREAKING HYPHEN"]

    def test_an_accented_name_is_not_reported(self):
        """A recorded name carries accents: that is how the data spells it."""
        assert odd_characters(
            "Ángel Fabián Di María Hernández, "
            "José Luis Cuciuffo, Héctor Adolfo Enrique, "
            "Julián Álvarez"
        ) == ()

    def test_plain_ascii_is_not_reported(self):
        assert odd_characters(
            "Maradona shot and scored at 54:18; nobody else touched it."
        ) == ()

    def test_an_em_dash_is_reported(self):
        """`app/grounding.py` already refuses this one, so it should never
        reach a candidate. Reported anyway, because the report is what catches
        the characters no rule names."""
        assert [name for _, name in odd_characters("a — b")] == ["EM DASH"]

    def test_each_character_is_reported_once(self):
        found = odd_characters("a b c d")
        assert len(found) == 1

    def test_the_kept_candidates_carry_it_in_their_coverage(self, feed):
        facts = facts_for(feed, MATCH_1986, GOAL_1986)
        clean = coverage(
            "Maradona scored.", "[24] Maradona scored.", facts
        )
        assert clean["odd_characters"] == []
        dirty = coverage(
            "Terry Butcher was dribbled past.",
            "[14] Terry Butcher was dribbled past.",
            facts,
        )
        assert dirty["odd_characters"][0]["codepoint"] == "U+202F"


class TestRefreshing:
    """`--refresh`, which remeasures written candidates and calls no model."""

    def document(self, feed, text=None, tagged=None):
        facts = facts_for(feed, MATCH_1986, GOAL_1986)
        tagged = tagged or "[24] Diego Armando Maradona shot and scored."
        text = text if text is not None else strip_citations(tagged)
        return {
            "model": "openai/gpt-oss-120b",
            "provider": "watsonx",
            "generated_on": "2026-10-30",
            "goals": [
                {
                    "year": 1986,
                    "match_id": MATCH_1986,
                    "minute": 54,
                    "second": 18,
                    "player": "Diego Armando Maradona",
                    "team": "Argentina",
                    "facts": len(facts.facts),
                    "recorded_players": tuple(
                        dict.fromkeys(f.beat.player for f in facts.facts)
                    ),
                    "players_who_touched_the_ball": touched_the_ball(facts),
                    "candidates": [
                        {
                            "slot": 1,
                            "text": text,
                            "tagged_text": tagged,
                            "attempt": 1,
                            "first_attempt_grounded": True,
                            "claims_checked": 0,
                            "billed_characters": 0,
                            "coverage": {},
                        }
                    ],
                    "dropped": [],
                    "over_budget": [],
                    "allowance": None,
                }
            ],
        }

    def test_it_recomputes_the_price_and_the_coverage(self, feed):
        out = refreshed(self.document(feed))
        one = out["goals"][0]["candidates"][0]
        assert one["billed_characters"] == billed_for_match(
            MATCH_1986, one["text"]
        )
        assert one["claims_checked"] > 0
        assert one["coverage"]["says_scored"] is True
        assert "odd_characters" in one["coverage"]

    def test_a_candidate_that_stopped_passing_refuses_the_refresh(self, feed):
        """A refresh rewrites the file Shawn chooses from, so it does not
        quietly carry forward a narration the data no longer supports."""
        doc = self.document(
            feed, tagged="[1] Diego Armando Maradona shot and scored."
        )
        with pytest.raises(SystemExit) as raised:
            refreshed(doc)
        assert "no longer passes the check" in str(raised.value)


class TestTheRunRefusesToWriteIntoTheRepo:
    """A candidate is not a narration the app may speak, so it stays out."""

    def test_the_default_out_is_outside_the_repo(self):
        assert ROOT != DEFAULT_OUT
        assert ROOT not in DEFAULT_OUT.resolve().parents

    def test_an_out_inside_the_repo_is_refused(self, capsys):
        with pytest.raises(SystemExit) as raised:
            main(["--plan", "--out", str(ROOT / "docs")])
        assert "inside the repo" in str(raised.value)

    def test_the_repo_root_itself_is_refused(self):
        with pytest.raises(SystemExit) as raised:
            main(["--plan", "--out", str(ROOT)])
        assert "inside the repo" in str(raised.value)


class TestThePlan:
    """Nothing is sent without `--confirm`, and the count comes first."""

    def test_the_plan_sends_nothing_and_states_the_call_count(self, capsys):
        assert main(["--plan"]) == 0
        printed = capsys.readouterr().out
        attempts = 3
        wanted = DEFAULT_PER_GOAL * len(HEROES)
        assert "at most {} generations".format(wanted * attempts) in printed
        assert "nothing was sent" in printed
        assert "freezes   nothing" in printed

    def test_no_argument_at_all_still_sends_nothing(self, capsys):
        assert main([]) == 0
        assert "nothing was sent" in capsys.readouterr().out

    def test_the_plan_says_the_decoding_is_pinned(self, capsys):
        """Unpinned, watsonx decodes greedily and five candidates would be one
        candidate five times."""
        main(["--plan"])
        printed = capsys.readouterr().out
        assert "temperature 0.8" in printed
        assert "greedily" in printed

    def test_per_goal_has_to_be_a_count(self):
        with pytest.raises(SystemExit):
            main(["--plan", "--per-goal", "0"])


class TestTheReviewFile:
    """The file Shawn reads to choose, built without a model."""

    def test_it_holds_every_candidate_with_its_price_and_coverage(self, feed):
        facts = facts_for(feed, MATCH_2022, HERO_2022)
        text = (
            "Nahuel Molina Lucero passed at 35:12. Ángel Fabián Di "
            "María Hernández scored."
        )
        goals = [
            {
                "year": 2022,
                "match_id": MATCH_2022,
                "minute": 35,
                "second": 22,
                "player": "Ángel Fabián Di María Hernández",
                "team": "Argentina",
                "facts": len(facts.facts),
                "recorded_players": tuple(
                    dict.fromkeys(f.beat.player for f in facts.facts)
                ),
                "players_who_touched_the_ball": touched_the_ball(facts),
                "candidates": [
                    {
                        "slot": 1,
                        "text": text,
                        "tagged_text": "[1] " + text,
                        "attempt": 1,
                        "first_attempt_grounded": True,
                        "claims_checked": 12,
                        "billed_characters": billed_for_match(
                            MATCH_2022, text
                        ),
                        "coverage": coverage(text, "[1] " + text, facts),
                    }
                ],
                "dropped": [],
            }
        ]
        out = review(goals, "openai/gpt-oss-120b", "watsonx")
        assert "# Hero narration candidates" in out
        assert "Candidate 1" in out
        assert text in out
        assert "openai/gpt-oss-120b" in out
        assert "Nothing here is frozen" in out
        assert str(billed_for_match(MATCH_2022, text)) in out

    def test_it_says_so_when_a_goal_got_no_candidate(self, feed):
        goals = [
            {
                "year": 1986,
                "match_id": MATCH_1986,
                "minute": 54,
                "second": 18,
                "player": "Diego Armando Maradona",
                "team": "Argentina",
                "facts": 24,
                "recorded_players": ("Diego Armando Maradona",),
                "players_who_touched_the_ball": ("Diego Armando Maradona",),
                "candidates": [],
                "dropped": [{"slot": 1, "attempts": 3, "failures": ["x"]}],
            }
        ]
        out = review(goals, "openai/gpt-oss-120b", "watsonx")
        assert "No candidate for this goal passed." in out
        assert "reached the template fallback" in out

    def test_it_has_no_em_dashes(self, feed, frozen):
        facts = facts_for(feed, MATCH_2022, HERO_2022)
        entry = frozen[str(MATCH_2022)]
        goals = [
            {
                "year": 2022,
                "match_id": MATCH_2022,
                "minute": 35,
                "second": 22,
                "player": "Ángel Fabián Di María Hernández",
                "team": "Argentina",
                "facts": len(facts.facts),
                "recorded_players": tuple(
                    dict.fromkeys(f.beat.player for f in facts.facts)
                ),
                "players_who_touched_the_ball": touched_the_ball(facts),
                "candidates": [
                    {
                        "slot": 1,
                        "text": entry["text"],
                        "tagged_text": entry["tagged_text"],
                        "attempt": 1,
                        "first_attempt_grounded": True,
                        "claims_checked": 40,
                        "billed_characters": 1041,
                        "coverage": coverage(
                            entry["text"], entry["tagged_text"], facts
                        ),
                    }
                ],
                "dropped": [],
            }
        ]
        out = review(goals, "openai/gpt-oss-120b", "watsonx")
        assert "—" not in out
        assert "–" not in out
