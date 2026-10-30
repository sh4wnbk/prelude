"""How a narration is delivered: one row per persona per situation.

A persona is a sound, and this is the sound. `app/personas.py` holds which
voice says a narration; this holds how that voice is set when it says it, and
it is keyed by persona **and situation**, because the same voice telling a fan
their side scored and telling them it conceded is not the same delivery.

**The situation comes from the orchestrator and never from a model.**
`situation` reads it off the moment and the listener: `SCORED` or `CONCEDED`
from `outcome` in `app/orchestrator.py`, which compares the scoring side to
the listener's allegiance, and `NEUTRAL` for a listener who has no side. No
model is asked, nothing is inferred from the narration text, and nothing here
reads a word of it. A delivery chosen from the text would be a model deciding
how a fan should feel about a goal, off the same text the grounding check is
busy holding to the records.

**What a row may hold is what the service honours**, which
`scripts/tts_probe.py` measured and `docs/VOICE.md` records. It is narrower
than the plan this task began with, and each narrowing is a rule below:

| Field | What it is | Who may hold one |
| ----- | ---------- | ---------------- |
| `rate` | `rate_percentage`, a signed percentage | every persona |
| `pitch` | `pitch_percentage`, a percentage at or above zero | every persona |
| `sentence_break` | the pause between sentences, in milliseconds | the Caller |
| `goal_break` | the pause before the goal sentence, in milliseconds | the Caller |

**Pitch cannot go down.** `pitch_percentage` of +20 moves all three voices and
-20 moves none of them, measured twice. So a negative pitch is refused here
rather than sent and ignored: a value that looks set and does nothing is worse
than no value, because it reads as a decision somebody made. A persona meant
to sit lower than another gets there by leaving its own pitch alone while the
others rise.

**Only the Caller can pause.** `<break>` works on `en-AU_HeidiNatural` and on
neither of the other two voices, so the two break fields are the Caller's and
a break on another persona is refused. `Persona.breaks_work` is where that
fact lives, beside the voice it is about.

**The two parameters are per request.** They go in the address rather than in
the text, which is why they cost no billable characters and also why one
narration gets one rate and one pitch. A rate that changed at the goal would
be two requests and two files.

**The values are Shawn's, set by ear**, and `prosody_confirmed` is true on all
three personas. The shape, the rules and the tests were written first and the
numbers went in afterwards, which is what made filling the table in an edit to
this file and a run of the suite: every bound below was already enforced, so a
value the service would ignore could not have been written down.

What the numbers say, in a sentence each. The Caller is quicker except when
the other side scored, because hurrying a fan through a goal against them is
its version of being cheerful about it. The Storyteller is the voice's own
rate in all three situations, which is what makes it the one the other two are
set against. The Mate lifts for your goal and comes back down for theirs,
going up rather than down because down is not available.

**Eight rows and not nine.** The Mate is `fans_only`: a partisan voice told to
a listener with no side would be telling them they support a team they did not
choose, so there is no neutral Mate row to write. `validate` requires exactly
the rows that can exist.

Standard library only, like the rest of `app/`.
"""

from dataclasses import dataclass
from typing import Mapping

from app.orchestrator import outcome
from app.orchestrator_contract import (
    CALLER,
    CONCEDED,
    MATE,
    NEUTRAL,
    SCORED,
    STORYTELLER,
    Listener,
    ScoringMoment,
)
from app.personas import BY_ID, PERSONAS, persona

#: The three situations a delivery is chosen for. `SCORED` and `CONCEDED` are
#: the orchestrator's own words for what the moment was from the listener's
#: point of view; `NEUTRAL` is its word for a listener with no side, and it is
#: a real answer rather than a missing one.
SITUATIONS: tuple[str, ...] = (SCORED, CONCEDED, NEUTRAL)

#: What `rate_percentage` may be set to. IBM's documentation says values below
#: -50 begin to cost pronunciation, and that above 100 sounds no different
#: from 100. Neither bound is a judgement about this app; both are the
#: service's.
RATE_FLOOR = -50
RATE_CEILING = 100

#: What `pitch_percentage` may be set to. The floor is zero because the probe
#: found a lowered pitch ignored, not because a lower voice is unwanted.
PITCH_FLOOR = 0
PITCH_CEILING = 100

#: The Caller's rate has a ceiling below `RATE_CEILING`, because comprehension
#: comes first: the names and the clock are the whole of what a narration
#: carries, and a listener who misses them has been told nothing. The number
#: is not here, because it is words per minute measured off real audio and
#: nothing has measured it. `docs/VOICE.md` records that it is owed.
CALLER_RATE_CEILING: int | None = None


class DeliveryError(ValueError):
    """A delivery value the service would ignore, or a table with a hole in it.

    Raised at import, so a table edited wrongly fails before anything speaks
    rather than producing audio that quietly ignores half of it.
    """


