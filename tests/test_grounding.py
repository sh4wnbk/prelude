"""Tests for the grounding check.

Each test is one way a narration can be wrong, or one way it can look wrong and
be fine. The second kind matters as much as the first: the check fails a
narration whole and the pipeline throws it away, so a false positive costs a
good narration and makes a model look worse than it is. Three of the tests here
exist because the first live run produced exactly that, and the words it tripped
on ("Finally", "Argentina's", a clock the prompt itself had printed) are named in
the tests so they cannot come back.

Every narration here is in the past tense, carries a citation per sentence, and
ends on the goal, because those are the three things the check asks of a
narration before it reads a single claim. The numbers are the real fact numbers
for these two buildups, read out of `data/raw/` and written down, so a test says
which record it means rather than deriving it from the thing under test. The
facts worth knowing for the 1986 goal are in `FACTS_1986` below.

Nothing here calls a model. The narrations are written in the test.
"""

import pytest

from app.grounding import (
    ACTION_CLAIMS,
    BANNED_PATTERNS,
    FIRST_PERSON,
    PRESENT_TENSE,
    PRESENT_TENSE_PHRASES,
    TEAM_DEMONYMS,
    GroundingResult,
    NoSideForAPartisanVoice,
    bare,
    check,
    fold,
    name_parts,
    sentences,
    strip_citations,
)
from app.narration_prompt import (
    EVENT_VERBS,
    facts_from_buildup,
    template_narration,
)
from app.personas import THE_CALLER, THE_MATE, THE_STORYTELLER
from app.statsbomb_event_feed import StatsBombEventFeed

MATCH_1986 = 3750191
MATCH_2022 = 3869685

GOAL_1986 = (54, 18)
PENALTY_2022 = (22, 24)

# The facts of the 54:18 buildup this file cites, read out of data/raw/. The
# whole list is 24 facts, one per recorded event; these are the ones the tests
# point at. They are in the past tense, because the buildup already happened.
FACTS_1986 = """
   3. José Luis Cuciuffo (Argentina) passed, 54:03
   6. Héctor Adolfo Enrique (Argentina) passed, 54:06
   7. Diego Armando Maradona (Argentina) received the ball, 54:07
   8. Diego Armando Maradona (Argentina) carried the ball, 54:07
  10. Peter Beardsley (England) was dribbled past, 54:08
  11. Diego Armando Maradona (Argentina) dribbled, 54:08
  13. Peter Reid (England) pressed, 54:08
  14. Terry Butcher (England) was dribbled past, 54:13
  15. Diego Armando Maradona (Argentina) dribbled, 54:13
  16. Diego Armando Maradona (Argentina) carried the ball, 54:13
  17. Terry Fenwick (England) was dribbled past, 54:15
  18. Diego Armando Maradona (Argentina) dribbled, 54:15
  21. Peter Shilton (England) was dribbled past, 54:18
  22. Diego Armando Maradona (Argentina) dribbled, 54:18
  24. Diego Armando Maradona (Argentina) shot, 54:18
"""

# The 2022 penalty buildup reaches back a possession, so the foul that won it is
# in the list: 98 is Dembélé's Foul Committed, 99 is Di María's Foul Won, and
# 100 is Messi's shot.
FACTS_2022 = """
  98. Ousmane Dembélé (France) committed a foul, 20:53
  99. Ángel Fabián Di María Hernández (Argentina) won a foul, 20:53
 100. Lionel Andrés Messi Cuccittini (Argentina) shot, 22:24
"""

# The narration ends on the goal and nothing follows it, so a fragment about the
# run-up carries this as its last sentence. Fact 24 is the shot.
GOAL_SENTENCE = "[24] Diego Armando Maradona shot and scored for Argentina."
PENALTY_GOAL_SENTENCE = "[100] Messi shot and scored for Argentina."


def narration(*lines: str) -> str:
    """The lines given, ending on the goal, which the check requires."""
    return "\n".join(lines + (GOAL_SENTENCE,))


@pytest.fixture(scope="module")
def feed():
    return StatsBombEventFeed()


@pytest.fixture(scope="module")
def facts_1986(feed):
    """Maradona's second: open play, left foot, eight players, minute 54."""
    moment = next(
        m for m in feed.defining_moments(MATCH_1986)
        if (m.minute, m.second) == GOAL_1986
    )
    return facts_from_buildup(feed.buildup(MATCH_1986, moment))


@pytest.fixture(scope="module")
def facts_penalty(feed):
    moment = next(
        m for m in feed.defining_moments(MATCH_2022)
        if (m.minute, m.second) == PENALTY_2022
    )
    return facts_from_buildup(feed.buildup(MATCH_2022, moment))


def kinds(result: GroundingResult) -> set[str]:
    return {failure.kind for failure in result.failures}


