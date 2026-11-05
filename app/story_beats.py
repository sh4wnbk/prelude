"""The passage curated down to its story beats, which is what the model sees.

`app/narration_prompt.py` reads one `Fact` per recorded event, and that is the
right shape for the cited narration: a citation has to point at a record, so
every record needs a number. The goal call cites nothing, and handing it the
same list is what produced the candidates of 2026-10-31.

**The complaint, in Shawn's words: the candidates echo the fact list.** Given
twenty-four lines of which eight are a ball receipt and seven are a carry of
under a yard, the model wrote "received, carried and passed" over and over,
because that is what the page in front of it said. Nothing in
`app/grounding.py` was wrong about any of it. A receipt is a real record and
so is a touch on the spot; they are simply not beats of a story, and a
narration built out of them is a list of records read aloud.

So the curation happens here, before the prompt, and it is Prelude's job
whatever model narrates: a better model given twenty-four records including
eight receipts writes the same sentence about the receipts.

**What is kept, and nothing is kept for being interesting.** Each rule is a
recorded field read against a threshold that already exists in
`app/narration_grammar.py`, which is the same threshold `app/grounding.py`
refuses a claim on:

| Kept | Why it is a beat |
| ---- | ---------------- |
| the ball recovery | the move starts somewhere and this is where |
| every pass | the chain is the move; `forward` or `back` off the change in x, `long` at `LONG_PASS_YARDS` |
| every carry of `RUN_YARDS` or more | a run, with its distance and whether it ended in the box |
| every dribble past an opponent | the turning points, one beat for the two records |
| pressure on the player on the ball | "under pressure" is a claim and this is the record behind it |
| the finish | with the body part and whether it was struck first time |

**What is dropped.** `Ball Receipt*`, because a pass that reached its
recipient already says they received it, and a carry under `RUN_YARDS`,
because a player taking a touch where he stands is not a beat and "drove
forward" over 0.7 yards is what the check spent Task 9d refusing. A record of
any other type is kept rather than guessed at, the way `EVENT_VERBS` names a
type it has no verb for.

**No beat carries a clock.** Not a minute, not a second, not a timestamp: a
goal call says when nothing happened, the header above it says when the goal
came, and `app/grounding.py` refuses a digit in the narration anyway. `Beat`
in `app/narration_prompt.py` carries all three fields and this deliberately
does not, so a clock cannot reach the prompt through a beat. The pairing that
needs a clock, a `Dribble` with the `Dribbled Past` beside it, is done here
against the records and then left behind.

**The check is unchanged and still reads the full record.** A narration is
verified against every `Fact` of the passage, so the curation can only narrow
what a narration may say, never widen it: a line about a ball receipt would
still pass the check and will not be written, because the model was not shown
one. That is the trade this module makes, and it is the right way round.

**`play_pattern` and the own half are stated once.** Both were on every line,
which is twenty-four copies of two facts, and a repetition in the prompt is a
repetition in the narration. They belong to the passage rather than to a beat,
so `Story` holds them and the block says each one once.

Standard library only.
"""

from dataclasses import dataclass, fields
from typing import Mapping, Sequence

from app.narration_grammar import (
    DIRECTION_YARDS,
    RUN_YARDS,
    carry_yards,
    change_in_x,
)
from app.narration_prompt import (
    DRIBBLE,
    EVENT_VERBS,
    LONG_PASS_YARDS,
    Beat,
    Fact,
    Facts,
    key_beats,
    spoken_names,
)

#: The kinds of beat. They are the story's words rather than StatsBomb's,
#: because a beat is a turn in the telling and not a record type: one dribble
#: past an opponent is two records and one beat, and a carry is only a beat
#: when it was long enough to be a run.
RECOVERY = "recovery"
PASS = "pass"
RUN = "run"
DRIBBLE_PAST = "dribble past"
PRESSURE = "pressure"
FINISH = "finish"
OTHER = "other"

