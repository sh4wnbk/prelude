"""Contract for the orchestrator: what is said before the narration starts.

This file is a contract, not a component. It declares the data shapes, the
fixed wording table and the interface an implementer satisfies, and it decides
nothing: every function in it raises. The one piece of code here is
`ScoringMoment.__post_init__`, which refuses a score that cannot have come
from one side scoring; that is the shape holding itself together rather than a
decision about what to say. `docs/bob_brief.md` carries the briefs, as Task 4
for the orchestrator and Task 5 for the header, and IBM Bob builds the module
against them.

**What the orchestrator is for.** The narration says only what the play data
proves, which leaves it unable to say anything to the person listening. It
cannot greet them, it cannot know which side they are on, and it stops dead on
the goal because the stadium takes over. Everything addressed to the fan
therefore happens before the narration, in one line, and that line is this
module's whole output.

It is built from what the app knows without a model: when kickoff was, who
scored, what the score was before and after, and which side the listener is
on. None of that comes from the event data a narration is checked against, so
none of it carries the "Verified from play data" label, and nothing here may
be voiced as though it did. The header is not narration. `app/grounding.py`
never sees it and would refuse it if it did, because a line spoken to the fan
is exactly what the ending rule in `docs/VOICE.md` keeps out.

**The header is game focused, and it is the same line for every listener.** It
says what the goal did to the score rather than how the fan should feel about
it: a transition read out of the score before and the score after, then the
score itself, then the tail. Allegiance no longer reaches it at all; what
allegiance picks is the persona. The wording is in `HEADER_WORDING` and
`docs/VOICE.md` carries it.

**It is sport agnostic on purpose.** The phase of a game is a share of
regulation time rather than a count of minutes, so a 60 minute game and a 90
minute one are read the same way. Nothing in this module names football, and
`tests/test_orchestrator.py` proves it with a sport that does not exist.

Standard library only, like the rest of `app/`.
"""

from dataclasses import dataclass
from datetime import datetime, time
from typing import Mapping, Protocol, runtime_checkable

#: Kickoff at or after this local time makes it an evening match, and the
#: greeting becomes "tonight". Configuration rather than a rule: it is a
#: judgement about when evening starts, it will be argued about, and 17:00 is
#: where it starts. Task 6 adds a committed config file and this belongs in it.
EVENING_CUTOFF: time = time(17, 0)

#: Where the phase boundaries sit, as shares of regulation time. Early is the
#: first third and late is the final quarter, which leaves the middle as
#: whatever is between them.
EARLY_UNTIL: float = 1 / 3
LATE_FROM: float = 3 / 4

#: Which side a listener is on. `NEUTRAL` is a real answer and not a missing
#: one: "Just here for the game" is an option on the card in Task 7.
TEAM_A = "team_a"
TEAM_B = "team_b"
NEUTRAL = "neutral"

#: The phase of the game a moment happened in.
EARLY = "early"
MIDDLE = "middle"
LATE = "late"

#: Where the listener's side stands once the moment has happened.
AHEAD = "ahead"
LEVEL = "level"
BEHIND = "behind"

#: What the moment was, from the listener's point of view. A neutral listener
#: has neither, so `outcome` raises for one rather than inventing an answer.
#: The header does not read these: it is the same line for every listener.
SCORED = "scored"
CONCEDED = "conceded"

#: The greeting word, which is the whole of what the time of day decides.
TODAY = "today"
TONIGHT = "tonight"

#: The personas, by the id Task 6's config file will use. Declared here
#: because the orchestrator picks the default one, and named rather than
#: described: the descriptions, the writing styles and the voices are Task 6.
CALLER = "caller"
STORYTELLER = "storyteller"
BUDDY = "buddy"

#: What the moment did to the score, **from the scoring side's point of
#: view**, read out of the score before it and the score after it and nothing
#: else.
#:
#: **No transition depends on what happened earlier in the match.** There is
#: no "again" and no "back in front", because the two scores this is built
#: from do not say whether this side has led before. A header claiming a goal
#: that nothing in front of it records is the mistake the old late-scored cell
#: made, and it was wrong for England's only goal in 1986.
#:
#: The five are exhaustive over a score that rose for one side only, which is
#: the only score `ScoringMoment` accepts: the scoring side was level, behind
#: or ahead before, and a side that was ahead and scored is further ahead.
TAKE_LEAD = "take_lead"
OVERTAKE = "overtake"
EXTEND = "extend"
CLOSE_GAP = "close_gap"
DRAW_LEVEL = "draw_level"

