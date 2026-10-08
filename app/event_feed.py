"""Contract for the EventFeed and moment-detection module.

This file is a contract, not a component. It declares the data shapes and the
interface that `EventFeed` implementers satisfy, and contains no behaviour: no
file access, no parsing, no detection rules, no defaults that compute anything.

The module itself is reserved for IBM Bob (see CLAUDE.md). Nothing in this repo
implements `EventFeed`, and nothing here should grow into an implementation.
Callers depend on these shapes; Bob supplies the class behind them.

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
