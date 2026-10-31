"""The eight reference narrations, and the lines the check has to refuse.

**These are the standard, not the recordings.** Eight narrations, two goals by
four narrator-and-side slots, written to the framework in `docs/VOICE.md`:
Prelude is the recap stage of a goal call, so a narration starts at the
catalyst, tells the decisive part and lands the finish. They say what a
commentator would say about these two passages, and they say nothing the
records do not hold. What they are for is to hold `app/grounding.py` to a
standard a listener would recognise, word for word.

**They never go into a prompt for these two goals.** A reference pasted into
the prompt for the goal it describes would be dictation: the model would give
the words back, the check would pass them, and nothing would have been
measured. `scripts/hero_candidates.py` generates the candidates for these two
goals and nothing here reaches it. The style a narrator is shown is worked
through an invented match with invented players instead, which is Task 9c.

**They fail today, and the failure is the point.** `app/grounding.py` reads a
sentence against the fact numbers that sentence cited, and none of these
carries a citation tag, so every one of them is refused as `untagged` right
now. Task 9b teaches the check the grammar these lines are written in: a name
part that identifies one player, "he" and "his" resolved to the player being
followed, a chain ("Molina to MacAllister") read as a recorded pass, an action
named before its player, "past X" as a dribble past X, "we" over the listener
side's own recorded actions, and where an exclamation mark may stand. Until
then the eight tests in `TestTheReferences` are red and say what is owed.

The refusals below are the other half of the standard, and they pass today.
Each is one of the references with one thing changed: a chain the records do
not hold, a name part that fits two players, a claim about the shape of a
carry, the first person from a side the passage records nothing for, an
exclamation mark where the listener would not cheer, and a clock. They are
refused now because nothing here cites a fact, and they have to stay refused
once the grammar can read them, which is the only reason they are worth
writing down before the grammar exists.

Nothing here calls a model. The narrations are written in the test, and the
facts come off `data/raw/`.
"""

import pytest

from app.grounding import check
from app.narration_prompt import facts_from_buildup
from app.personas import THE_BUDDY, THE_CALLER, THE_STORYTELLER
from app.recorded_names import recorded_nicknames
from app.statsbomb_event_feed import StatsBombEventFeed

MATCH_1986 = 3750191
MATCH_2022 = 3869685

#: The two hero goals, the ones the recordings speak.
HERO_1986 = (54, 18)
HERO_2022 = (35, 22)

# The 1986 buildup as the facts number it, read out of data/raw/ and written
# down so a test says which record it means. Twenty-four facts; these are the
# ones the references and the refusals below stand on. The recorded nicknames
# are on them, which for this match is one name: Héctor Adolfo Enrique is
# "Héctor Enrique", and the lineups file records none for Maradona.
#
#    1. José Luis Cuciuffo (Argentina) recovered the ball, 54:02
#    3. José Luis Cuciuffo (Argentina) passed, 54:03          -> Enrique
#    6. Héctor Enrique (Argentina) passed, 54:06              -> Maradona, goal_assist
#    7. Diego Armando Maradona (Argentina) received the ball, 54:07   x 55.2
#    9. Peter Beardsley (England) pressed, 54:07
#   10. Peter Beardsley (England) was dribbled past, 54:08
#   11. Diego Armando Maradona (Argentina) dribbled, 54:08    under_pressure
#   13. Peter Reid (England) pressed, 54:08
#   14. Terry Butcher (England) was dribbled past, 54:13
#   17. Terry Fenwick (England) was dribbled past, 54:15
#   19. Diego Armando Maradona (Argentina) carried the ball, 54:15   -> x 112.8
#   20. Terry Butcher (England) pressed, 54:17
#   21. Peter Shilton (England) was dribbled past, 54:18
#   24. Diego Armando Maradona (Argentina) shot, 54:18        Left Foot
#
# Every event in it carries play_pattern "From Counter", and every one of
# Maradona's five carries and four dribbles carries under_pressure.