#: The record types that are not beats and are left out.
#:
#: `Ball Receipt*` says a player received a pass, which the pass already says:
#: the beat for it names the recipient, so a receipt is the same fact written
#: twice from the other end. Eight of the twenty-four records in the 1986
#: passage are receipts and five of the thirteen in the 2022 one, and the
#: candidates of 2026-10-31 said "received" in almost every telling.
#:
#: `Dribble` is here for a different reason: it is not dropped, it is folded.
#: The `Dribbled Past` record beside it names the defender who was beaten, and
#: one beat says both. A `Dribble` with no `Dribbled Past` at the same clock
#: went past nobody, which `key_beats` already says is not a beat, and that one
#: is kept as its own beat rather than silently thrown away.
NOT_A_BEAT = frozenset({"Ball Receipt*"})

#: The record types that are pressure applied to somebody.
#:
#: A `Pressure` is a beat when it was pressure on the player with the ball,
#: which is how Peter Reid reaches the prompt at all: pressing is his only
#: record in the 1986 passage, and without it "Beardsley and Reid closed him
#: down" cannot be written. `_pressed_the_carrier` is what decides.
PRESSED_TYPES = frozenset({"Pressure"})


@dataclass(frozen=True)
class StoryBeat:
    """One beat of the story, with the recorded fields a goal call says.

    Every field is copied out of a record or read off two coordinates, so a
    beat asserts nothing a `Fact` does not. `event_ids` is what points back at
    `data/raw/`, and it holds two for a dribble past an opponent because that
    beat is two records.

    **There is no minute, no second and no timestamp, and that is the point.**
    A goal call carries no clock, and a field a beat carries is a field the
    prompt can print.
    """

    kind: str
    #: What a narration calls this player: `Beat.name`, the recorded nickname
    #: where the lineups file holds one.
    player: str
    team: str
    event_ids: tuple[str, ...]
    #: What the record is, where `kind` is `OTHER`: the StatsBomb type name,
    #: named rather than guessed at.
    action: str | None = None
    #: `pass.recipient.name`, as a narration would say it.
    recipient: str | None = None
    #: "forward", "back", or empty where the records show neither. Read off
    #: the change in x against `DIRECTION_YARDS`, which is the threshold
    #: `app/grounding.py` refuses the word on.
    direction: str = ""
    #: `pass.length` at `LONG_PASS_YARDS` or more.
    long_ball: bool = False
    #: `pass.goal_assist`. One pass in a passage carries it.
    assist: bool = False
    #: Whether this is a carry of `RUN_YARDS` or more, which is a run rather
    #: than a touch on the spot.
    #:
    #: **It is a flag and not a figure, and the run of 2026-11-05 is why.**
    #: The beats carried the distance in whole yards and every 1986 candidate
    #: read it out: "carried forward thirty-five yards, evaded Reid, beat
    #: Butcher, ran forward seventeen yards, beat Fenwick, ran forward
    #: seventeen yards into the box". It is grounded, because the records hold
    #: the lengths, and the two seventeens read as a stumble rather than as a
    #: build. A figure in front of a model is a figure in the narration.
    long_carry: bool = False
    #: Whether this beat was inside the box the team was attacking: where a
    #: run or a pass ended, and where a shot was struck from. One field
    #: rather than three, because it is one coordinate read against the
    #: eighteen yard line either way; `beat_line` says it in the words the
    #: kind calls for.
    in_the_box: bool = False
    #: The defenders who were beaten, in order, for a dribble past an
    #: opponent. A tuple rather than one name because consecutive dribbles
    #: are one beat: "past Beardsley, Butcher and Fenwick" is how the
    #: references say it and how a listener hears four defenders rather than
    #: one. `_grouped` is what collapses them.
    beaten: tuple[str, ...] = ()
    #: Whether a carry was absorbed into this dribble beat, which is what
    #: lets the narration say the ball was carried forward between the
    #: defenders without the carries having beats of their own.
    carried: bool = False
    #: `under_pressure` on the record itself.
    under_pressure: bool = False
    #: `shot.first_time`.
    first_time: bool = False
    #: `shot.body_part.name`, for the finish.
    body_part: str | None = None