class TestGrounded:
    """Narration the check has to accept."""

    def test_a_plain_grounded_line(self, facts_1986):
        result = check(
            "[22, 24] Maradona dribbled and shot, and scored for Argentina.",
            facts_1986,
        )
        assert result.grounded, result.summary

    def test_a_possessive_names_the_same_team(self, facts_1986):
        """The word pattern keeps apostrophes so O'Brien survives, which meant
        "Argentina's" arrived with its ending attached and matched nothing. Two
        model attempts died on this before the ending came off."""
        result = check(
            "[24] Argentina's Maradona shot.\n[24] Maradona's effort scored.",
            facts_1986,
        )
        assert result.grounded, result.summary

    def test_a_sentence_can_start_with_an_ordinary_word(self, facts_1986):
        """Three model attempts in a row failed on "Finally", which was this
        module's bug and not the model's."""
        result = check(
            "[24] Finally, Maradona shot for Argentina.\n"
            "[24] However, it was close.",
            facts_1986,
        )
        assert result.grounded, result.summary

    def test_a_demonym_grounds_against_its_team(self, facts_1986):
        """Fact 14 is recorded against England, which is what the demonym has
        to sit in; a demonym is checked in the cited facts like any name."""
        result = check(
            narration(
                "[14, 15] Maradona dribbled past the English defenders for "
                "Argentina."
            ),
            facts_1986,
        )
        assert result.grounded, result.summary

    def test_an_accented_name_spelled_plainly(self, facts_1986):
        """Hector for Héctor is a spelling variant of a player who is really
        there, not an invented one. Fact 6 is Enrique's pass and fact 7 is
        Maradona receiving it, so naming both ends of the pass needs both."""
        result = check(
            narration("[6, 7] Hector Enrique passed to Maradona."), facts_1986
        )
        assert result.grounded, result.summary

    def test_the_goal_minute_and_second(self, facts_1986):
        result = check(
            "[24] Maradona scored in minute 54, second 18.", facts_1986
        )
        assert result.grounded, result.summary

    def test_a_clock_quoted_from_the_fact_it_cites(self, facts_1986):
        """A per-second clock is groundable now, which it was not before the
        facts were numbered: 54:07 is fact 7's clock, and citing fact 7 is what
        makes it something a reader can be pointed at."""
        result = check(
            narration("[7] Maradona received it at 54:07."), facts_1986
        )
        assert result.grounded, result.summary

    def test_one_sentence_may_span_several_facts(self, facts_1986):
        """Two defenders beaten is two `Dribbled Past` records and two
        `Dribble` records, and the sentence that says so cites all four."""
        result = check(
            narration(
                "[14, 15, 17, 18] Maradona dribbled past Terry Butcher and "
                "Terry Fenwick."
            ),
            facts_1986,
        )
        assert result.grounded, result.summary

    def test_a_penalty_narration_may_say_penalty(self, facts_penalty):
        result = check(
            "[100] Messi scored from the penalty spot for Argentina.",
            facts_penalty,
        )
        assert result.grounded, result.summary

    def test_a_penalty_narration_may_say_a_foul_was_won(self, facts_penalty):
        """"won a foul" is a recorded Foul Won event, which is why "won" grounds
        against one instead of being refused as a claim about a result. One
        action per sentence, so the foul and the goal are two sentences."""
        result = check(
            "[99] Di Maria won a foul.\n"
            "[100] Messi scored from the penalty spot for Argentina.",
            facts_penalty,
        )
        assert result.grounded, result.summary

    def test_tags_written_after_the_full_stops(self, facts_1986):
        """`granite4:micro` put every tag just after the full stop and ran the
        sentences together on one line, and the splitter read each tag as part
        of the sentence it started, shifting every citation by one. The layout
        is not what was wrong with that narration, so narration written this way
        and citing correctly has to pass: fact 15 is a dribble, 16 the carry
        beside it, 24 the shot."""
        result = check(
            "Diego Armando Maradona dribbled past a defender. [15] "
            "He carried the ball. [16] "
            "He shot and scored for Argentina. [24]",
            facts_1986,
        )
        assert result.grounded, result.summary

    def test_every_fallback_narration_is_grounded(self, feed):
        """The fallback is grounded by construction, which is a claim worth
        testing rather than trusting. All nine goals, both matches."""
        for match_id in (MATCH_1986, MATCH_2022):
            for moment in feed.defining_moments(match_id):
                facts = facts_from_buildup(feed.buildup(match_id, moment))
                result = check(template_narration(facts), facts)
                assert result.grounded, f"{moment}: {result.summary}"