# The 2022 buildup, the Di María goal, whole: thirteen facts, five players,
# four of them with a recorded nickname.
#
#    1. Nahuel Molina (Argentina) passed, 35:12               -> MacAllister
#    3. Alexis MacAllister (Argentina) passed, 35:14          -> Messi
#    6. Lionel Messi (Argentina) passed, 35:15                -> Álvarez
#    9. Julián Álvarez (Argentina) passed, 35:17              -> MacAllister, 38.5 long
#   11. Alexis MacAllister (Argentina) passed, 35:20          -> Di María, goal_assist
#   12. Ángel Di María (Argentina) received the ball, 35:22    x 111.8
#   13. Ángel Di María (Argentina) shot, 35:22                Left Foot, first_time
#
# Every event carries play_pattern "From Counter", the whole move runs from
# 00:35:12.890 to 00:35:22.647, and every record in it is Argentina's: France
# has no event in this passage at all.

STORYTELLER_1986 = (
    "Cuciuffo's recovery started the counter, and Enrique played it to "
    "Maradona just inside his own half, who carried it forward under pressure "
    "past Beardsley, Butcher and Fenwick and took it into the box, where he "
    "went around Peter Shilton and scored with his left foot."
)

BUDDY_1986_ARGENTINA = (
    "We won it back through Cuciuffo and Enrique gave it to Maradona in his "
    "own half, and from there it was all him: past Beardsley, Butcher and "
    "Fenwick, on into the box, around Shilton, and he scored with his left "
    "foot!"
)

BUDDY_1986_ENGLAND = (
    "Maradona picked it up in his own half, and though Beardsley and Reid "
    "closed him down and Butcher came back at him, he went past Beardsley, "
    "Butcher and Fenwick, got around Shilton in the box, and scored."
)

CALLER_1986 = (
    "It started with a Cuciuffo recovery, Enrique to Maradona just inside his "
    "own half, and from there it was Maradona under pressure the whole way, "
    "past Beardsley, past Butcher, past Fenwick, into the box, around Peter "
    "Shilton, and finished with his left!"
)

STORYTELLER_2022 = (
    "Argentina were on the counter when Molina picked it up and found "
    "MacAllister, who played it to Messi, and Messi moved it on to Álvarez, "
    "whose long ball forward found MacAllister again. He set it up for Di "
    "María in the box, who finished it first time with his left foot."
)

BUDDY_2022_ARGENTINA = (
    "We went on the counter, Molina to MacAllister, MacAllister to Messi, "
    "Messi on to Álvarez, a long ball forward to MacAllister again, and he "
    "set up Di María, who hit it first time with his left foot and scored!"
)

BUDDY_2022_FRANCE = (
    "In under ten seconds it went Molina to MacAllister, MacAllister to Messi "
    "and Messi to Álvarez, whose long ball found MacAllister again, and he "
    "set up Di María in the box to score first time with his left foot."
)

CALLER_2022 = (
    "Molina picked it up and the counter was on, Molina to MacAllister, "
    "MacAllister to Messi, Messi on to Álvarez, a long ball forward to "
    "MacAllister again, and he set up Di María in the box, who, with one "
    "touch, finished it with his left!"
)


@pytest.fixture(scope="module")
def feed():
    return StatsBombEventFeed()


def _hero_facts(feed, match_id, clock):
    """The facts for one hero goal, with the recorded nicknames on them.

    The nicknames are what the references call four of the 2022 players, and
    they are read out of `data/raw/lineups/`, so a narration saying
    "MacAllister" is saying a name the match records. The 1986 goal gains one
    name this way, "Héctor Enrique", and keeps the full "Diego Armando
    Maradona" because that lineups file records no nickname for him.
    """
    moment = next(
        m
        for m in feed.defining_moments(match_id)
        if (m.minute, m.second) == clock
    )
    return facts_from_buildup(
        feed.buildup(match_id, moment), recorded_nicknames(match_id)
    )


@pytest.fixture(scope="module")
def facts_1986(feed):
    """Maradona's second: open play, left foot, eight players, minute 54."""
    return _hero_facts(feed, MATCH_1986, HERO_1986)


@pytest.fixture(scope="module")
def facts_2022(feed):
    """Di María's counter: open play, left foot, five players, minute 35."""
    return _hero_facts(feed, MATCH_2022, HERO_2022)