#: The five, for a caller that wants to say "every transition" once.
TRANSITIONS: tuple[str, ...] = (
    TAKE_LEAD,
    OVERTAKE,
    EXTEND,
    CLOSE_GAP,
    DRAW_LEVEL,
)

#: The first sentence of the header, by transition. `{scorer}` is the scoring
#: team's name as the event names it.
#:
#: **This is the starting wording and Shawn writes the final wording.** The
#: shape is what matters here: a fixed table, looked up, with nothing
#: generated and nothing a model chooses, so changing a word is a one line
#: edit to this file.
#:
#: Taking the lead and overtaking share a sentence, because "take the lead" is
#: true of both and the difference between them is history the listener
#: already has. They are separate transitions anyway, so a wording that wants
#: to tell them apart can, without the classification being rewritten.
#:
#: Nothing here is sport specific, and nothing here says "goal".
HEADER_WORDING: Mapping[str, str] = {
    TAKE_LEAD: "{scorer} take the lead.",
    OVERTAKE: "{scorer} take the lead.",
    EXTEND: "{scorer} extend the lead.",
    CLOSE_GAP: "{scorer} close the gap.",
    DRAW_LEVEL: "{scorer} draw level.",
}

#: The score after the moment, said as the second sentence. Both teams, in the
#: order the event names them, so a listener with no side reads it the same way
#: as a listener with one.
SCORE_LINE = "{team_a} {score_a}, {team_b} {score_b}."

#: What every header ends on, whoever is listening. It is not the neutral case
#: of anything: there is one header, and this is the sentence it ends on.
HEADER_TAIL = "Here's how it happened."


@dataclass(frozen=True)
class Event:
    """The fixture, as the app knows it before a ball is kicked.

    `kickoff` is local to the venue, because the greeting is about the
    listener's evening and not about UTC. `sport` is carried but never
    branched on: it is here so a header can be logged with what it was for,
    not so the rules can differ by sport.
    """

    kickoff: datetime
    team_a: str
    team_b: str
    sport: str


@dataclass(frozen=True)
class ScoringMoment:
    """One goal, and the state of the game once it had happened.

    `scoring_side` is `TEAM_A` or `TEAM_B`, never `NEUTRAL`: somebody scored.

    `score_a` and `score_b` are the score **after** the moment, which is what
    the listener is looking at while they listen. `score_before_a` and
    `score_before_b` are the score it was before.

    **Both are carried, and the before is never derived from the after.**
    Subtracting one from the scoring side would be reading football into a
    shape that is meant to outlive it: a score can move by any number of
    points, and a sport that scores three at a time would get a header built
    from a score that never existed. The caller knows both numbers, so the
    caller passes both.

    `__post_init__` refuses a pair that cannot have come from one side
    scoring: the scoring side's score has to have risen, by more than zero,
    and the other side's score has to be the number it was. That catches the
    two mistakes this shape invites, a before and after swapped and a before
    copied from another moment, at the point they are made rather than in a
    header that reads oddly.

    `minute` and `second` are the game clock, and `regulation_minutes` is how
    long the game is meant to last: 90 for football, 60 for a sport that plays
    60. The phase is the ratio of the two, so nothing here needs to know which
    sport it is. A moment past regulation, which both 2022 extra time goals
    are, gives a ratio above 1 and is late, as it should be.
    """

    scoring_side: str
    minute: int
    second: int
    score_before_a: int
    score_before_b: int
    score_a: int
    score_b: int
    regulation_minutes: int

    def __post_init__(self) -> None:
        """Refuse a score that one side scoring cannot explain."""
        if self.scoring_side == TEAM_A:
            before, after = self.score_before_a, self.score_a
            still, was = self.score_b, self.score_before_b
        elif self.scoring_side == TEAM_B:
            before, after = self.score_before_b, self.score_b
            still, was = self.score_a, self.score_before_a
        else:
            raise ValueError(
                f"scoring_side is {self.scoring_side!r}; somebody scored, so "
                f"it is {TEAM_A!r} or {TEAM_B!r}"
            )
        if after <= before:
            raise ValueError(
                f"{self.scoring_side} scored, so its score has to have risen: "
                f"it is {before} before and {after} after"
            )
        if still != was:
            raise ValueError(
                f"{self.scoring_side} scored, so the other side's score has "
                f"to be the number it was: it is {was} before and {still} "
                "after"
            )