class TestTense:
    """A buildup is playback, so it is told in the past tense.

    The facts are written that way and the narration follows. A present-tense
    verb is not a weaker way of saying the past one: it narrates the passage as
    though it were still happening, which is a different claim from the one the
    records support.
    """

    def test_a_past_tense_narration_passes(self, facts_1986):
        result = check(
            "[7] Maradona received the ball inside his own half.\n"
            "[10, 11] He dribbled past Peter Beardsley.\n"
            "[14, 15] He dribbled past Terry Butcher.\n"
            "[24] Maradona shot and scored for Argentina.",
            facts_1986,
        )
        assert result.grounded, result.summary

    def test_a_present_tense_sentence_is_flagged(self, facts_1986):
        result = check(
            narration("[10, 11] Maradona dribbles past Peter Beardsley."),
            facts_1986,
        )
        assert not result.grounded
        assert kinds(result) == {"tense"}
        assert "dribbled" in result.summary

    def test_the_present_tense_of_every_action_word_is_refused(self, facts_1986):
        """One sentence per entry, so a word added to the table without a
        refusal behind it fails here rather than passing quietly."""
        for present, past in PRESENT_TENSE.items():
            result = check(
                narration(f"[24] Maradona {present} the ball."), facts_1986
            )
            assert not result.grounded, present
            assert "tense" in kinds(result), present
            assert past in result.summary, present

    def test_an_auxiliary_carries_the_tense_too(self, facts_1986):
        """"is dribbled past" holds the past participle the facts use, so the
        tense sits in "is" and a single word cannot catch it."""
        result = check(
            narration("[10] Peter Beardsley is dribbled past."), facts_1986
        )
        assert not result.grounded
        assert kinds(result) == {"tense"}
        assert "was dribbled past" in result.summary

    def test_the_past_participle_on_its_own_is_fine(self, facts_1986):
        """What is refused is the auxiliary, not the participle: the facts
        themselves say "was dribbled past"."""
        result = check(
            narration("[10] Peter Beardsley was dribbled past."), facts_1986
        )
        assert result.grounded, result.summary

    def test_won_a_foul_is_allowed(self, facts_penalty):
        result = check(
            "[99] Di Maria won a foul.\n" + PENALTY_GOAL_SENTENCE,
            facts_penalty,
        )
        assert result.grounded, result.summary

    def test_won_the_match_is_refused(self, facts_penalty):
        """The same word, and what is being won decides it: a `Foul Won` is a
        record, and the result of the match is in no buildup."""
        result = check(
            "[99] Di Maria won a foul.\n"
            "[100] Messi scored and Argentina won the match.",
            facts_penalty,
        )
        assert not result.grounded
        assert "outcome claim" in kinds(result)
        assert "won the match" in result.summary

    def test_winning_anything_the_buildup_cannot_show_is_refused(
        self, facts_1986
    ):
        for ending in ("won the game", "won the final", "won the World Cup"):
            result = check(
                f"[24] Maradona scored and Argentina {ending}.", facts_1986
            )
            assert not result.grounded, ending
            assert "outcome claim" in kinds(result), ending


class TestEnding:
    """The narration ends on the goal, and nothing follows it.

    There is no closing line addressed to the fan. The moment the goal lands the
    stadium takes over, so the app stops talking; `docs/VOICE.md` carries the
    reasoning. What the check can hold is where the narration stops, which is
    the sentence citing the shot the moment was built from.
    """

    def test_a_narration_that_ends_on_the_shot_passes(self, facts_1986):
        result = check(
            "[10, 11] Maradona dribbled past Peter Beardsley.\n"
            + GOAL_SENTENCE,
            facts_1986,
        )
        assert result.grounded, result.summary

    def test_a_last_sentence_that_does_not_cite_the_shot_is_refused(
        self, facts_1986
    ):
        result = check(
            "[24] Maradona shot and scored for Argentina.\n"
            "[10, 11] He had dribbled past Peter Beardsley to get there.",
            facts_1986,
        )
        assert not result.grounded
        assert kinds(result) == {"ending"}
        assert "fact 24" in result.summary

    def test_a_narration_that_stops_before_the_goal_is_refused(self, facts_1986):
        result = check(
            "[7] Maradona received the ball.\n"
            "[10, 11] He dribbled past Peter Beardsley.",
            facts_1986,
        )
        assert not result.grounded
        assert kinds(result) == {"ending"}

    def test_a_closing_line_addressed_to_the_fan_is_refused(self, facts_1986):
        """The shape the no-closer decision exists for: the passage, and then a
        sentence of the app's own. Citation placement cannot catch this one,
        because a closer can cite the goal's fact as easily as the goal sentence
        can, so what catches it is the second person: there is no line spoken to
        the fan for "you" to belong to."""
        result = check(
            GOAL_SENTENCE + "\n[24] That is the moment you came for.",
            facts_1986,
        )
        assert not result.grounded
        assert "address to the reader" in kinds(result)

    def test_what_the_ending_rule_alone_cannot_catch(self, facts_1986):
        """Worth knowing rather than implying otherwise. A closing line that
        cites the goal's fact, keeps out of the second person and asserts
        nothing checkable is refused by nothing here: the ending rule holds
        where the narration stops, not what its last sentence means."""
        result = check(
            GOAL_SENTENCE + "\n[24] That was the moment.", facts_1986
        )
        assert result.grounded, result.summary

    def test_the_fallback_ends_on_the_goal(self, feed):
        """All nine goals: the fallback's last sentence cites the shot."""
        for match_id in (MATCH_1986, MATCH_2022):
            for moment in feed.defining_moments(match_id):
                facts = facts_from_buildup(feed.buildup(match_id, moment))
                last = sentences(template_narration(facts))[-1]
                assert last.cites == (facts.goal_fact.number,), moment