@dataclass(frozen=True)
class Delivery:
    """One persona's delivery in one situation.

    `rate` and `pitch` are percentages as integers, because they are numbers
    the request carries as numbers and because a bound is a comparison rather
    than a string match. `None` means "leave the voice alone", which is not the
    same as zero: zero is a decision to send the parameter at its neutral
    value, and `None` is the parameter not being sent at all.

    `sentence_break` and `goal_break` are milliseconds. They are separate
    fields rather than one with a multiplier so that the pause before the goal
    can be read against the pause between sentences at a glance.

    `__post_init__` refuses what the service would ignore. The bounds are the
    service's, and the pitch floor is the probe's: a lowered pitch came back
    byte for byte identical to no pitch at all.
    """

    rate: int | None = None
    pitch: int | None = None
    sentence_break: int | None = None
    goal_break: int | None = None

    def __post_init__(self) -> None:
        if self.rate is not None and not RATE_FLOOR <= self.rate <= RATE_CEILING:
            raise DeliveryError(
                "rate is {}; rate_percentage runs {} to {}".format(
                    self.rate, RATE_FLOOR, RATE_CEILING
                )
            )
        if self.pitch is not None and not (
            PITCH_FLOOR <= self.pitch <= PITCH_CEILING
        ):
            raise DeliveryError(
                "pitch is {}; pitch_percentage runs {} to {} here, because "
                "scripts/tts_probe.py found a lowered pitch ignored on all "
                "three voices rather than applied".format(
                    self.pitch, PITCH_FLOOR, PITCH_CEILING
                )
            )
        for name, pause in (
            ("sentence_break", self.sentence_break),
            ("goal_break", self.goal_break),
        ):
            if pause is not None and pause <= 0:
                raise DeliveryError(
                    "{} is {}; a pause is a positive number of milliseconds, "
                    "and no pause is None".format(name, pause)
                )
        if (
            self.sentence_break is not None
            and self.goal_break is not None
            and self.goal_break < self.sentence_break
        ):
            raise DeliveryError(
                "goal_break is {} and sentence_break is {}; the pause before "
                "the goal is the longer one".format(
                    self.goal_break, self.sentence_break
                )
            )

    @property
    def is_set(self) -> bool:
        """Whether anything in this row has been decided yet."""
        return any(
            value is not None
            for value in (
                self.rate, self.pitch, self.sentence_break, self.goal_break
            )
        )


#: The table. Keyed by `(persona id, situation)`, eight rows, every value a
#: placeholder for Shawn to set by ear.
#:
#: The comment on each row is what the row is for, so that the person filling
#: it in is reading the intent beside the numbers rather than in another file.
DELIVERY: Mapping[tuple[str, str], Delivery] = {
    # Quick, and quick is the one thing it may not be too much of: a rate far
    # above the Storyteller's costs the listener the names and the clock. +10
    # is what that came to by ear, and it drops to the voice's own rate when
    # the other side scored: hurrying a fan through a goal against them is the
    # Caller's version of being cheerful about it.
    #
    # It is the only persona with pauses, because `<break>` moves its voice
    # and neither of the other two. They are short on purpose. The probe
    # measured a requested 600 ms arriving as 1.36s on this voice, so a
    # request lands at roughly twice what it asks for, and 200 and 400 are
    # about 450 ms between sentences and 900 ms before the goal.
    (CALLER, SCORED): Delivery(rate=10, sentence_break=200, goal_break=400),
    (CALLER, CONCEDED): Delivery(rate=0, sentence_break=200, goal_break=400),
    (CALLER, NEUTRAL): Delivery(rate=10, sentence_break=200, goal_break=400),
    # The plainest of the three and the one the others are set against, so its
    # rate is the voice's own in every situation and nothing else is set. Its
    # neutral row is the default a listener with no side hears, because
    # `default_persona` in `app/orchestrator.py` returns the Storyteller.
    #
    # Three rows holding the same values is not a table that wants collapsing.
    # The Storyteller sounding the same whoever scored is a decision about
    # this persona, and a row per situation is what lets that decision change
    # for one situation later without the shape changing.
    (STORYTELLER, SCORED): Delivery(rate=0),
    (STORYTELLER, CONCEDED): Delivery(rate=0),
    (STORYTELLER, NEUTRAL): Delivery(rate=0),
    # Warm, from the next seat, and **never cheerful when the other side
    # scored**: a voice that brightens over a goal against your team is a
    # voice that was not listening with you. Up and quicker for your goal,
    # slower and back to its own pitch for theirs, which is the rule
    # `_validate_the_mate_is_never_cheerful` enforces rather than describes:
    # the conceded row carries less of both.
    #
    # The pitch goes up for the goal rather than down for the concession
    # because down is not available. `pitch_percentage` below zero is ignored
    # by the service, so 0 is the floor and the only way to be lower than
    # something is to let the other row rise.
    (MATE, SCORED): Delivery(rate=10, pitch=10),
    (MATE, CONCEDED): Delivery(rate=-10, pitch=0),
    # No (MATE, NEUTRAL): the Mate is fans only.
}