#: The fields a beat may never carry, asserted rather than assumed.
#: `tests/test_narrator_candidates.py` reads it off `StoryBeat` itself, so a
#: clock added to the dataclass fails a test rather than reaching a prompt.
NO_CLOCK_FIELDS = frozenset({"minute", "second", "timestamp", "clock"})


@dataclass(frozen=True)
class Story:
    """The beats of one passage, and the two things true of all of them.

    `play_pattern` and `started_in_own_half` sit here rather than on every
    beat because they are facts about the passage. Printed once, they are two
    claims the narration may make; printed per beat they were two claims
    repeated twenty-four times.
    """

    beats: tuple[StoryBeat, ...]
    team: str
    play_pattern: str | None
    started_in_own_half: bool
    #: How many records the passage holds and how many of them became beats,
    #: so a report can say what the curation left out without re-deriving it.
    records: int

    @property
    def kept(self) -> int:
        return len(self.beats)


def _direction(facts: Facts, beat: Beat) -> str:
    """"forward", "back", or neither, for the side in possession only.

    StatsBomb mirrors a defensive record's coordinates, so "forward" on a
    defender's record would mean the way his own team was going, which is the
    opposite of what the word says in a narration about this move.
    """
    if beat.team != facts.moment.team:
        return ""
    change = change_in_x(beat)
    if change is None:
        return ""
    if change >= DIRECTION_YARDS:
        return "forward"
    if change <= -DIRECTION_YARDS:
        return "back"
    return ""


def _pressed_the_carrier(facts: Facts, fact: Fact) -> bool:
    """Whether this `Pressure` was pressure on the player with the ball.

    Read off `under_pressure`, which is StatsBomb's own link: it is set on a
    record when an opponent's `Pressure` overlapped it. The record it
    overlapped is the possession team's nearest one in feed order, looking
    back first and then forward, because a pressure is recorded during
    somebody's touch rather than instead of it.

    **Feed order rather than the clock.** Matching on the second would drop
    Terry Butcher's pressure in the 1986 passage: it is recorded at 54:17 and
    the carry it overlapped is at 54:15, since the clock fields floor and a
    pressure lasts longer than the touch that began under it. Nothing in the
    beat keeps either value.
    """
    ours = [
        one
        for one in facts.facts
        if one.beat.team == facts.moment.team
    ]
    before = [one for one in ours if one.beat.index < fact.beat.index]
    after = [one for one in ours if one.beat.index > fact.beat.index]
    neighbour = (before[-1] if before else None) or (
        after[0] if after else None
    )
    return bool(neighbour and neighbour.beat.under_pressure)


def _dribbler(facts: Facts, beaten: Fact) -> Fact | None:
    """The `Dribble` record paired with a `Dribbled Past`, or `None`.

    The pair is what `key_beats` already builds: the two records share a
    clock, one naming the player who went past and one the player who was
    beaten. This reads the pairing off the clock and then keeps neither.
    """
    clock = (beaten.beat.minute, beaten.beat.second)
    return next(
        (
            fact
            for fact in facts.facts
            if fact.beat.action == "Dribble"
            and (fact.beat.minute, fact.beat.second) == clock
        ),
        None,
    )