class TestNotGrounded:
    """Narration the check has to refuse."""

    def test_an_invented_player(self, facts_1986):
        result = check(
            narration("[6, 7] Maradona passed to Valdano."), facts_1986
        )
        assert not result.grounded
        assert kinds(result) == {"name"}
        assert "Valdano" in result.summary

    def test_a_real_player_who_is_not_in_this_passage(self, facts_1986):
        """Rule 3 of the prompt says so explicitly: a real player who is not in
        the buildup is still not something this narration can point at."""
        result = check(
            narration("[7] Burruchaga squared it for Maradona."), facts_1986
        )
        assert not result.grounded
        assert kinds(result) == {"name"}

    def test_a_demonym_for_a_team_that_is_not_playing(self, facts_1986):
        result = check(
            narration("[22] The Brazilian defender could not stop Maradona."),
            facts_1986,
        )
        assert not result.grounded
        assert kinds(result) == {"name"}
        assert "Brazil" in result.summary

    def test_the_wrong_body_part(self, facts_1986):
        result = check("[24] Maradona headed it in for Argentina.", facts_1986)
        assert not result.grounded
        assert kinds(result) == {"body_part"}
        assert "Left Foot" in result.summary

    def test_a_goal_turned_into_a_set_piece(self, facts_1986):
        """The highest-value check here: the facts do not reveal the shot type,
        so a model can invent a penalty without contradicting anything it was
        shown."""
        result = check(
            "[24] Maradona scored the penalty for Argentina.", facts_1986
        )
        assert not result.grounded
        assert kinds(result) == {"shot_type"}
        assert "Open Play" in result.summary

    def test_a_set_piece_turned_into_the_wrong_one(self, facts_penalty):
        result = check(
            "[100] Messi scored from the corner for Argentina.", facts_penalty
        )
        assert not result.grounded
        assert kinds(result) == {"shot_type"}

    def test_an_action_that_is_not_in_the_buildup(self, facts_1986):
        result = check(narration("[21] Shilton saved it."), facts_1986)
        assert not result.grounded
        assert kinds(result) == {"action"}
        assert "Goal Keeper" in result.summary

    def test_an_action_that_is_in_the_buildup_but_not_in_the_cited_facts(
        self, facts_1986
    ):
        """A miscitation, not an invention, and the report says which it is: a
        retry that reads "not in the buildup" for a dribble that is in the
        buildup would be told to drop a true sentence."""
        result = check(
            narration("[7, 8] Maradona dribbled past a defender."), facts_1986
        )
        assert not result.grounded
        assert kinds(result) == {"action"}
        assert "not in the facts this sentence cites" in result.summary

    def test_a_number_that_is_not_a_minute(self, facts_1986):
        """7 is a second several events happened at, which is why a bare digit
        is grounded only by a minute or the goal's own second: a count would
        otherwise land on whatever second an event happened at."""
        result = check(
            narration("[22] Maradona beat 7 defenders in minute 54."),
            facts_1986,
        )
        assert not result.grounded
        assert kinds(result) == {"number"}

    def test_a_clock_from_a_fact_the_sentence_did_not_cite(self, facts_1986):
        """54:07 is a real clock in this buildup: it is fact 7's. Cited against
        fact 22, which is 54:18, it is a claim about the wrong event."""
        result = check(
            narration("[22] Maradona dribbled at 54:07."), facts_1986
        )
        assert not result.grounded
        assert kinds(result) == {"clock"}
        assert "54:07" in result.summary

    def test_a_name_in_the_buildup_but_not_in_the_cited_facts(self, facts_1986):
        """Fenwick is in the passage and fact 14 is Butcher, so this is the
        right action attached to the wrong player."""
        result = check(
            narration("[14] Terry Fenwick was dribbled past."), facts_1986
        )
        assert not result.grounded
        assert kinds(result) == {"name"}
        assert "Fenwick" in result.summary

    def test_the_miscitation_the_first_live_run_produced(self, facts_1986):
        """The first attempt of the first live run, verbatim. Fact 17 is Terry
        Fenwick being dribbled past; Maradona carrying the ball at the same
        second is fact 19. Every word of the sentence is in the passage and the
        clock is real, and it still cites the wrong record: the wrong player and
        the wrong action, both reported against the fact it named.

        It is in the present tense, because it was written before the voice was
        settled, so it is refused for that as well. Kept verbatim anyway: what
        it holds is that citing the wrong record is caught. The miscited carry
        is now reported as the tense mistake it also is, because a
        present-tense verb is refused before it is read as a claim, so the
        miscitation that survives as a claim is the wrong player.
        """
        result = check(
            "Diego Armando Maradona dribbles the ball (54:13). [15] "
            "Maradona carries the ball as he approaches the goal (54:15). [17] "
            "He shoots and scores the goal (54:18). [24]",
            facts_1986,
        )
        assert not result.grounded
        assert kinds(result) == {"name", "tense"}
        miscitations = [f for f in result.failures if f.kind != "tense"]
        assert miscitations
        assert all(f.sentence_number == 2 for f in miscitations)
        assert all("[17]" in f.value for f in miscitations)

    def test_a_sentence_that_cites_nothing(self, facts_1986):
        """Every sentence names the facts it used. One that does not cannot be
        read against anything, however true it reads."""
        result = check(
            "[7] Maradona received the ball.\n"
            "He carried it past a defender.\n" + GOAL_SENTENCE,
            facts_1986,
        )
        assert not result.grounded
        assert kinds(result) == {"untagged"}
        assert result.failures[0].sentence_number == 2

    def test_a_citation_that_is_not_one_of_the_facts(self, facts_1986):
        result = check(
            narration("[99] Maradona dribbled past a defender."), facts_1986
        )
        assert not result.grounded
        assert kinds(result) == {"citation"}
        assert "24 facts" in result.summary

    def test_a_verdict_nickname(self, facts_1986):
        result = check(
            "[24] Maradona scored the Goal of the Century.", facts_1986
        )
        assert not result.grounded
        assert "verdict nickname" in kinds(result)

    def test_an_editorial_epithet(self, facts_1986):
        """The first run that got past the name checks still called it "this
        decisive moment" and "a significant moment"."""
        result = check(
            "[24] Maradona scored a decisive goal for Argentina.", facts_1986
        )
        assert not result.grounded
        assert kinds(result) == {"editorial epithet"}

    def test_an_outcome_claim(self, facts_1986):
        """A buildup is one passage of play and carries no scoreline, so the
        result is outside the facts the narration was written from."""
        for line in (
            "[24] Maradona scored for Argentina, securing the victory.",
            "[24] Maradona scored the winner for Argentina.",
            "[24] Maradona's goal sealed the trophy for Argentina.",
            "[24] Maradona scored and Argentina won the match.",
        ):
            result = check(line, facts_1986)
            assert not result.grounded, line
            assert "outcome claim" in kinds(result), line

    def test_an_em_dash(self, facts_1986):
        result = check(
            "[24] Maradona turned away — and scored for Argentina.", facts_1986
        )
        assert not result.grounded
        assert "em dash" in kinds(result)

    def test_narration_that_asserts_nothing_checkable(self, facts_1986):
        """Prose that names nobody and quotes no clock has nothing tracing back
        to the data, so there is nothing for the label to be true about. A pass
        here would mean "found no problem", which is not the same as grounded.
        It cites its facts and it ends on the goal, so neither of those is what
        refuses it.
        """
        result = check(
            "[8] Just inside his own half, he turned away from two.\n"
            "[11] Past one, past another, still going.\n"
            "[24] He shot and scored.",
            facts_1986,
        )
        assert not result.grounded
        assert kinds(result) == {"unverifiable"}

    def test_every_failing_claim_is_reported_not_just_the_first(self, facts_1986):
        """A retry and a log both need the whole list."""
        result = check(
            narration(
                "[6, 7] Valdano passed to Burruchaga, who headed it in for "
                "Brazil."
            ),
            facts_1986,
        )
        assert len(result.failures) >= 3
        assert {"name", "body_part"} <= kinds(result)

    def test_a_failure_says_which_sentence_it_was_in(self, facts_1986):
        result = check(
            "[22] Maradona dribbled.\n[24] Valdano scored.", facts_1986
        )
        assert not result.grounded
        assert result.failures[0].sentence_number == 2
        assert "Valdano" in result.failures[0].sentence


