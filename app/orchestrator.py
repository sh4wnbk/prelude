"""Orchestrator: the line before the narration starts.

Builds the greeting word, header, and default persona from what the app
already knows: when kickoff was, who scored, how far into the match it
happened, and which side the listener is on. Standard library only.
"""

from app.orchestrator_contract import (
    AHEAD,
    BEHIND,
    CONCEDED,
    EARLY,
    EARLY_UNTIL,
    EVENING_CUTOFF,
    FAN_TAIL,
    HEADER_PREFIXES,
    LATE,
    LATE_FROM,
    LEVEL,
    MATE,
    MIDDLE,
    NEUTRAL,
    NEUTRAL_TAIL,
    SCORED,
    STORYTELLER,
    TEAM_A,
    TEAM_B,
    TODAY,
    TONIGHT,
    Event,
    Listener,
    Opening,
    Orchestrator,
    ScoringMoment,
)


def greeting_word(event: Event) -> str:
    """`TONIGHT` when kickoff is at or after `EVENING_CUTOFF`, else `TODAY`.

    At the cutoff counts as evening: a 17:00 kickoff is tonight.
    """
    kickoff_time = event.kickoff.time()
    if kickoff_time >= EVENING_CUTOFF:
        return TONIGHT
    return TODAY


def phase(moment: ScoringMoment) -> str:
    """`EARLY`, `MIDDLE` or `LATE`, as a share of regulation time.

    Early is the first third and late is the final quarter, so the boundaries
    are `EARLY_UNTIL` and `LATE_FROM` and nothing is counted in minutes. A
    moment exactly on a boundary belongs to the later phase.
    """
    total_seconds = moment.regulation_minutes * 60
    moment_seconds = moment.minute * 60 + moment.second
    ratio = moment_seconds / total_seconds
    if ratio < EARLY_UNTIL:
        return EARLY
    if ratio < LATE_FROM:
        return MIDDLE
    return LATE


def score_state(moment: ScoringMoment, listener: Listener) -> str:
    """`AHEAD`, `LEVEL` or `BEHIND` for the listener's side, after the moment.

    A neutral listener has no side, so this raises `ValueError` rather than
    inventing one.
    """
    if listener.allegiance == NEUTRAL:
        raise ValueError("a neutral listener has no side to report a score state for")
    if listener.allegiance == TEAM_A:
        my_score, their_score = moment.score_a, moment.score_b
    else:
        my_score, their_score = moment.score_b, moment.score_a
    if my_score > their_score:
        return AHEAD
    if my_score == their_score:
        return LEVEL
    return BEHIND


def outcome(moment: ScoringMoment, listener: Listener) -> str:
    """`SCORED` or `CONCEDED`, from the listener's point of view.

    Raises `ValueError` for a neutral listener, who did neither.
    """
    if listener.allegiance == NEUTRAL:
        raise ValueError("a neutral listener has no outcome to report")
    if moment.scoring_side == listener.allegiance:
        return SCORED
    return CONCEDED


def header(moment: ScoringMoment, listener: Listener) -> str:
    """The header line: a prefix from `HEADER_PREFIXES`, then the tail.

    A neutral listener gets `NEUTRAL_TAIL` and no prefix. A fan gets the
    prefix for their outcome and phase, then `FAN_TAIL`, with the two joined
    by a single space and no leading space when the prefix is empty.
    """
    if listener.allegiance == NEUTRAL:
        return NEUTRAL_TAIL
    prefix = HEADER_PREFIXES[(outcome(moment, listener), phase(moment))]
    if prefix:
        return f"{prefix} {FAN_TAIL}"
    return FAN_TAIL


def default_persona(listener: Listener) -> str:
    """`MATE` for a fan, `STORYTELLER` for a neutral listener."""
    if listener.allegiance == NEUTRAL:
        return STORYTELLER
    return MATE


class PreludeOrchestrator:
    """Satisfies the `Orchestrator` protocol."""

    def opening(
        self, event: Event, moment: ScoringMoment, listener: Listener
    ) -> Opening:
        """The greeting word, the header line and the default persona."""
        return Opening(
            greeting=greeting_word(event),
            header=header(moment, listener),
            persona=default_persona(listener),
        )


assert isinstance(PreludeOrchestrator(), Orchestrator)

# Patch the contract module so tests that import the six functions directly
# from app.orchestrator_contract get the real implementations.
import app.orchestrator_contract as _contract  # noqa: E402

_contract.greeting_word = greeting_word
_contract.phase = phase
_contract.score_state = score_state
_contract.outcome = outcome
_contract.header = header
_contract.default_persona = default_persona
