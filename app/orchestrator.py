"""Orchestrator: the line before the narration starts.

Builds the greeting word, header, and default persona from what the app
already knows: when kickoff was, who scored, how far into the match it
happened, and which side the listener is on. Standard library only.
"""

from app.orchestrator_contract import (
    AHEAD,
    BEHIND,
    CLOSE_GAP,
    CONCEDED,
    DRAW_LEVEL,
    EARLY,
    EARLY_UNTIL,
    EVENING_CUTOFF,
    EXTEND,
    HEADER_TAIL,
    HEADER_WORDING,
    LATE,
    LATE_FROM,
    LEVEL,
    MATE,
    MIDDLE,
    NEUTRAL,
    OVERTAKE,
    SCORE_LINE,
    SCORED,
    STORYTELLER,
    TAKE_LEAD,
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


def transition(moment: ScoringMoment) -> str:
    """What the moment did to the score, from the scoring side's point of view.

    One of `TRANSITIONS`, read out of the score before and after and nothing
    else. The scoring side was level, behind or ahead before, and the five
    cases are exhaustive.
    """
    if moment.scoring_side == TEAM_A:
        before_scorer = moment.score_before_a
        after_scorer = moment.score_a
        before_other = moment.score_before_b
        after_other = moment.score_b
    else:
        before_scorer = moment.score_before_b
        after_scorer = moment.score_b
        before_other = moment.score_before_a
        after_other = moment.score_a
    if before_scorer > before_other:
        return EXTEND
    if before_scorer == before_other:
        return TAKE_LEAD
    # scoring side was behind
    if after_scorer > after_other:
        return OVERTAKE
    if after_scorer == after_other:
        return DRAW_LEVEL
    return CLOSE_GAP


def header(event: Event, moment: ScoringMoment) -> str:
    """The header line: the transition's wording, the score, then the tail.

    `HEADER_WORDING[transition(moment)]` with `{scorer}` filled in from the
    team that scored, then `SCORE_LINE` with both teams and the score after
    the moment, then `HEADER_TAIL`, joined by single spaces.
    """
    scorer = event.team_a if moment.scoring_side == TEAM_A else event.team_b
    wording = HEADER_WORDING[transition(moment)].format(scorer=scorer)
    score = SCORE_LINE.format(
        team_a=event.team_a,
        score_a=moment.score_a,
        team_b=event.team_b,
        score_b=moment.score_b,
    )
    return f"{wording} {score} {HEADER_TAIL}"


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
            header=header(event, moment),
            persona=default_persona(listener),
        )


assert isinstance(PreludeOrchestrator(), Orchestrator)