class TestMisdescription:
    """The failure the old check could not see.

    Everything in a sentence can be in the passage and the sentence can still
    describe something that did not happen. This is the case `docs/VOICE.md`
    worked through as the check's limit, and it is the case the numbered facts
    and the pairing rule exist to catch.
    """

    # Beardsley, Reid and Butcher. The records show Beardsley, Butcher, Fenwick
    # and Shilton dribbled past (facts 10, 14, 17, 21) and Beardsley, Reid and
    # Butcher applying pressure (9, 13, 20). Reid pressured and was never
    # dribbled past, so this names three defenders beaten and one of them was
    # not.
    BEARDSLEY_REID_BUTCHER = (
        "[10, 11, 13, 14] Maradona dribbled past Peter Beardsley, Peter Reid "
        "and Terry Butcher.\n" + GOAL_SENTENCE
    )

    # The same sentence with Reid taken out, which is true and has to pass. The
    # two together are what show the refusal is about the pairing and not about
    # the shape of the sentence.
    BEARDSLEY_AND_BUTCHER = (
        "[10, 11, 14] Maradona dribbled past Peter Beardsley and Terry "
        "Butcher.\n" + GOAL_SENTENCE
    )

    def test_a_defender_who_pressured_was_not_dribbled_past(self, facts_1986):
        result = check(self.BEARDSLEY_REID_BUTCHER, facts_1986)
        assert not result.grounded, result.summary
        assert kinds(result) == {"pairing"}
        assert "Reid" in result.summary

    def test_only_the_misdescribed_name_is_reported(self, facts_1986):
        """Beardsley and Butcher were dribbled past, so the sentence is wrong
        about one defender and right about two. A report that failed all three
        would send a retry to rewrite the true part."""
        result = check(self.BEARDSLEY_REID_BUTCHER, facts_1986)
        assert len(result.failures) == 1
        assert "Beardsley" not in result.failures[0].value
        assert "Butcher" not in result.failures[0].value

    def test_it_still_fails_in_the_past_tense(self, facts_1986):
        """The sentence is past tense now, which the voice requires, and the
        tense was never what was wrong with it."""
        assert "dribbled past" in self.BEARDSLEY_REID_BUTCHER
        assert "dribbles" not in self.BEARDSLEY_REID_BUTCHER
        result = check(self.BEARDSLEY_REID_BUTCHER, facts_1986)
        assert "tense" not in kinds(result)
        assert kinds(result) == {"pairing"}

    def test_the_same_sentence_without_the_wrong_name_passes(self, facts_1986):
        result = check(self.BEARDSLEY_AND_BUTCHER, facts_1986)
        assert result.grounded, result.summary

    def test_every_word_of_it_is_in_the_passage(self, facts_1986):
        """Why the old check passed it: Reid is a recorded player, a Dribble is
        a recorded action, and nothing in the sentence is invented. Membership
        was never the thing that was wrong with it."""
        assert "reid" in name_parts(facts_1986)
        assert "Dribble" in facts_1986.actions
        assert "Pressure" in facts_1986.actions

    def test_a_citation_cannot_be_chosen_to_make_it_pass(self, facts_1986):
        """Reid has one record in this passage, a `Pressure`, so no set of
        citations pairs him with a dribble. The failure is not a tagging
        mistake a model can tag its way out of."""
        every_fact = ", ".join(str(n) for n in range(1, len(facts_1986.facts) + 1))
        result = check(
            narration(f"[{every_fact}] Maradona dribbled past Peter Reid."),
            facts_1986,
        )
        assert not result.grounded
        assert kinds(result) == {"pairing"}