@dataclass(frozen=True)
class Listener:
    """Who is listening, which is the only thing the fan tells the app.

    `allegiance` is `TEAM_A`, `TEAM_B` or `NEUTRAL`. `name` is optional and
    stays on the phone: Task 7 adds it to the header after the narration has
    been generated, and it is never sent to a model or a server.
    """

    allegiance: str
    name: str | None = None


@dataclass(frozen=True)
class Opening:
    """What the orchestrator produces: the line before the narration.

    `greeting` is `TODAY` or `TONIGHT`, the word alone, so a caller can put it
    in a sentence of its own choosing. `header` is the line as it is shown,
    wording, score and tail already joined, and it is the same line for every
    listener. `persona` is the id of the persona to narrate in unless the
    listener has chosen another, and it is the one thing in here that the
    listener's allegiance decides.
    """

    greeting: str
    header: str
    persona: str


def greeting_word(event: Event) -> str:
    """`TONIGHT` when kickoff is at or after `EVENING_CUTOFF`, else `TODAY`.

    At the cutoff counts as evening: a 17:00 kickoff is tonight.
    """
    raise NotImplementedError("the orchestrator is not built yet")


def phase(moment: ScoringMoment) -> str:
    """`EARLY`, `MIDDLE` or `LATE`, as a share of regulation time.

    Early is the first third and late is the final quarter, so the boundaries
    are `EARLY_UNTIL` and `LATE_FROM` and nothing is counted in minutes. A
    moment exactly on a boundary belongs to the later phase, so that the first
    third is the first third and not a hair more.
    """
    raise NotImplementedError("the orchestrator is not built yet")


def score_state(moment: ScoringMoment, listener: Listener) -> str:
    """`AHEAD`, `LEVEL` or `BEHIND` for the listener's side, after the moment.

    A neutral listener has no side, so there is no state to report and this
    raises `ValueError` rather than inventing one.
    """
    raise NotImplementedError("the orchestrator is not built yet")


def outcome(moment: ScoringMoment, listener: Listener) -> str:
    """`SCORED` or `CONCEDED`, from the listener's point of view.

    Raises `ValueError` for a neutral listener, who did neither.
    """
    raise NotImplementedError("the orchestrator is not built yet")


def transition(moment: ScoringMoment) -> str:
    """What the moment did to the score, from the scoring side's point of view.

    One of `TRANSITIONS`, read out of `moment`'s two scores and nothing else:
    level to ahead is `TAKE_LEAD`, behind to ahead is `OVERTAKE`, ahead to
    further ahead is `EXTEND`, behind to still behind is `CLOSE_GAP`, and
    behind to level is `DRAW_LEVEL`. Nothing here looks at earlier moments,
    because nothing it is given records one.
    """
    raise NotImplementedError("the game focused header is not built yet")


def header(event: Event, moment: ScoringMoment) -> str:
    """The header line: the transition's wording, the score, then the tail.

    `HEADER_WORDING[transition(moment)]` with `{scorer}` filled in from the
    side that scored, then `SCORE_LINE` with both team names and the score
    after the moment, then `HEADER_TAIL`, joined by single spaces.

    It takes no listener. The header is the same line for everybody: it says
    what happened to the score, which is not a different fact for a fan of
    either side. What a listener's allegiance picks is the persona, which is
    `default_persona`.
    """
    raise NotImplementedError("the game focused header is not built yet")


def default_persona(listener: Listener) -> str:
    """`BUDDY` for a fan, `STORYTELLER` for a neutral listener.

    A partisan voice is for somebody who has a side. Saying "late one for your side"
    in the Buddy's voice to a neutral listener would be telling them they
    support a team they did not choose.
    """
    raise NotImplementedError("the orchestrator is not built yet")


@runtime_checkable
class Orchestrator(Protocol):
    """Turns an event, a moment and a listener into the line before narration."""

    def opening(
        self, event: Event, moment: ScoringMoment, listener: Listener
    ) -> Opening:
        """The greeting word, the header line and the default persona."""
        ...