def story(facts: Facts) -> Story:
    """Curate one passage down to the beats a goal call tells.

    The order is the records' own, by the index of the first record behind
    each beat, so the beats run in the order the play did.
    """
    spoken = spoken_names(facts)
    dribbles = {
        number
        for key in key_beats(facts)
        if key.kind == DRIBBLE
        for number in key.numbers
    }
    goal = facts.goal_fact

    beats: list[StoryBeat] = []
    for fact in facts.facts:
        beat = fact.beat
        if beat.action in NOT_A_BEAT:
            continue
        if fact.number == goal.number:
            beats.append(
                StoryBeat(
                    kind=FINISH,
                    player=beat.name,
                    team=beat.team,
                    event_ids=(beat.event_id,),
                    first_time=beat.first_time,
                    body_part=facts.body_part or beat.body_part,
                    in_the_box=bool(beat.start and beat.start.in_the_box),
                    under_pressure=beat.under_pressure,
                )
            )
            continue
        if beat.action == "Dribbled Past":
            dribbler = _dribbler(facts, fact)
            if dribbler is None:
                # No `Dribble` beside it, so there is no player to credit.
                # Kept as itself rather than dropped or attributed.
                beats.append(
                    StoryBeat(
                        kind=OTHER,
                        player=beat.name,
                        team=beat.team,
                        event_ids=(beat.event_id,),
                        action=beat.action,
                    )
                )
                continue
            beats.append(
                StoryBeat(
                    kind=DRIBBLE_PAST,
                    player=dribbler.beat.name,
                    team=dribbler.beat.team,
                    event_ids=(dribbler.beat.event_id, beat.event_id),
                    beaten=(beat.name,),
                    under_pressure=dribbler.beat.under_pressure,
                )
            )
            continue
        if beat.action == "Dribble":
            if fact.number in dribbles:
                # Folded into the dribble-past beat above.
                continue
            beats.append(
                StoryBeat(
                    kind=OTHER,
                    player=beat.name,
                    team=beat.team,
                    event_ids=(beat.event_id,),
                    action=beat.action,
                    under_pressure=beat.under_pressure,
                )
            )
            continue
        if beat.action == "Ball Recovery":
            beats.append(
                StoryBeat(
                    kind=RECOVERY,
                    player=beat.name,
                    team=beat.team,
                    event_ids=(beat.event_id,),
                    under_pressure=beat.under_pressure,
                )
            )
            continue
        if beat.action == "Pass":
            beats.append(
                StoryBeat(
                    kind=PASS,
                    player=beat.name,
                    team=beat.team,
                    event_ids=(beat.event_id,),
                    recipient=(
                        spoken.get(beat.recipient, beat.recipient)
                        if beat.recipient
                        else None
                    ),
                    direction=_direction(facts, beat),
                    long_ball=beat.long_pass,
                    assist=beat.goal_assist,
                    in_the_box=bool(beat.end and beat.end.in_the_box),
                    under_pressure=beat.under_pressure,
                )
            )
            continue
        if beat.action == "Carry":
            yards = carry_yards(beat)
            if yards is None or yards < RUN_YARDS:
                # A touch on the spot is not a beat. Dropping it is what stops
                # "drove forward" over 0.7 yards being written in the first
                # place, rather than refused after it is.
                continue
            beats.append(
                StoryBeat(
                    kind=RUN,
                    player=beat.name,
                    team=beat.team,
                    event_ids=(beat.event_id,),
                    direction=_direction(facts, beat),
                    long_carry=True,
                    in_the_box=bool(beat.end and beat.end.in_the_box),
                    under_pressure=beat.under_pressure,
                )
            )
            continue
        if beat.action in PRESSED_TYPES:
            if not _pressed_the_carrier(facts, fact):
                continue
            beats.append(
                StoryBeat(
                    kind=PRESSURE,
                    player=beat.name,
                    team=beat.team,
                    event_ids=(beat.event_id,),
                )
            )
            continue
        beats.append(
            StoryBeat(
                kind=OTHER,
                player=beat.name,
                team=beat.team,
                event_ids=(beat.event_id,),
                action=beat.action,
                under_pressure=beat.under_pressure,
            )
        )

    ours = [
        fact.beat
        for fact in facts.facts
        if fact.beat.team == facts.moment.team and fact.beat.start
    ]
    return Story(
        beats=_grouped(tuple(enumerate(beats))),
        team=facts.moment.team,
        play_pattern=next(iter(sorted(facts.play_patterns)), None),
        started_in_own_half=bool(ours and ours[0].start.in_own_half),
        records=len(facts.facts),
    )