class TestPairingRefusesSomeTrueSentences:
    """The cost of pairing, named rather than left to be discovered.

    Nothing in a sentence says which name goes with which action, so a sentence
    holding one action and a name outside that action is refused even when it is
    true. The prompt asks for one action per sentence because of this, and the
    same words in two sentences pass; `docs/VOICE.md` records the trade.
    """

    def test_two_clauses_in_one_sentence_are_refused(self, facts_penalty):
        result = check(
            "[99, 100] Di Maria won a foul and Messi scored for Argentina.",
            facts_penalty,
        )
        assert not result.grounded
        assert kinds(result) == {"pairing"}
        assert "Messi" in result.summary

    def test_the_same_words_in_two_sentences_pass(self, facts_penalty):
        result = check(
            "[99] Di Maria won a foul.\n[100] Messi scored for Argentina.",
            facts_penalty,
        )
        assert result.grounded, result.summary


class TestThePartisanVoice:
    """The one thing a persona changes: who may say "we".

    `app/personas.py` has the Mate writing as the listener's side, so that
    voice may call that side "we", "our" or "us". The Caller and the
    Storyteller are written as nobody, so the same word from them is a loyalty
    the app has put in its own mouth, and no voice may address the fan as
    "you".

    The 1986 buildup holds both teams, which is what makes the pair of tests
    below a pair: the same sentence, cited two ways, is grounded for an
    Argentina listener over fact 11 and refused over fact 10.
    """

    def test_our_citing_the_listeners_team_passes(self, facts_1986):
        """Fact 11 is Maradona's Dribble, recorded against Argentina."""
        result = check(
            narration("[11] Our captain dribbled past a defender."),
            facts_1986,
            persona=THE_MATE,
            side="Argentina",
        )
        assert result.grounded, result.summary

    def test_the_same_sentence_citing_the_other_team_fails(self, facts_1986):
        """Fact 10 is Beardsley's Dribbled Past, recorded against England.

        The sentence is one an England listener could be told and an
        Argentina listener could not, and nothing in the words says which.
        What decides it is the team on the record it cited.
        """
        result = check(
            narration("[10] Our captain dribbled past a defender."),
            facts_1986,
            persona=THE_MATE,
            side="Argentina",
        )
        assert not result.grounded
        assert "side" in kinds(result)
        assert "Argentina" in result.summary

    def test_the_same_sentence_passes_for_a_listener_on_that_side(
        self, facts_1986
    ):
        """Fact 10 is England's record, so an England listener may say it."""
        result = check(
            narration("[10] Our defender was dribbled past."),
            facts_1986,
            persona=THE_MATE,
            side="England",
        )
        assert result.grounded, result.summary

    def test_both_records_of_one_dribble_ground_it(self, facts_1986):
        """One cited fact is enough, which is how a name claim works too.

        Facts 10 and 11 are the two records of one dribble. A sentence citing
        both is true for an Argentina listener, and a rule asking every cited
        fact to be theirs would refuse it.
        """
        result = check(
            narration("[10, 11] We dribbled past Peter Beardsley."),
            facts_1986,
            persona=THE_MATE,
            side="Argentina",
        )
        assert result.grounded, result.summary

    def test_our_from_the_caller_fails(self, facts_1986):
        result = check(
            narration("[11] Our captain dribbled past a defender."),
            facts_1986,
            persona=THE_CALLER,
        )
        assert not result.grounded
        assert "first person" in kinds(result)

    def test_our_from_the_storyteller_fails(self, facts_1986):
        result = check(
            narration("[11] Our captain dribbled past a defender."),
            facts_1986,
            persona=THE_STORYTELLER,
        )
        assert not result.grounded
        assert "first person" in kinds(result)

    def test_we_and_us_are_refused_with_no_persona_at_all(self, facts_1986):
        """The default is the stricter one: nobody is partisan by default."""
        for line in (
            "[11] We went past a defender.",
            "[11] Maradona went past a defender for us.",
            "[11] We're past a defender.",
        ):
            result = check(narration(line), facts_1986)
            assert not result.grounded, line
            assert "first person" in kinds(result), line

    def test_you_is_refused_from_the_mate_too(self, facts_1986):
        """The narration is not addressed to the fan in any voice."""
        result = check(
            narration("[11] Your captain dribbled past a defender."),
            facts_1986,
            persona=THE_MATE,
            side="Argentina",
        )
        assert not result.grounded
        assert "address to the reader" in kinds(result)

    def test_the_mate_with_a_neutral_listener_is_refused(self, facts_1986):
        """A voice written as the listener's side needs one to be written as.

        Checking it as though nobody were partisan would be answering a
        question nobody asked, so both the prompt and the check raise.
        """
        with pytest.raises(NoSideForAPartisanVoice):
            check(narration(GOAL_SENTENCE), facts_1986, persona=THE_MATE)

    def test_a_partisan_narration_is_held_to_every_other_rule(self, facts_1986):
        """The Mate loosens the first person and nothing else.

        Reid pressured and was never dribbled past, which is the named
        misdescription in `TestMisdescription`. Saying it as "we" does not
        make it true.
        """
        result = check(
            narration("[11, 13] We dribbled past Peter Reid."),
            facts_1986,
            persona=THE_MATE,
            side="Argentina",
        )
        assert not result.grounded
        assert "pairing" in kinds(result)
        assert "Reid" in result.summary

    def test_the_first_person_patterns_hold_their_word_boundaries(self):
        """A contraction is caught and an ordinary word is not.

        The words are patterns rather than a word list because an apostrophe
        is a word boundary: the word loop reads "we're" as one word and
        strips nothing from it, so a list would miss it. The other half is
        that `\bus\b` must not fire on "because", which is what a pattern
        with its boundaries lost would do.
        """
        import re

        def hit(text):
            return any(re.search(p, text.lower()) for p in FIRST_PERSON)

        for said in ("we", "our", "ours", "us", "we're", "we've", "for us"):
            assert hit(said), said
        for said in ("because", "trust", "flour", "bus", "four", "pressure"):
            assert not hit(said), said

    def test_a_banned_word_is_banned_in_every_voice(self, facts_1986):
        for persona, side in (
            (THE_MATE, "Argentina"),
            (THE_CALLER, None),
            (THE_STORYTELLER, None),
        ):
            result = check(
                "[24] Maradona scored a decisive goal for Argentina.",
                facts_1986,
                persona=persona,
                side=side,
            )
            assert not result.grounded, persona.id
            assert "editorial epithet" in kinds(result), persona.id


