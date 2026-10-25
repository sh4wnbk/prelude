"""The facts a narration may use, the prompt built from them, and the fallback.

Three things live here, and they all read from one `Buildup`:

  * `Facts`, everything a narration is allowed to mention: the players, the
    teams, the clock values, the actions, and the goal's own shot type and body
    part. Nothing else about the match is in scope, so a narration that names
    something absent from `Facts` is not grounded.
  * `build_prompt`, which turns `Facts` into the prompt a model is given. It
    lists the run of play event by event and states the rules the narration has
    to obey, including the ones `app/grounding.py` enforces afterwards.
  * `template_narration`, the fallback. It assembles a short, plain narration
    straight from the events with no model involved, so it is grounded by
    construction. It is still checked like any other narration, because
    "grounded by construction" is a claim worth testing rather than trusting.

`Facts` is derived from raw records only. No field here is inferred, and the
clock values are the raw StatsBomb minute and second, which floor the match
clock; nothing adds one.

Standard library only, like the rest of `app/`.
"""

from dataclasses import dataclass
from typing import Mapping, Sequence

from app.event_feed import Buildup, Moment, RawEvent

#: How a StatsBomb event type is said in the fallback narration. Every type
#: that occurs in a buildup across the two matches in `data/raw/` is here; a
#: type with no entry is skipped by the fallback rather than guessed at.
TEMPLATE_VERBS: Mapping[str, str] = {
    "Ball Recovery": "recovers the ball",
    "Pass": "passes",
    "Ball Receipt*": "receives the ball",
    "Carry": "carries the ball",
    "Dribble": "dribbles",
    "Dribbled Past": "is dribbled past",
    "Pressure": "presses",
    "Duel": "contests the ball",
    "Clearance": "clears",
    "Block": "blocks",
    "Interception": "intercepts",
    "Dispossessed": "is dispossessed",
    "Miscontrol": "miscontrols",
    "Foul Committed": "commits a foul",
    "Foul Won": "wins a foul",
    "Goal Keeper": "plays the ball as goalkeeper",
    "Error": "makes an error",
    "Shot": "shoots",
}

#: The actions the fallback narration will mention, in the order the events
#: happen. The rest of a possession is the receipts, carries and pressures that
#: sit between them, which make a plain narration longer without making it say
#: more. The goal shot is always included, whatever this holds.
TEMPLATE_KEY_ACTIONS = frozenset(
    {
        "Ball Recovery",
        "Pass",
        "Dribble",
        "Clearance",
        "Interception",
        "Foul Committed",
        "Foul Won",
        "Shot",
    }
)

#: Sentences the fallback allows itself, counting the goal. Short on purpose:
#: it is what gets voiced when a model could not stay inside the data.
TEMPLATE_MAX_SENTENCES = 5

#: Sentences the prompt asks a model for.
DEFAULT_SENTENCES = 4


@dataclass(frozen=True)
class Beat:
    """One recorded event, reduced to what a narration could say about it.

    A beat is not a new source of truth. Every field is copied out of one raw
    record, and `event_id` is kept so any beat can be pointed back at the
    record it came from in `data/raw/`.
    """

    index: int
    minute: int
    second: int
    player: str
    team: str
    action: str
    event_id: str

    @property
    def clock(self) -> str:
        return f"{self.minute}:{self.second:02d}"


@dataclass(frozen=True)
class Facts:
    """Everything one narration is allowed to mention.

    `players` maps the full recorded player name to the team it was recorded
    under. `actions` holds the StatsBomb event type names present.

    `numbers` holds the numbers a narration may write as digits: every minute
    in the buildup, plus the second the goal was recorded at. It deliberately
    leaves out the other seconds. Every second a possession passes through is a
    number between 0 and 59, so admitting them would ground almost any small
    number a model invented: "beats 7 defenders" would pass because some event
    happened at second 7. Minutes, and the one second worth saying aloud, are
    what narration actually quotes.

    `set_piece` and `body_part` come off the goal shot itself. They are here
    because they are the two things a model invents most readily: a goal
    becomes a penalty, or a left foot becomes a header, and neither is visible
    in the run of play.
    """

    moment: Moment
    beats: tuple[Beat, ...]
    players: Mapping[str, str]
    teams: tuple[str, ...]
    numbers: frozenset[int]
    actions: frozenset[str]
    set_piece: str | None
    body_part: str | None

    @property
    def goal_beat(self) -> Beat:
        """The shot the moment was built from, which is the last beat."""
        return self.beats[-1]


def _goal_shot(buildup: Buildup) -> RawEvent:
    """The goal shot in a buildup, which the contract puts last."""
    return buildup.events[-1]