def beat_line(beat: StoryBeat) -> str:
    """One beat said plainly, in the words a narration would use.

    The extras are the recorded fields, in a fixed order, so two beats of a
    kind read the same way and a reader of the prompt can see at a glance
    which claims this beat supports.
    """
    if beat.kind == DRIBBLE_PAST:
        said = "{} ({}) dribbled past {}".format(
            beat.player, beat.team, _and(beat.beaten)
        )
    elif beat.kind == PRESSURE:
        said = "{} ({}) pressed the player on the ball".format(
            beat.player, beat.team
        )
    elif beat.kind == PASS:
        said = "{} ({}) passed to {}".format(
            beat.player, beat.team, beat.recipient or "nobody recorded"
        )
    elif beat.kind == RUN:
        said = "{} ({}) carried the ball, a long carry".format(
            beat.player, beat.team
        )
    elif beat.kind == RECOVERY:
        said = "{} ({}) recovered the ball".format(beat.player, beat.team)
    elif beat.kind == FINISH:
        said = "{} ({}) shot".format(beat.player, beat.team)
    else:
        said = "{} ({}) {}".format(
            beat.player,
            beat.team,
            EVENT_VERBS.get(beat.action or "", beat.action or "had the ball"),
        )

    extras: list[str] = []
    if beat.carried:
        extras.append(
            "carrying the ball {} between them".format(beat.direction)
            if beat.direction
            else "carrying the ball between them"
        )
    if beat.assist:
        extras.append("the assist")
    if beat.long_ball:
        extras.append("long")
    if beat.direction and not beat.carried:
        extras.append(beat.direction)
    if beat.in_the_box:
        extras.append(
            {
                PASS: "into the box",
                RUN: "ending in the box",
                FINISH: "from inside the box",
            }.get(beat.kind, "in the box")
        )
    if beat.under_pressure:
        extras.append("under pressure")
    if beat.first_time:
        extras.append("first time")
    if beat.kind == FINISH and beat.body_part:
        extras.append("with his {}".format(beat.body_part.lower()))
    if extras:
        said += ", " + ", ".join(extras)
    return said


def _and(names: Sequence[str]) -> str:
    """"Beardsley, Butcher and Fenwick", for the defenders of one beat."""
    if len(names) < 2:
        return "".join(names)
    return "{} and {}".format(", ".join(names[:-1]), names[-1])