class TestSentences:
    """Reading a narration into sentences and citations."""

    def test_a_sentence_carries_the_numbers_it_cites(self):
        read = sentences("[14, 15] Maradona dribbled past Terry Butcher.")
        assert len(read) == 1
        assert read[0].cites == (14, 15)
        assert read[0].text == "Maradona dribbled past Terry Butcher."
        assert read[0].number == 1

    def test_several_sentences_are_numbered_in_order(self):
        read = sentences("[1] First one.\n[2] Then another.")
        assert [s.number for s in read] == [1, 2]
        assert [s.cites for s in read] == [(1,), (2,)]

    def test_a_tag_after_the_full_stop_belongs_to_the_sentence_before(self):
        """The first chunk carries no tag, so the tags in this narration trail
        their sentences. Refusing that layout over where the full stop fell
        would throw away good copy."""
        read = sentences("Maradona shot. [24]")
        assert len(read) == 1
        assert read[0].cites == (24,)

    def test_the_layout_the_first_live_run_wrote(self):
        """`granite4:micro` put every tag just after the full stop and ran the
        sentences together on one line. Reading a tag as part of the chunk it
        starts shifted every citation by one and failed the narration for it,
        which was this module's bug and not the model's.
        """
        read = sentences(
            "Diego Armando Maradona dribbled past a defender. [15] "
            "He carried the ball. [16] "
            "He shot and scored for Argentina. [24]"
        )
        assert [s.cites for s in read] == [(15,), (16,), (24,)]
        assert [s.text for s in read] == [
            "Diego Armando Maradona dribbled past a defender.",
            "He carried the ball.",
            "He shot and scored for Argentina.",
        ]

    def test_tags_written_in_front_of_their_sentences(self):
        """The layout the prompt asks for. A tag opening the first chunk has no
        sentence before it to belong to, which is what settles the narration as
        citation-first."""
        read = sentences("[15] Maradona dribbled.\n[19] Maradona carried it.")
        assert [s.cites for s in read] == [(15,), (19,)]

    def test_an_untagged_sentence_in_a_citation_first_narration(self):
        """Why the layout is settled once per narration rather than per tag.
        Binding the third sentence's tag backwards would hand it to the second
        and leave the third citing nothing, which flags the wrong sentence and
        hides the one that cited nothing."""
        read = sentences(
            "[11] Maradona dribbled.\n"
            "He carried the ball.\n"
            "[24] Maradona shot."
        )
        assert [s.cites for s in read] == [(11,), (), (24,)]

    def test_a_fact_number_is_not_read_as_a_clock_or_a_count(self):
        """The tag comes out of the text before any claim is read, or every
        citation would be a number claim about the match clock."""
        assert "24" not in sentences("[24] Maradona shot.")[0].text

    def test_strip_citations_leaves_no_tag_and_one_paragraph(self):
        stripped = strip_citations(
            "[14, 15] Maradona dribbled past Terry Butcher.\n"
            "[24] Maradona shot and scored."
        )
        assert "[" not in stripped
        assert "\n" not in stripped
        assert stripped == (
            "Maradona dribbled past Terry Butcher. Maradona shot and scored."
        )

    def test_strip_citations_leaves_no_space_before_the_full_stop(self):
        assert strip_citations("Maradona shot [24].") == "Maradona shot."