#: The eight slots, as the framework names them: a goal, a narrator, and the
#: side the listener is on. The Caller and the Storyteller are offered to
#: everybody, so the side is `None` for them; the Buddy is `fans_only` and is
#: checked as the listener's side, which is why each goal has two of them.
REFERENCES = (
    ("1986 Storyteller, neutral", "1986", THE_STORYTELLER, None, STORYTELLER_1986),
    ("1986 Buddy, Argentina", "1986", THE_BUDDY, "Argentina", BUDDY_1986_ARGENTINA),
    ("1986 Buddy, England", "1986", THE_BUDDY, "England", BUDDY_1986_ENGLAND),
    ("1986 Caller", "1986", THE_CALLER, None, CALLER_1986),
    ("2022 Storyteller, neutral", "2022", THE_STORYTELLER, None, STORYTELLER_2022),
    ("2022 Buddy, Argentina", "2022", THE_BUDDY, "Argentina", BUDDY_2022_ARGENTINA),
    ("2022 Buddy, France", "2022", THE_BUDDY, "France", BUDDY_2022_FRANCE),
    ("2022 Caller", "2022", THE_CALLER, None, CALLER_2022),
)


def _facts(goal, facts_1986, facts_2022):
    return facts_1986 if goal == "1986" else facts_2022


class TestTheReferences:
    """The eight references pass the check, word for word.

    Red until Task 9b. Each one is refused today as `untagged`, because the
    check reads a sentence against the fact numbers it cited and a reference
    cites none: the framework in `docs/VOICE.md` is a goal call, and a goal
    call does not read bracketed numbers aloud.
    """

    @pytest.mark.parametrize(
        "slot, goal, narrator, side, text",
        REFERENCES,
        ids=[reference[0] for reference in REFERENCES],
    )
    def test_the_reference_is_grounded(
        self, slot, goal, narrator, side, text, facts_1986, facts_2022
    ):
        result = check(
            text, _facts(goal, facts_1986, facts_2022), narrator, side
        )
        assert result.grounded, f"{slot}: {result.summary}"


class TestAChainTheRecordsDoNotHold:
    """A chain is a recorded pass from the first name to the second.

    "X to Y" is the shortest thing a commentator says and the easiest thing to
    get wrong, because both names are in the passage and the pass between them
    is not. Molina's one pass in the 2022 buildup, fact 1, has Alexis Mac
    Allister as its recipient; nothing in the passage records a pass from
    Molina to Messi.
    """

    def test_a_pass_that_was_never_played_is_refused(self, facts_2022):
        text = (
            "Molina picked it up and the counter was on, Molina to Messi, "
            "Messi on to Álvarez, a long ball forward to MacAllister again, "
            "and he set up Di María in the box, who, with one touch, finished "
            "it with his left!"
        )
        result = check(text, facts_2022, THE_CALLER, None)
        assert not result.grounded, result.summary


class TestANamePartTwoPlayersShare:
    """A short name is grounded when it picks out one player, and not when it
    picks out two.

    This is the price of short names, and the 1986 buildup is where it has to
    be paid: "Peter" is Beardsley, Reid and Shilton, and "Terry" is Butcher and
    Fenwick. A listener hearing either one has not been told who. The full
    names and the surnames stay sayable, which is what the references use.
    """

    def test_a_forename_two_defenders_share_is_refused(self, facts_1986):
        text = (
            "Cuciuffo's recovery started the counter, and Enrique played it "
            "to Maradona just inside his own half, who carried it forward "
            "under pressure past Beardsley, Terry and Fenwick and took it "
            "into the box, where he went around Peter Shilton and scored with "
            "his left foot."
        )
        result = check(text, facts_1986, THE_STORYTELLER, None)
        assert not result.grounded, result.summary

    def test_a_forename_three_players_share_is_refused(self, facts_1986):
        text = (
            "Cuciuffo's recovery started the counter, and Enrique played it "
            "to Maradona just inside his own half, who carried it forward "
            "under pressure past Beardsley, Butcher and Fenwick and took it "
            "into the box, where he went around Peter and scored with his "
            "left foot."
        )
        result = check(text, facts_1986, THE_STORYTELLER, None)
        assert not result.grounded, result.summary


