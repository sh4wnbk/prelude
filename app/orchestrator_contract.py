"""Contract for the orchestrator: what is said before the narration starts.

This file is a contract, not a component. It declares the data shapes, the
fixed wording table and the interface an implementer satisfies, and it
contains no behaviour: nothing here decides anything, and every function
raises. `docs/bob_brief.md` carries the brief as Task 4, and IBM Bob builds
the module against it.

**What the orchestrator is for.** The narration says only what the play data
proves, which leaves it unable to say anything to the person listening. It
cannot greet them, it cannot know which side they are on, and it stops dead on
the goal because the stadium takes over. Everything addressed to the fan
therefore happens before the narration, in one line, and that line is this
module's whole output.

It is built from what the app knows without a model: when kickoff was, who
scored, how far into the match it happened, and which side the listener is on.
None of that comes from the event data a narration is checked against, so none
of it carries the "Verified from play data" label, and nothing here may be
voiced as though it did. The header is not narration. `app/grounding.py` never
sees it and would refuse it if it did, because a line spoken to the fan is
exactly what the ending rule in `docs/VOICE.md` keeps out.

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
#: has neither, which is why the header table has a row of its own for them.
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
MATE = "mate"

#: What a fan's header ends with, and what a neutral listener's header is.
FAN_TAIL = "Here's how it happened."
NEUTRAL_TAIL = "Here's the buildup."

#: The prefix for a fan's header, by what the moment was and the phase it
#: happened in. The empty string means no prefix, leaving the tail alone.
#:
#: **This is the starting wording and not the final wording.** Shawn writes
#: that, and `docs/VOICE.md` carries it. The shape is what matters here: a
#: fixed table, looked up, with nothing generated and nothing a model chooses.
#:
#: The late conceded cell is empty on purpose. "There's still time" is a
#: kindness early and a lie late, and a phone telling someone there is still
#: time when there is not is worse than a phone saying nothing.
HEADER_PREFIXES: Mapping[tuple[str, str], str] = {
    (SCORED, EARLY): "Great start.",
    (SCORED, MIDDLE): "Good news.",
    (SCORED, LATE): "Your side again.",
    (CONCEDED, EARLY): "Still early.",
    (CONCEDED, MIDDLE): "There's still time.",
    (CONCEDED, LATE): "",
}


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
    the listener is looking at while they listen. A score before it would make
    every header one goal out of date.

    `minute` and `second` are the game clock, and `regulation_minutes` is how
    long the game is meant to last: 90 for football, 60 for a sport that plays
    60. The phase is the ratio of the two, so nothing here needs to know which
    sport it is. A moment past regulation, which both 2022 extra time goals
    are, gives a ratio above 1 and is late, as it should be.
    """

    scoring_side: str
    minute: int
    second: int
    score_a: int
    score_b: int
    regulation_minutes: int


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
    prefix and tail already joined. `persona` is the id of the persona to
    narrate in unless the listener has chosen another.
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


def header(moment: ScoringMoment, listener: Listener) -> str:
    """The header line: a prefix from `HEADER_PREFIXES`, then the tail.

    A neutral listener gets `NEUTRAL_TAIL` and no prefix. A fan gets the
    prefix for their outcome and phase, then `FAN_TAIL`, with the two joined
    by a single space and no leading space when the prefix is empty.
    """
    raise NotImplementedError("the orchestrator is not built yet")


def default_persona(listener: Listener) -> str:
    """`MATE` for a fan, `STORYTELLER` for a neutral listener.

    A partisan voice is for somebody who has a side. Saying "your side again"
    in the Mate's voice to a neutral listener would be telling them they
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
