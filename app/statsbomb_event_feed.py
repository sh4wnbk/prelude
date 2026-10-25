"""StatsBomb implementation of the EventFeed protocol.

Reads match event data from data/raw/events/<match_id>.json and returns
raw source records unchanged. Goals (Shot events with outcome "Goal") in
periods 1-4 are the only defining moments. Period 5 (penalty shootout) is
excluded.
"""

import json
from pathlib import Path
from typing import Sequence

from app.event_feed import (
    SET_PIECE_SHOT_TYPES,
    Buildup,
    EventFeed,
    EventWindow,
    Moment,
    RawEvent,
)

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

        # Identify the period and index of the source shot event.
        source_event = next(
            event
            for event in events
            if event["type"]["name"] == "Shot"
            and event["shot"]["outcome"]["name"] == "Goal"
            and event["minute"] == moment.minute
            and event["second"] == moment.second
            and event["team"]["name"] == moment.team
            and event["player"]["name"] == moment.player
        )
        moment_period = source_event["period"]
        shot_index = source_event["index"]

        window_events = [
            event
            for event in events
            if event["period"] == moment_period
            and start_seconds <= event["minute"] * 60 + event["second"] <= end_seconds
            and event["index"] <= shot_index
        ]
        # Feed order is preserved (events are already in index order from JSON).
        return EventWindow(
            moment=moment,
            events=window_events,
            seconds_before=seconds_before,
        )

    def buildup(self, match_id: int, moment: Moment) -> Buildup:
        """Return the possession(s) leading up to *moment*.

        For an open play goal: the goal's possession, truncated at the shot.
        For a set piece goal: the previous possession (period-filtered) followed
        by the goal's possession truncated at the shot.

        Does not cross period boundaries. Returns raw source records unchanged.
        """
        events = self.load_match(match_id)

        # Find the source shot event for this moment.
        shot = next(
            event
            for event in events
            if event["type"]["name"] == "Shot"
            and event["shot"]["outcome"]["name"] == "Goal"
            and event["minute"] == moment.minute
            and event["second"] == moment.second
            and event["team"]["name"] == moment.team
            and event["player"]["name"] == moment.player
        )

        goal_period = shot["period"]
        goal_possession = shot["possession"]
        shot_index = shot["index"]
        shot_type = shot["shot"]["type"]["name"]
        is_set_piece = shot_type in SET_PIECE_SHOT_TYPES

        # Collect the goal's possession up to and including the shot.
        goal_possession_events = [
            e
            for e in events
            if e["possession"] == goal_possession
            and e["index"] <= shot_index
        ]

        if is_set_piece:
            prev_possession = goal_possession - 1
            prev_possession_events = [
                e
                for e in events
                if e["possession"] == prev_possession
                and e["period"] == goal_period
            ]
            buildup_events = prev_possession_events + goal_possession_events
            possessions = [prev_possession, goal_possession] if prev_possession_events else [goal_possession]
        else:
            buildup_events = goal_possession_events
            possessions = [goal_possession]

        return Buildup(
            moment=moment,
            events=buildup_events,
            possessions=possessions,
            set_piece=shot_type if is_set_piece else None,
        )