def facts_from_buildup(buildup: Buildup) -> Facts:
    """Read the facts a narration may use out of one buildup.

    Every value is copied from a raw record. Nothing is counted, ranked,
    summarised or inferred, because a fact this function invents is a fact the
    grounding check would then happily approve.
    """
    beats = tuple(
        Beat(
            index=event["index"],
            minute=event["minute"],
            second=event["second"],
            player=event["player"]["name"],
            team=event["team"]["name"],
            action=event["type"]["name"],
            event_id=event["id"],
        )
        for event in buildup.events
        if event.get("player")
    )

    players: dict[str, str] = {}
    for beat in beats:
        players.setdefault(beat.player, beat.team)

    teams: list[str] = []
    for beat in beats:
        if beat.team not in teams:
            teams.append(beat.team)

    numbers: set[int] = {beat.minute for beat in beats}
    numbers.add(buildup.moment.second)

    shot = _goal_shot(buildup)
    body_part = (shot.get("shot") or {}).get("body_part", {}).get("name")

    return Facts(
        moment=buildup.moment,
        beats=beats,
        players=players,
        teams=tuple(teams),
        numbers=frozenset(numbers),
        actions=frozenset(beat.action for beat in beats),
        set_piece=buildup.set_piece,
        body_part=body_part,
    )


def _run_of_play(facts: Facts) -> str:
    """The events in order, with the minute but not the second.

    The second is left out on purpose. Printing "54:04" and then forbidding any
    digit but the minute and the goal's second told the model to quote the
    prompt and then failed it for doing so, which is how the first live run
    went. The order of the lines carries the sequence, and minutes are
    groundable, so nothing a narration can read here is off limits.
    """
    return "\n".join(
        f"  min {beat.minute}  {beat.action}: {beat.player} ({beat.team})"
        for beat in facts.beats
    )


def build_prompt(facts: Facts, sentences: int = DEFAULT_SENTENCES) -> str:
    """The prompt for one goal.

    The rules in it are the rules `app/grounding.py` enforces afterwards, said
    plainly. A prompt that asked for less than the check requires would set the
    model up to fail, and the retry would not help it.
    """
    moment = facts.moment
    set_piece = facts.set_piece or "Open Play"
    body_part = facts.body_part or "not recorded"

    return f"""You are writing the narration for one goal in a football match.
The app this is for says only what the match data proves, so you may use the
facts below and nothing else. Anything you add from memory will be rejected.

THE GOAL
  Team:       {moment.team}
  Scorer:     {moment.player}
  Clock:      minute {moment.minute}, second {moment.second}
  Shot type:  {set_piece}
  Body part:  {body_part}

THE RUN OF PLAY
Each line is one recorded event, in the order it happened. Nothing happened
that is not here.
{_run_of_play(facts)}

RULES
1. Use only the player names, team names and numbers that appear above. A name
   or number that is not listed will be rejected, including a real player who
   is not in this passage.
2. Do not say the goal was a penalty, a free kick or a corner unless the shot
   type above says so. Do not name a body part other than the one above.
3. Write any count as a word, not a digit: "past two defenders", never
   "past 2 defenders". The only digits allowed are the minute of an event in
   the list above and the second the goal was scored at. Any other digit is
   rejected.
4. Describe only actions that appear above. Do not add a save, a cross, a
   header or a tackle that is not in the list.
5. No nicknames and no verdicts for the goal, the players or the match. Say
   what the data records, not how good it was. Words like "decisive",
   "brilliant" and "significant" are rejected.
6. Say nothing about the score, the result, or what the goal meant for the
   match. What you have is one passage of play, and it does not say who won.
7. No em dashes. Use a colon, a semicolon, parentheses or two sentences.
8. Write {sentences} sentences of plain, present-tense commentary. Output the
   narration only, with no preamble, heading or explanation.
"""


def template_narration(facts: Facts) -> str:
    """A short, plain narration assembled from the events, with no model.

    This is the fallback for when a model cannot stay inside the data. It is
    grounded by construction: every name, number and action in it is copied out
    of a beat. It reads plainly rather than well, which is the trade being
    made, and it uses the full recorded player names rather than shortening
    them, because a fallback should not be the thing that introduces a judgement
    call about what a player is called.
    """
    goal = facts.goal_beat
    candidates = [
        beat
        for beat in facts.beats[:-1]
        if beat.action in TEMPLATE_KEY_ACTIONS and beat.action in TEMPLATE_VERBS
    ]

    # A run like Maradona's is four separate Dribble events, which would read as
    # the same sentence four times over. Collapsing a run of the same player
    # doing the same thing loses no fact: the events are still what the label
    # points at, and the sentence still describes them.
    chosen: list[Beat] = []
    for beat in candidates:
        if chosen and (beat.player, beat.action) == (
            chosen[-1].player,
            chosen[-1].action,
        ):
            continue
        chosen.append(beat)

    # The goal is the point of the narration, so it keeps its place and the
    # run-up is trimmed from the front to fit around it.
    room = max(TEMPLATE_MAX_SENTENCES - 2, 0)
    chosen = chosen[-room:] if room else []

    lines = [f"Minute {goal.minute}."]
    lines += [f"{beat.player} {TEMPLATE_VERBS[beat.action]}." for beat in chosen]
    lines.append(f"{goal.player} shoots and scores for {goal.team}.")
    return " ".join(lines)
