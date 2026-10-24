"""StatsBomb implementation of the EventFeed protocol.

Reads match event data from data/raw/events/<match_id>.json and returns
raw source records unchanged. Goals (Shot events with outcome "Goal") in
periods 1-4 are the only defining moments. Period 5 (penalty shootout) is
excluded.
"""

import json
from pathlib import Path
from typing import Sequence

from app.event_feed import EventFeed, EventWindow, Moment, RawEvent

_RAW = Path(__file__).resolve().parent.parent / "data" / "raw"


class StatsBombEventFeed:
    """Satisfies the EventFeed protocol using local StatsBomb JSON files."""

    def load_match(self, match_id: int) -> Sequence[RawEvent]:
        """Return every event for *match_id* in feed order, untouched."""
        path = _RAW / "events" / f"{match_id}.json"
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)

    def defining_moments(self, match_id: int) -> Sequence[Moment]:
        """Return Goal-outcome shots from periods 1-4, earliest first.

        Period 5 is the penalty shootout; its goals are excluded because
        the shootout decides the trophy, not the scoreline.
        """
        events = self.load_match(match_id)
        goals = [
            event
            for event in events
            if event["type"]["name"] == "Shot"
            and event["shot"]["outcome"]["name"] == "Goal"
            and 1 <= event["period"] <= 4
        ]
        goals.sort(key=lambda e: (e["period"], e["minute"], e["second"]))
        return [
            Moment(
                type="Goal",
                team=event["team"]["name"],
                player=event["player"]["name"],
                minute=event["minute"],
                second=event["second"],
            )
            for event in goals
        ]

    def event_window(
        self,
        match_id: int,
        moment: Moment,
        seconds_before: float,
    ) -> EventWindow:
        """Return events in the *seconds_before* run-up to *moment*.

        The window ends at the moment (inclusive). It does not cross period
        boundaries: if *seconds_before* reaches before the first event of the
        period, the window is truncated there. Raw source records are returned
        unchanged. *EventWindow.seconds_before* records the requested span, not
        the span actually covered.
        """
        events = self.load_match(match_id)
        end_seconds = moment.minute * 60 + moment.second
        start_seconds = end_seconds - seconds_before

        # Identify the period the moment belongs to by finding its source event.
        moment_period = next(
            event["period"]
            for event in events
            if event["type"]["name"] == "Shot"
            and event["shot"]["outcome"]["name"] == "Goal"
            and event["minute"] == moment.minute
            and event["second"] == moment.second
            and event["team"]["name"] == moment.team
            and event["player"]["name"] == moment.player
        )

        window_events = [
            event
            for event in events
            if event["period"] == moment_period
            and start_seconds <= event["minute"] * 60 + event["second"] <= end_seconds
        ]
        # Feed order is preserved (events are already in index order from JSON).
        return EventWindow(
            moment=moment,
            events=window_events,
            seconds_before=seconds_before,
        )


# Verify the protocol is satisfied at import time (cheap isinstance check).
assert isinstance(StatsBombEventFeed(), EventFeed)