class TestHelpers:
    def test_fold_strips_accents_and_case(self):
        assert fold("Héctor") == "hector"
        assert fold("MARADONA") == "maradona"

    def test_bare_strips_a_possessive(self):
        assert bare("argentina's") == "argentina"
        assert bare("argentina’s") == "argentina"
        assert bare("butchers'") == "butchers"
        assert bare("maradona") == "maradona"

    def test_name_parts_splits_full_names(self, facts_1986):
        parts = name_parts(facts_1986)
        assert {"maradona", "diego", "argentina", "england", "shilton"} <= parts

    def test_the_demonym_table_names_only_teams_in_the_data(self):
        """The table does not generalise, and a third match needs its own
        entries. This fails if one is added without a team to back it."""
        assert set(TEAM_DEMONYMS.values()) == {"Argentina", "England", "France"}

    def test_no_banned_pattern_is_blank(self):
        """A blank pattern would match every line and fail everything."""
        for label, pattern in BANNED_PATTERNS:
            assert label and pattern

    def test_every_action_claim_names_event_types_a_fact_can_say(self):
        """A claim whose event type no fact can be phrased from could never be
        matched, so it would refuse the word wherever it appeared."""
        for word, types in ACTION_CLAIMS.items():
            assert types, word
            assert types <= set(EVENT_VERBS), (word, types - set(EVENT_VERBS))

    def test_the_two_sided_action_words_name_both_records(self):
        """"X dribbled past Y" is a `Dribble` on X's record and a `Dribbled
        Past` on Y's. Without both in the set, naming the beaten defender would
        be reported as an invented action."""
        assert ACTION_CLAIMS["dribbled"] == {"Dribble", "Dribbled Past"}
        assert ACTION_CLAIMS["passed"] == {"Pass", "Ball Receipt*"}
        assert ACTION_CLAIMS["foul"] == {"Foul Committed", "Foul Won"}

    def test_the_action_words_are_past_tense_or_tenseless(self):
        """The facts are written in the past tense, so the words that ground an
        event are the past forms and the nouns. A present form here would be a
        word the check both grounds and refuses."""
        assert not set(ACTION_CLAIMS) & set(PRESENT_TENSE)
        for word in ("dribbled", "shot", "scored", "pressed", "recovered", "won"):
            assert word in ACTION_CLAIMS, word

    def test_every_present_form_has_a_past_form_the_check_knows(self):
        """A present-tense entry whose past form the check does not recognise
        would refuse a word and offer a replacement that fails too."""
        said = {verb.split()[0] for verb in EVENT_VERBS.values()}
        for present, past in PRESENT_TENSE.items():
            assert past in ACTION_CLAIMS or past in said, (present, past)

    def test_the_present_tense_phrases_offer_their_past_form(self):
        """Each phrase differs from its replacement only in the auxiliary."""
        for phrase, past in PRESENT_TENSE_PHRASES.items():
            assert past.split()[0] in ("was", "were")
            assert phrase.split()[1:] == past.split()[1:]

    def test_every_fact_verb_is_past_tense(self):
        """The facts are the narration's source, so a present-tense verb here
        would be asking the model to copy the thing the check refuses."""
        for action, verb in EVENT_VERBS.items():
            first = verb.split()[0]
            assert first not in PRESENT_TENSE, (action, verb)


class TestResult:
    def test_a_grounded_result_says_how_much_it_checked(self, facts_1986):
        result = check(
            "[24] Maradona shot and scored for Argentina.", facts_1986
        )
        assert result.grounded
        assert result.checked > 0
        assert "grounded" in result.summary

    def test_an_ungrounded_result_lists_its_claims(self, facts_1986):
        result = check("[24] Valdano scored.", facts_1986)
        assert not result.grounded
        assert "Valdano" in result.summary
        assert result.failures