def rows_that_should_exist() -> tuple[tuple[str, str], ...]:
    """Every `(persona, situation)` pair that can exist, in table order.

    A `fans_only` persona has no neutral row, because a partisan voice told to
    a listener with no side would be telling them they support a team they did
    not choose. That is `available` in `app/personas.py` read from the other
    end.
    """
    return tuple(
        (one.id, where)
        for one in PERSONAS
        for where in SITUATIONS
        if not (one.fans_only and where == NEUTRAL)
    )


def validate(table: Mapping[tuple[str, str], Delivery]) -> None:
    """Raise `DeliveryError` unless `table` is a delivery table that can ship.

    Called at import over `DELIVERY`, so a bad edit fails on the import rather
    than in audio nobody is listening to closely. It is a function taking a
    table rather than a check over the module's own global, because the tests
    have to be able to hand it a wrong one.
    """
    expected = set(rows_that_should_exist())
    actual = set(table)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing or extra:
        raise DeliveryError(
            "the delivery table has {} missing row(s) {} and {} row(s) that "
            "cannot exist {}".format(len(missing), missing, len(extra), extra)
        )

    for (persona_id, where), row in table.items():
        one = BY_ID[persona_id]
        if not one.breaks_work and (
            row.sentence_break is not None or row.goal_break is not None
        ):
            raise DeliveryError(
                "{} in {} carries a break, and <break> does nothing on {}: "
                "scripts/tts_probe.py measured audio byte for byte identical "
                "to the same request without it".format(
                    persona_id, where, one.voice
                )
            )
        if (
            persona_id == CALLER
            and CALLER_RATE_CEILING is not None
            and row.rate is not None
            and row.rate > CALLER_RATE_CEILING
        ):
            raise DeliveryError(
                "the Caller's rate in {} is {}, above the ceiling of {}; "
                "comprehension comes first and the names and the clock are "
                "the whole of what a narration carries".format(
                    where, row.rate, CALLER_RATE_CEILING
                )
            )

    _validate_the_mate_is_never_cheerful(table)


def _validate_the_mate_is_never_cheerful(
    table: Mapping[tuple[str, str], Delivery]
) -> None:
    """The Mate's conceded delivery is no brighter and no quicker than its own.

    Brighter and quicker is what cheerful is made of in the only two controls
    there are, so the rule is readable as a comparison: the conceded row may
    not raise the pitch above the scored row's, and may not raise the rate
    above it either.

    It is compared against the Mate's own scored row rather than against a
    fixed number. That was the only thing sayable while the table was empty,
    and it is still the right shape now that it is not: the rule is about one
    row relative to the other, so it holds for whatever pair of numbers gets
    picked next. The shipped rows pass it because the conceded one is slower
    and no brighter, which is the reason it was written rather than for want
    of values to compare
    (`tests/test_delivery.py::TestTheValuesAreShawnsAndTheTableSaysSo::test_the_shipped_table_satisfies_the_mate_rule`).

    A row with nothing set is not refused. An unset row has not been made
    cheerful, so there is nothing to compare and nothing to object to.
    """
    scored = table.get((MATE, SCORED))
    conceded = table.get((MATE, CONCEDED))
    if scored is None or conceded is None:
        return
    for field, label in (("pitch", "brighter"), ("rate", "quicker")):
        over_the_top = getattr(conceded, field)
        when_scoring = getattr(scored, field)
        if (
            over_the_top is not None
            and when_scoring is not None
            and over_the_top > when_scoring
        ):
            raise DeliveryError(
                "the Mate's {} is {} when the other side scored and {} when "
                "its own side did, which is {} over a goal against the "
                "listener's team".format(
                    field, over_the_top, when_scoring, label
                )
            )


def situation(moment: ScoringMoment, listener: Listener) -> str:
    """Which situation this moment is, for this listener.

    `NEUTRAL` for a listener with no side, and otherwise the orchestrator's
    own `outcome`: `SCORED` when the scoring side is the listener's and
    `CONCEDED` when it is not. Read off two numbers and an allegiance, with no
    model and no narration text anywhere near it.
    """
    if listener.allegiance == NEUTRAL:
        return NEUTRAL
    return outcome(moment, listener)


def delivery(persona_id: str, where: str) -> Delivery:
    """The delivery for this persona in this situation.

    A `KeyError` here is a caller holding a pair that cannot exist, which is
    either a persona id read from somewhere stale or a `fans_only` persona
    asked for its neutral row. Both are bugs rather than things to recover
    from, so the message names what went wrong instead of returning a default
    delivery that would quietly sound like nothing was chosen.
    """
    one = persona(persona_id)
    if where not in SITUATIONS:
        raise KeyError(
            "{!r} is not a situation; the three are {}".format(
                where, ", ".join(SITUATIONS)
            )
        )
    try:
        return DELIVERY[(one.id, where)]
    except KeyError:
        raise KeyError(
            "{} has no {} delivery, because it is fans only and a listener "
            "with no side has no side for it to be partisan about".format(
                one.id, where
            )
        ) from None


validate(DELIVERY)
