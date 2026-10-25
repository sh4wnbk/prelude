"""Contract for the EventFeed and moment-detection module.

This file is a contract, not a component. It declares the data shapes and the
interface that implementers satisfy, and contains no behaviour: no file access,
no parsing, no detection rules, no defaults that compute anything.

The module itself is reserved for IBM Bob (see CLAUDE.md), and nothing here
should grow into an implementation. `app/statsbomb_event_feed.py` is Bob's
class, and it satisfies `EventFeed`.

There are two protocols, because the contract is implemented in stages:

  * `EventFeed` is built. `StatsBombEventFeed` satisfies it.
  * `BuildupFeed` is `EventFeed` plus `buildup`, which is **not implemented**.
    It is separate so that the tests which prove `EventFeed` is satisfied keep
    proving it while `buildup` is still pending. Once `buildup` is built the
    two can be merged into one protocol, with the tests changed in the same
    commit.

See docs/bob_brief.md for what to build, which files to read, and which tests
must pass.
"""

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence, runtime_checkable

# A single raw StatsBomb event, exactly as it appears in the JSON feed. Kept as
# a mapping rather than a parsed type so the window can hand back untouched
# source records, which is what "Verified from play data" has to point at.
RawEvent = Mapping[str, Any]


@dataclass(frozen=True)
class Moment:
    """One defining moment in a match.

    `type` names the kind of moment. The only kind the acceptance tests cover
    is `"Goal"`. `team` and `player` are the full recorded StatsBomb names, not
    shortened or reformatted, and `minute` and `second` are the raw clock
    fields.

    There is no period field. The 2022 shootout is therefore not distinguishable
    from extra time by a `Moment` alone, which is why excluding it is a rule the
    implementation applies rather than something a caller can filter on later.
    Adding `period` is the first extension to consider.

    `minute` floors the match clock, so minute 50 second 27 falls in the 51st
    minute as a broadcast would caption it. Do not add one here; the display
    layer decides how to caption it.
    """

    type: str
    team: str
    player: str
    minute: int
    second: int


@dataclass(frozen=True)
class EventWindow:
    """The run of play leading up to a moment.

    `events` holds the raw events in feed order, oldest first, ending with the
    event the moment was built from. `seconds_before` is the window length that
    was requested, not the span actually covered, which may be shorter at the
    start of a period.
    """

    moment: Moment
    events: Sequence[RawEvent]
    seconds_before: float


#: The `shot.type.name` values that make a goal a set piece. StatsBomb records
#: the type on the shot itself, so this is read off the goal event rather than
#: inferred from `play_pattern` or from the events before it.
#:
#: Only two of these occur among the goals in the two covered matches: every
#: 1986 goal is `"Open Play"`, and the 2022 final's six goals are three
#: `"Open Play"` and three `"Penalty"`. `"Free Kick"` appears on six 1986 shots,
#: none of which scored, and `"Corner"` appears in neither match. So the free
#: kick and corner branches are specified here and are not exercised by any
#: test, because there is no goal in `data/raw/` to exercise them with.
SET_PIECE_SHOT_TYPES = frozenset({"Penalty", "Free Kick", "Corner"})


@dataclass(frozen=True)
class Buildup:
    """The possession a goal came from, and the one before it for a set piece.

    This exists because `EventWindow` cannot answer the set piece case. A
    window is a span of clock time, and a penalty is alone in its own
    possession: a 30 second window around one of the 2022 penalties holds
    exactly one event, the kick. The foul that won it is in the possession
    before, 71 to 91 seconds earlier. Narration needs that foul, and padding
    the window to reach it would break the window's own truncation rule.

    `events` holds raw source records, untouched, in feed order, oldest first,
    ending with the goal shot. Events recorded after the shot in the same
    possession, which is usually the goalkeeper's record, are excluded, exactly
    as in `EventWindow`.

    `possessions` holds the StatsBomb possession numbers included, in order:
    one for an open play goal, two for a set piece. It is what makes "plus the
    previous possession" something a caller can check rather than infer from
    the events.

    `set_piece` is the goal's `shot.type.name` when it is in
    `SET_PIECE_SHOT_TYPES`, and `None` otherwise. A caller that needs to say
    the goal came from a penalty reads it here rather than re-deriving it.
    """

    moment: Moment
    events: Sequence[RawEvent]
    possessions: Sequence[int]
    set_piece: str | None


@runtime_checkable
class EventFeed(Protocol):
    """Reads a match's events and finds the moments worth narrating."""

    def load_match(self, match_id: int) -> Sequence[RawEvent]:
        """Return every event for `match_id`, in feed order."""
        ...

    def defining_moments(self, match_id: int) -> Sequence[Moment]:
        """Return the match's defining moments, earliest first.

        Ordering is by period, then minute, then second.
        """
        ...

    def event_window(
        self,
        match_id: int,
        moment: Moment,
        seconds_before: float,
    ) -> EventWindow:
        """Return the events in the `seconds_before` run-up to `moment`."""
        ...


@runtime_checkable
class BuildupFeed(EventFeed, Protocol):
    """`EventFeed`, plus the buildup to a moment.

    **Not implemented.** `StatsBombEventFeed` satisfies `EventFeed` and does not
    satisfy this. See docs/bob_brief.md, Task 3.
    """

    def buildup(self, match_id: int, moment: Moment) -> Buildup:
        """Return the possession `moment` came from, and the one before it if
        the goal came from a set piece.

        The rules, each of which has a test in `tests/test_event_feed.py`:

        **The goal's possession, truncated at the shot.** Every event of the
        possession the goal shot belongs to, up to and including the shot. What
        StatsBomb records after the shot in that possession, which is usually
        the goalkeeper's event, is excluded. This is the same truncation
        `event_window` applies, and for the same reason: the goal is the end of
        the moment.

        **The previous possession, in full, only for a set piece.** A goal is a
        set piece when its `shot.type.name` is in `SET_PIECE_SHOT_TYPES`, read
        off the goal event itself. For a set piece, the possession numbered one
        below the goal's comes first, in full, and then the goal's possession.
        For an open play goal there is one possession and nothing reaches back.

        **Raw source records, feed order, oldest first.** Identical to the
        records in `data/raw/`, untouched, exactly as `event_window` returns
        them. "Verified from play data" has to point at something in that
        directory.

        **Do not cross a period boundary.** Every event in the buildup is in
        the goal's own period. This is not hypothetical: possession 99 of the
        1986 match spans the half time break, and four possessions of the 2022
        final span a period boundary. If the previous possession began in an
        earlier period, only its events in the goal's period are included.

        **Do not pad.** If the previous possession does not exist, or lies
        entirely in an earlier period, return what exists and no more. A short
        buildup is correct, in the same way a short window is correct.
        """
        ...