def _grouped(placed: Sequence[tuple[int, StoryBeat]]) -> tuple[StoryBeat, ...]:
    """Consecutive dribbles past one player as one beat, carries absorbed.

    **What the run of 2026-11-05 showed.** Shawn read the ten candidates
    aloud: the event order was right in every 1986 one, and the model still
    narrated every beat in one long comma chain, so there was no build and no
    grouping. "Beat Butcher, ran forward seventeen yards, beat Fenwick, ran
    forward seventeen yards" against the references' "past Beardsley, Butcher
    and Fenwick". A list of beats is read out as a list of beats, so the
    grouping has to be in the beats.

    **The rule.** A run of `DRIBBLE_PAST` beats by one player collapses into
    one, naming the defenders in order, when the only beats between them are
    a carry (which is absorbed and loses its own beat) or a pressure (which
    keeps its own beat). Anything else ends the group: a pass, a recovery,
    the finish, or a carry that ended in the box, because that one is a
    change of position and the references say it in its own clause.

    **The group sits where it ends**, which is the index of the last defender
    beaten, so a pressure recorded inside its span is said before it. That is
    the references' order too: "though Beardsley and Reid closed him down, he
    went past Beardsley, Butcher and Fenwick".
    """
    beats = [beat for _index, beat in placed]
    absorbed: set[int] = set()
    merged: dict[int, StoryBeat] = {}
    at = 0
    while at < len(beats):
        if beats[at].kind != DRIBBLE_PAST:
            at += 1
            continue
        first = beats[at]
        members = [at]
        carries: list[int] = []
        held: list[int] = []
        last = at
        ahead = at + 1
        while ahead < len(beats):
            other = beats[ahead]
            if other.kind == DRIBBLE_PAST and other.player == first.player:
                members.append(ahead)
                carries += held
                held = []
                last = ahead
                ahead += 1
                continue
            if other.kind == PRESSURE:
                ahead += 1
                continue
            if other.kind == RUN and not other.in_the_box:
                held.append(ahead)
                ahead += 1
                continue
            break
        if len(members) > 1:
            absorbed |= set(members[:-1]) | set(carries)
            ways = {beats[one].direction for one in carries}
            merged[last] = StoryBeat(
                kind=DRIBBLE_PAST,
                player=first.player,
                team=first.team,
                event_ids=tuple(
                    event_id
                    for one in members
                    for event_id in beats[one].event_ids
                ),
                beaten=tuple(
                    name for one in members for name in beats[one].beaten
                ),
                carried=bool(carries),
                direction=ways.pop() if len(ways) == 1 else "",
                # Said only where every record in the group holds it, so the
                # claim is true of whichever one it is pointed at.
                under_pressure=all(
                    beats[one].under_pressure for one in members
                ),
            )
        at = last + 1
    return tuple(
        merged.get(index, beat)
        for index, beat in enumerate(beats)
        if index not in absorbed
    )


def beats_block(one: Story) -> str:
    """The curated beats, numbered, with the two passage facts above them.

    Bulleted and not numbered, because rule 9 allows no digit in the
    narration and this is the one list the model is told to work from. The
    block says what the curation left out, because a model told "nothing
    happened that is not here" over a curated list is being told something
    untrue.
    """
    where = (
        "{} started the move in their own half.".format(one.team)
        if one.started_in_own_half
        else "The move did not start in {}'s own half.".format(one.team)
    )
    pattern = (
        "The possession is recorded as {}.".format(one.play_pattern)
        if one.play_pattern
        else "No play pattern is recorded for this possession."
    )
    # Bulleted rather than numbered. Rule 9 of the goal-call prompt allows no
    # digit anywhere in the narration, and the one list the model is told to
    # work from is the last place to put one in front of it.
    lines = ["  - {}".format(beat_line(beat)) for beat in one.beats]
    return "\n".join(
        [
            "THE BEATS OF THE PASSAGE",
            "The records of this move, in order, curated down to the beats of "
            "it. The",
            "ball receipts and the touches on the spot are left out because "
            "they are not",
            "beats: a pass below names who it reached, which is the same "
            "fact, and a",
            "player taking a touch where he stands is not a turn in the "
            "story. Yards are",
            "there for you to read and never to write.",
            "",
            "  {} {}".format(pattern, where),
            "",
        ]
        + lines
        + [
            "",
            "Tell every beat in that list and nothing outside it. The move "
            "may only be",
            "told with these players, these passes, these defenders, these "
            "carries, this",
            "body part and these two positions on the pitch; anything else "
            "is rejected,",
            "whether or not it happened. Where one beat names several "
            "defenders, say them",
            "as one move: that is how a listener hears four defenders "
            "rather than one.",
        ]
    )


def beat_fields() -> frozenset[str]:
    """The field names a `StoryBeat` carries, for the test that reads them."""
    return frozenset(field.name for field in fields(StoryBeat))


def kinds(one: Story) -> Mapping[str, int]:
    """How many beats of each kind, for a run's own report."""
    tally: dict[str, int] = {}
    for beat in one.beats:
        tally[beat.kind] = tally.get(beat.kind, 0) + 1
    return tally