class TestAClaimAboutTheShapeOfTheCarry:
    """"Straight into the box" is a claim about a path, and the path curves.

    Maradona's five carries run [55.2, 55.6] to [54.4, 56.4] to [87.1, 68.6]
    to [97.1, 55.1] to [112.8, 49.4] to [113.4, 49.5]: out towards the
    touchline and back in again, nineteen yards of it across the pitch. The
    records hold the start and the end of every carry, so the shape of the run
    is something they can refuse rather than something they are silent about.
    """

    def test_a_carry_called_straight_is_refused(self, facts_1986):
        text = (
            "Cuciuffo's recovery started the counter, and Enrique played it "
            "to Maradona just inside his own half, who carried it forward "
            "under pressure past Beardsley, Butcher and Fenwick and took it "
            "straight into the box, where he went around Peter Shilton and "
            "scored with his left foot."
        )
        result = check(text, facts_1986, THE_STORYTELLER, None)
        assert not result.grounded, result.summary


class TestTheFirstPersonNeedsTheListenersOwnPlay:
    """The Buddy says "we" over the listener side's recorded actions only.

    The 2022 counter is thirteen records and every one of them is Argentina's.
    So the France fan's Buddy has nothing to say "we" about in this passage,
    and the word would be putting a loyalty over somebody else's move. The same
    sentence is the reference for an Argentina listener.
    """

    def test_we_from_the_conceding_side_is_refused(self, facts_2022):
        text = (
            "We went on the counter, Molina to MacAllister, MacAllister to "
            "Messi and Messi to Álvarez, whose long ball found MacAllister "
            "again, and he set up Di María in the box to score first time "
            "with his left foot."
        )
        result = check(text, facts_2022, THE_BUDDY, "France")
        assert not result.grounded, result.summary


class TestWhereAnExclamationMarkMayStand:
    """"!" goes where the listener would cheer, which is one place or none.

    The ball going in is the only moment in a recap that a listener cheers at,
    so the mark belongs on the last sentence and nowhere earlier. Two voices do
    not get it at all: the Storyteller is a documentary register whoever
    scored, and a Buddy sitting with the side that conceded is not cheering.
    """

    def test_an_exclamation_before_the_last_sentence_is_refused(self, facts_2022):
        text = (
            "Molina picked it up and the counter was on! Molina to "
            "MacAllister, MacAllister to Messi, Messi on to Álvarez, a long "
            "ball forward to MacAllister again, and he set up Di María in the "
            "box, who, with one touch, finished it with his left!"
        )
        result = check(text, facts_2022, THE_CALLER, None)
        assert not result.grounded, result.summary

    def test_an_exclamation_from_the_storyteller_is_refused(self, facts_2022):
        text = (
            "Argentina were on the counter when Molina picked it up and found "
            "MacAllister, who played it to Messi, and Messi moved it on to "
            "Álvarez, whose long ball forward found MacAllister again. He set "
            "it up for Di María in the box, who finished it first time with "
            "his left foot!"
        )
        result = check(text, facts_2022, THE_STORYTELLER, None)
        assert not result.grounded, result.summary

    def test_an_exclamation_from_a_conceding_buddy_is_refused(self, facts_1986):
        text = (
            "Maradona picked it up in his own half, and though Beardsley and "
            "Reid closed him down and Butcher came back at him, he went past "
            "Beardsley, Butcher and Fenwick, got around Shilton in the box, "
            "and scored!"
        )
        result = check(text, facts_1986, THE_BUDDY, "England")
        assert not result.grounded, result.summary


class TestNoClockReachesTheNarration:
    """No narration carries a clock, in digits or in words.

    A clock was grounded and is now refused, which is a change in the standard
    rather than in the data: the fact's minute and second are still there to be
    pointed at. A goal call does not say when it happened, the header already
    carries the minute, and a colon between two numbers is read aloud as a
    colon between two numbers.
    """

    @pytest.mark.parametrize(
        "clock", ["at 54:02", "in minute 54", "two seconds into the 55th minute"]
    )
    def test_a_clock_is_refused(self, clock, facts_1986):
        text = (
            f"It started with a Cuciuffo recovery {clock}, Enrique to "
            "Maradona just inside his own half, and from there it was "
            "Maradona under pressure the whole way, past Beardsley, past "
            "Butcher, past Fenwick, into the box, around Peter Shilton, and "
            "finished with his left!"
        )
        result = check(text, facts_1986, THE_CALLER, None)
        assert not result.grounded, result.summary
