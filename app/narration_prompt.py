"""The facts a narration may use, the prompt built from them, and the fallback.

Three things live here, and they all read from one `Buildup`:

  * `Facts`, everything a narration is allowed to mention. At its centre is the
    numbered fact list: one plain sentence per recorded event, built by code out
    of the record, which is what the model narrates from and what
    `app/grounding.py` checks a narration against.
  * `build_prompt`, which turns `Facts` into the prompt a model is given. It
    prints the numbered facts and states the rules the narration has to obey,
    including the ones `app/grounding.py` enforces afterwards.
  * `template_narration`, the fallback. It assembles a short, plain narration
    straight from the facts with no model involved, so it is grounded by
    construction. It is still checked like any other narration, because
    "grounded by construction" is a claim worth testing rather than trusting.

**Why the facts are numbered.** A narration cites the facts each sentence used,
and the check then asks whether that sentence's names, actions and clocks are in
the facts it cited rather than merely somewhere in the passage. The number is the
whole mechanism: without it a sentence can only be checked against the buildup as
a lump, and "dribbles past Peter Reid" passes because a dribble and Reid both
occur in it, separately. Each `Fact` keeps the `Beat` it was built from, and
every beat keeps its `event_id`, so a cited number leads back to one record in
`data/raw/`.

`Facts` is derived from raw records only. No field here is inferred, and the
clock values are the raw StatsBomb minute and second, which floor the match
clock; nothing adds one.

Standard library only, like every module in `app/` but the hosted
service in `app/api.py`.
"""

import textwrap
from dataclasses import dataclass
from typing import Mapping, Sequence

from app.event_feed import Buildup, Moment, RawEvent

#: How a StatsBomb event type is said in a fact and in the fallback narration.
#: Every type that occurs in a buildup across the two matches in `data/raw/` is
#: here; a type with no entry falls back to naming the type itself rather than
#: being guessed at, and `tests/test_narration_prompt.py` checks that fallback
#: is unreachable with the data in the repo.
#:
#: **Past tense.** A buildup is playback of a passage that already happened, so
#: the facts are written as a record of it rather than as live commentary. The
#: narration follows, which `app/grounding.py` enforces: a present-tense verb in
#: a narration is refused, and the past-tense form is what grounds an event.
EVENT_VERBS: Mapping[str, str] = {
    "Ball Recovery": "recovered the ball",
    "Pass": "passed",
    "Ball Receipt*": "received the ball",
    "Carry": "carried the ball",
    "Dribble": "dribbled",
    "Dribbled Past": "was dribbled past",
    "Pressure": "pressed",
    "Duel": "contested the ball",
    "Clearance": "cleared",
    "Block": "blocked",
    "Interception": "intercepted",
    "Dispossessed": "was dispossessed",
    "Miscontrol": "miscontrolled",
    "Foul Committed": "committed a foul",
    "Foul Won": "won a foul",
    "Goal Keeper": "played the ball as goalkeeper",
    "Error": "made an error",
    "Shot": "shot",
}

#: The actions the fallback narration will mention, in the order the events
#: happen. The rest of a possession is the receipts, carries and pressures that
#: sit between them, which make a plain narration longer without making it say
#: more. The goal shot is always included, whatever this holds, and so is every
#: key beat: see `key_beats` and `template_narration`.
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

#: Sentences the fallback aims at, counting the minute line and the goal. Short
#: on purpose: it is what gets voiced when a model could not stay inside the
#: data. It is a target rather than a ceiling, because a key beat is never
#: dropped to meet it; a passage with more key beats than this runs longer.
TEMPLATE_MAX_SENTENCES = 5

#: The two sides of one dribble past an opponent. StatsBomb records the
#: `Dribble` against the player who beat someone and the `Dribbled Past`
#: against the player who was beaten, so one beat of play is two records.
DRIBBLE_TYPES = frozenset({"Dribble", "Dribbled Past"})

#: The two sides of one foul, likewise.
FOUL_TYPES = frozenset({"Foul Won", "Foul Committed"})

#: What `Facts.set_piece` says when the goal was a penalty.
PENALTY = "Penalty"

#: The kinds of key beat.
SHOT = "shot"
DRIBBLE = "dribble"
FOUL = "foul"

#: Sentences the prompt asks a model for.
DEFAULT_SENTENCES = 4

#: Characters the hero prompt asks a narration to come to, roughly.
#:
#: **It is a length the budget can pay for, not a style.** The recordings are
#: three per match and a monthly allowance pays for them, so a narration's
#: length is a price. The candidates of 2026-10-30 put the relation on
#: measured ground: the 1986 one that was usable came to 459 characters and
#: cost 1,491 billed for its three recordings, and the one that spelled every
#: clock out in words came to 988 and cost 4,299, more than the whole run is
#: allowed. So the target is set at about the length of the shorter one.
#:
#: It is a target and not a ceiling, because nothing here can make a model
#: count. `scripts/hero_candidates.py` is what enforces a price, by dropping a
#: candidate whose recordings would not fit the budget.
HERO_TARGET_CHARACTERS = 450

#: Characters per word in the narrations measured on 2026-10-30: 459
#: characters in 68 words, and 367 in 58. The prompt states the target in
#: words as well as characters, because a model counts words rather better
#: than it counts characters, and this is what converts the one into the
#: other. Nothing is load bearing in the sixth decimal place.
CHARACTERS_PER_WORD = 6.75

#: The one style every narration is written in, whatever persona was asked
#: for. It was the Storyteller's style text in `app/personas.py` until the
#: personas stopped carrying one.
#:
#: **There is one style because three could not be told apart.** Tasks 6c, 4b
#: and 6d asked for three registers three ways, described to a small model,
#: described to a capable one and shown to it as a worked example, and
#: `docs/narration_eval.md` holds what came back: words per sentence spread
#: 0.6, 2.1 and 1.9 across the voices, and on the 54:18 goal the three wrote
#: the same five sentences. The rules below are narrow enough that there is no
#: room for a register inside them, so the narration text is one text and
#: Phase 5 separates the personas in the audio.
#:
#: It is the Storyteller's text, which is the plainest of the three and the
#: one `docs/VOICE.md` was written around.
NARRATION_STYLE = (
    "Write in the calm, even voice of a documentary narrator. Measured "
    "sentences, told in the past tense, one step of the passage at a time. "
    "The facts carry it, so add no colour and no atmosphere the records do "
    "not hold: no weather, no crowd, no reading of anybody's intentions. Let "
    "the plainness be the register."
)


#: StatsBomb's pitch is 120 by 80, and x always runs towards the goal the team
#: the record belongs to is attacking. A defensive record is mirrored, which is
#: why these two lines can be read the same way for either team: Beardsley's
#: `Pressure` at x 64.9 and Maradona's `Carry` at x 55.2 are the same spot on
#: the pitch seen from the two ends.
#:
#: So `x < 60` is the recorded player's own half, and `x >= 102` is inside the
#: box they are attacking. Both numbers are the pitch's own geometry: the
#: halfway line, and the eighteen yard line at 120 minus 18.
HALFWAY_X = 60.0
BOX_X = 102.0

#: A pass this long is what the game calls a long ball, in StatsBomb's yards.
#:
#: It is a threshold and not a reading of a record, which makes it the one
#: number in this module somebody could argue with. It is set at thirty
#: because that is what separates the two hero passages rather than a judgement
#: about football in general: the five passes of the 2022 counter are 20.1,
#: 11.6, 11.5, 38.5 and 26.0 yards, and the one a commentator calls a long ball
#: forward is the 38.5. Above twenty-six and below thirty-eight is the whole
#: room the data gives, so the middle of it is as defensible as either edge.
LONG_PASS_YARDS = 30.0


@dataclass(frozen=True)
class Spot:
    """One recorded location on the pitch, as the record writes it.

    Two questions get asked of a spot, and both are the pitch's geometry rather
    than anybody's reading of the play: which half it is in, and whether it is
    inside the box. A narration saying "in his own half" or "into the box" is
    making a claim this can answer.
    """

    x: float
    y: float

    @property
    def in_own_half(self) -> bool:
        return self.x < HALFWAY_X

    @property
    def in_the_box(self) -> bool:
        return self.x >= BOX_X


def spot(location) -> Spot | None:
    """A raw `[x, y]` pair as a `Spot`, or `None` where the record has none.

    A `Pressure` carries a location and a `Ball Receipt*` carries one; a
    `Dribbled Past` carries one too. Nothing is defaulted, because a spot this
    function invented is a spot a position claim would then be checked against.
    """
    if not location or len(location) < 2:
        return None
    return Spot(x=float(location[0]), y=float(location[1]))


def timestamp_seconds(timestamp: str) -> float | None:
    """A StatsBomb `timestamp` ("00:09:02.383") as seconds into the period.

    The minute and second fields floor the clock, so two events a second and a
    half apart can carry the same second. The timestamp is what the feed
    records to the millisecond, and it is what a duration has to be read off:
    "in under ten seconds" is a claim about the passage, and 35:12 to 35:22 is
    anything from nine seconds to eleven if the floored fields are all there is.
    """
    if not timestamp:
        return None
    hours, minutes, seconds = timestamp.split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


@dataclass(frozen=True)
class Beat:
    """One recorded event, reduced to what a narration could say about it.

    A beat is not a new source of truth. Every field is copied out of one raw
    record, and `event_id` is kept so any beat can be pointed back at the
    record it came from in `data/raw/`.

    **The fields after `nickname` are the ones the framework in
    `docs/VOICE.md` says out loud.** A goal call says "under pressure", "a long
    ball forward", "he set up Di María", "first time", "into the box" and "in
    his own half", and every one of those is a claim about a recorded field
    rather than colour: `under_pressure`, `pass_length`, `goal_assist`,
    `first_time`, and the two locations. They are copied, never derived, with
    one exception that is arithmetic rather than judgement: `Spot.in_own_half`
    and `Spot.in_the_box` read a coordinate against the pitch's own geometry.
    """

    index: int
    minute: int
    second: int
    player: str
    team: str
    action: str
    event_id: str
    #: The shorter name the lineups file records for this player, or `None`
    #: where it records none. Copied from `player_nickname`, like every other
    #: field here, and read by `app/recorded_names.py`. It defaults to `None`
    #: so a beat built without the lineups file is the full recorded name, as
    #: every beat was before the file was fetched.
    nickname: str | None = None
    #: The feed's millisecond timestamp, "00:09:02.383". `minute` and `second`
    #: floor the clock; this does not, and a duration is read off it.
    timestamp: str = ""
    #: `play_pattern.name`: how the possession this record belongs to started.
    #: "From Counter" on every record of both hero passages, which is what
    #: "the counter was on" is a claim about.
    play_pattern: str | None = None
    #: `under_pressure` on the record itself, which StatsBomb sets when an
    #: opponent's `Pressure` overlaps it.
    under_pressure: bool = False
    #: Where the record happened, and where it ended for a carry, a pass or a
    #: shot. `None` where the record carries neither.
    start: Spot | None = None
    end: Spot | None = None
    #: `pass.recipient.name`, the full recorded name of the player a pass was
    #: played to. This is what makes a chain ("Molina to MacAllister")
    #: checkable rather than two names with a preposition between them.
    recipient: str | None = None
    #: `pass.length`, in StatsBomb's yards.
    pass_length: float | None = None
    #: `pass.goal_assist`, which StatsBomb sets on the pass that set the goal
    #: up. "He set up Di María" is a claim about this field.
    goal_assist: bool = False
    #: `shot.first_time`, set when the shot was struck without a touch to
    #: control it first.
    first_time: bool = False
    #: `pass.body_part.name` or `shot.body_part.name`, whichever the record
    #: carries. `Facts.body_part` is the goal's, which is the one a narration
    #: says; this is per record.
    body_part: str | None = None

    @property
    def clock(self) -> str:
        return f"{self.minute}:{self.second:02d}"

    @property
    def seconds(self) -> float | None:
        """The timestamp as seconds into the period, or `None` without one."""
        return timestamp_seconds(self.timestamp)

    @property
    def long_pass(self) -> bool:
        """Whether this record is a pass the game would call a long ball."""
        return self.pass_length is not None and self.pass_length >= LONG_PASS_YARDS

    @property
    def name(self) -> str:
        """What a narration calls this player: the nickname where one is
        recorded, and the full recorded name where none is.

        Both are the data's own spellings. Nothing here shortens a name the
        lineups file does not shorten; see `app/recorded_names.py`.
        """
        return self.nickname or self.player


@dataclass(frozen=True)
class Fact:
    """One numbered plain fact, built by code from one recorded event.

    `number` counts from 1 and is what a narration cites. `beat` is the record
    the fact was read from, so a citation leads back to an `event_id` in
    `data/raw/` rather than merely to a sentence someone wrote. `text` is the
    fact as the prompt prints it: who, which team, what they did, and the clock.

    A fact names one player, because one record names one player. "Maradona
    dribbles past Butcher" is two records and so two facts: a `Dribble` on
    Maradona's and a `Dribbled Past` on Butcher's. Pairing them into a single
    fact would mean inferring which dribble went past whom, and a fact this
    module invents is a fact the grounding check would then approve.
    """

    number: int
    beat: Beat
    text: str

    @property
    def line(self) -> str:
        """The fact as the prompt prints it, number included."""
        return f"{self.number}. {self.text}"


@dataclass(frozen=True)
class Facts:
    """Everything one narration is allowed to mention.

    `facts` is the numbered list, one per recorded event, in the order they
    happened. It is what a narration cites and what the grounding check reads;
    `beats` is the same events without the numbering, for callers that only
    want the records.

    `players` maps the full recorded player name to the team it was recorded
    under, and `actions` holds the StatsBomb event type names present. Neither
    is what grounds a sentence any more: a name or an action has to be in the
    facts that sentence cited. They are what tells two failures apart, so a
    report can say "not in this passage at all" rather than "not in the facts
    you cited". Those are different mistakes and want different fixes.

    `set_piece` and `body_part` come off the goal shot itself. They are here
    because they are the two things a model invents most readily: a goal becomes
    a penalty, or a left foot becomes a header, and neither is visible in the
    run of play.
    """

    moment: Moment
    facts: tuple[Fact, ...]
    players: Mapping[str, str]
    teams: tuple[str, ...]
    actions: frozenset[str]
    set_piece: str | None
    body_part: str | None
    #: The two teams of the fixture, from `app/recorded_names.py`, or empty
    #: where the caller did not read them.
    #:
    #: `teams` above is read off the records of this passage, and the 2022
    #: counter is thirteen Argentina records with nothing of France's in it,
    #: so the side being attacked is not in the facts at all. A zone phrase
    #: says whose half the ball was in ("just inside France's half"), and
    #: `opponent` is where that name comes from. It defaults to empty so
    #: every caller that built facts before zones existed still builds them.
    recorded_teams: tuple[str, ...] = ()

    @property
    def beats(self) -> tuple[Beat, ...]:
        return tuple(fact.beat for fact in self.facts)

    @property
    def opponent(self) -> str | None:
        """The side being attacked, or `None` where nothing names it.

        The fixture's teams first, because they hold both sides whether or
        not the passage records one of them, and the passage's own teams
        after, so a caller that read no lineups file still gets England out
        of the 1986 records. `None` is what a zone phrase naming a team is
        read leniently against; `app/narration_grammar.py` says how.
        """
        for team in tuple(self.recorded_teams) + tuple(self.teams):
            if team != self.moment.team:
                return team
        return None

    @property
    def goal_fact(self) -> Fact:
        """The fact for the shot the moment was built from, which is the last."""
        return self.facts[-1]

    @property
    def goal_beat(self) -> Beat:
        return self.goal_fact.beat

    @property
    def play_patterns(self) -> frozenset[str]:
        """How the possessions in this passage started, by `play_pattern`.

        Both hero passages are "From Counter" throughout, which is what a goal
        call means by "Argentina were on the counter". It is a set rather than
        one value because a set-piece buildup reaches back a possession and the
        two can have started differently.
        """
        return frozenset(
            beat.play_pattern for beat in self.beats if beat.play_pattern
        )

    @property
    def seconds(self) -> float | None:
        """How long the passage took, first timestamp to last.

        Computed rather than recorded: StatsBomb carries a `duration` per
        record and no span for a possession, so the span is the difference
        between the two ends of it. `None` when a timestamp is missing, so a
        duration claim is refused rather than measured against a guess.

        A buildup never crosses a period boundary (`app/event_feed.py` says
        so), so subtracting two timestamps in one period is the whole of it.
        """
        stamps = [beat.seconds for beat in self.beats]
        if not stamps or any(stamp is None for stamp in stamps):
            return None
        return max(stamps) - min(stamps)


@dataclass(frozen=True)
class KeyBeat:
    """One beat of play a narration of this goal ought to reach.

    `numbers` holds every fact that records this beat, because a beat can be
    recorded twice and citing either one says it happened. `label` is how a
    report names the beat when a narration missed it.
    """

    kind: str
    numbers: tuple[int, ...]
    label: str

    def covered_by(self, cited) -> bool:
        cited = set(cited)
        return any(number in cited for number in self.numbers)


def key_beats(facts: Facts) -> tuple[KeyBeat, ...]:
    """The beats of a passage that a narration of it ought to reach.

    Three kinds, in the order they happened:

    * **The shot**, always, and always exactly one. It is the last fact.
    * **Every dribble past an opponent.** One beat per `Dribbled Past` record,
      which is the record naming the player who was beaten. The `Dribble` on
      the other player's record at the same clock joins the same beat, so
      citing either covers it. A `Dribble` with no `Dribbled Past` beside it is
      not a beat: it is a dribble that went past nobody.
    * **The foul, for a penalty.** Every foul record in the buildup, as one
      beat. A penalty has one foul, and each of the three penalty buildups in
      this data holds exactly one (`Foul Won` and `Foul Committed` are its two
      sides, and the 117:05 penalty has only the `Foul Committed` side), which
      is why they are merged rather than paired by clock.

    Two things use this and they have to agree, which is why it lives here
    rather than beside either of them. `template_narration` builds a fallback
    that reaches every one of these beats, and `scripts/narration_eval.py`
    measures what share of them a narration reached. A separate definition in
    the measuring script would eventually score the fallback against a rule
    the fallback was not built to.

    **What it cannot do.** Five of the nine goals in `data/raw/` have no
    dribble past an opponent and no penalty, so their only key beat is the
    shot, which `app/grounding.py` already requires the last sentence to cite.
    Coverage of those five says nothing, and the report prints the beat count
    beside the share so the two cases can be told apart.
    """
    beats: list[KeyBeat] = []

    by_clock: dict[tuple[int, int], list[Fact]] = {}
    for fact in facts.facts:
        by_clock.setdefault((fact.beat.minute, fact.beat.second), []).append(fact)

    for fact in facts.facts:
        if fact.beat.action != "Dribbled Past":
            continue
        clock = (fact.beat.minute, fact.beat.second)
        numbers = tuple(
            sorted(
                {fact.number}
                | {
                    other.number
                    for other in by_clock[clock]
                    if other.beat.action in DRIBBLE_TYPES
                }
            )
        )
        beats.append(
            KeyBeat(
                kind=DRIBBLE,
                numbers=numbers,
                label=f"dribbled past {fact.beat.name}",
            )
        )

    if facts.set_piece == PENALTY:
        fouls = tuple(
            fact.number for fact in facts.facts if fact.beat.action in FOUL_TYPES
        )
        if fouls:
            beats.append(
                KeyBeat(
                    kind=FOUL,
                    numbers=fouls,
                    label="the foul that won the penalty",
                )
            )

    goal = facts.goal_fact
    beats.append(
        KeyBeat(
            kind=SHOT,
            numbers=(goal.number,),
            label=f"the shot by {goal.beat.name}",
        )
    )
    return tuple(sorted(beats, key=lambda beat: min(beat.numbers)))


def _goal_shot(buildup: Buildup) -> RawEvent:
    """The goal shot in a buildup, which the contract puts last."""
    return buildup.events[-1]


def fact_text(beat: Beat) -> str:
    """One recorded event said plainly, with its clock.

    The phrasing comes from `EVENT_VERBS`, so a fact a model reads and the
    fallback narration say the same event the same way.

    The player is `Beat.name`, which is the recorded nickname where the
    lineups file records one. The facts are what a model writes its names out
    of, so this is what decides whether a narration says "Lionel Messi" or
    "Lionel Andrés Messi Cuccittini".
    """
    verb = EVENT_VERBS.get(beat.action)
    if verb is None:
        # Unreachable with the data in the repo, and a guess would be worse than
        # naming the type: a reader can look a type up, an invented verb points
        # at nothing.
        verb = f"is recorded with a {beat.action} event"
    return f"{beat.name} ({beat.team}) {verb}, {beat.clock}"


def _beat(event: RawEvent, nicknames: Mapping[str, str]) -> Beat:
    """One raw record as a `Beat`, every field copied and none derived.

    The three nested blocks a record can carry are read where they are: `pass`
    holds the recipient, the length, the assist flag and a body part, `shot`
    holds `first_time` and its own body part, and `carry` holds only an end
    location. A record with none of them keeps the defaults, which say the
    field was not recorded rather than that it was false.
    """
    passed = event.get("pass") or {}
    shot = event.get("shot") or {}
    carry = event.get("carry") or {}
    recipient = passed.get("recipient") or {}
    body_part = (passed.get("body_part") or shot.get("body_part") or {})
    end = (
        passed.get("end_location")
        or shot.get("end_location")
        or carry.get("end_location")
    )
    return Beat(
        index=event["index"],
        minute=event["minute"],
        second=event["second"],
        player=event["player"]["name"],
        team=event["team"]["name"],
        action=event["type"]["name"],
        event_id=event["id"],
        nickname=nicknames.get(event["player"]["name"]),
        timestamp=event.get("timestamp", ""),
        play_pattern=(event.get("play_pattern") or {}).get("name"),
        under_pressure=bool(event.get("under_pressure")),
        start=spot(event.get("location")),
        end=spot(end),
        recipient=recipient.get("name"),
        pass_length=passed.get("length"),
        goal_assist=bool(passed.get("goal_assist")),
        first_time=bool(shot.get("first_time")),
        body_part=body_part.get("name"),
    )


def facts_from_buildup(
    buildup: Buildup,
    nicknames: Mapping[str, str] | None = None,
    teams: Sequence[str] = (),
) -> Facts:
    """Read the facts a narration may use out of one buildup.

    Every value is copied from a raw record. Nothing is counted, ranked,
    summarised or inferred, because a fact this function invents is a fact the
    grounding check would then happily approve.

    `nicknames` maps a full recorded player name to the shorter name the
    lineups file records for them, from `app/recorded_names.py`. It is
    optional because the event feed alone cannot answer it, and a caller
    without the lineups file gets what every caller got before it was
    fetched: the full recorded name on every beat. A player the mapping does
    not hold keeps their full name too, which is not a gap to be filled by
    guessing at a surname.

    `teams` is the fixture's two team names, from the same file, for
    `Facts.opponent`. It is optional for the same reason and defaults to
    nothing, which leaves the opponent to the records of the passage.
    """
    short = nicknames or {}
    beats = tuple(_beat(event, short) for event in buildup.events
                  if event.get("player"))

    facts = tuple(
        Fact(number=number, beat=beat, text=fact_text(beat))
        for number, beat in enumerate(beats, start=1)
    )

    players: dict[str, str] = {}
    for beat in beats:
        players.setdefault(beat.player, beat.team)

    # Named for what it is rather than `teams`, which is the fixture's two
    # from the lineups file and arrives as an argument.
    recorded: list[str] = []
    for beat in beats:
        if beat.team not in recorded:
            recorded.append(beat.team)

    shot = _goal_shot(buildup)
    body_part = (shot.get("shot") or {}).get("body_part", {}).get("name")

    return Facts(
        moment=buildup.moment,
        facts=facts,
        players=players,
        teams=tuple(recorded),
        actions=frozenset(beat.action for beat in beats),
        set_piece=buildup.set_piece,
        body_part=body_part,
        recorded_teams=tuple(teams),
    )


def fact_list(facts: Facts) -> str:
    """The numbered facts, one per line, in the order they happened."""
    width = len(str(len(facts.facts)))
    return "\n".join(
        f"  {fact.number:>{width}}. {fact.text}" for fact in facts.facts
    )


def cited_line(fact: Fact) -> str:
    """One fact said plainly as a sentence that cites it.

    The citation comes first, which is the order the work happens in: pick a
    fact, read its number, then say it. The phrasing comes from the same
    `EVENT_VERBS` entry the fact itself was built with, so nothing is invented
    in the step from a numbered line to a cited sentence.

    Two callers: `build_prompt` shows a model the shape with it, and
    `template_narration` writes the fallback's sentences with it. One function,
    so the example a model is given and the narration written without one cannot
    drift apart.
    """
    verb = EVENT_VERBS.get(
        fact.beat.action, f"is recorded with a {fact.beat.action} event"
    )
    return f"[{fact.number}] {fact.beat.name} {verb}."


def beats_block(facts: Facts) -> str:
    """The key beats, named for the model, or empty when there are none.

    The measured run behind `docs/narration_eval.md` found that
    `granite4:micro` cited the shot and nothing else in all fourteen
    narrations it wrote for the goals where coverage can move: no dribble past
    a defender, no penalty foul. It passed the grounding check every time,
    because the check asks whether what a sentence says is true and not
    whether the narration got to the point. The facts were all in the prompt
    and the model took the first few in order and jumped to the goal.

    So the beats are named rather than left to be found. Each one is printed
    with the fact number to cite for it, which is the record the fallback uses
    too: the `Dribbled Past` for a dribble, naming the player who was beaten,
    and the `Foul Won` for a penalty foul where there is one.

    **It is empty for a goal whose only key beat is the shot**, which is five
    of the nine in `data/raw/`. Those prompts are unchanged by this block, and
    that is what makes it sound to compare a rerun of the other goals against
    the earlier numbers for them.

    Nothing here enforces anything. `app/grounding.py` is unchanged and still
    refuses on truth alone; coverage is reported, not required.
    """
    required = [beat for beat in key_beats(facts) if beat.kind != SHOT]
    if not required:
        return ""

    by_number = {fact.number: fact for fact in facts.facts}
    lines = []
    for beat in required:
        number = _beat_fact_number(beat, by_number)
        lines.append(f"  fact {number}: {by_number[number].text}")

    return (
        "\nTHE BEATS TO COVER\n"
        "These are the turning points of this passage. A narration that leaves\n"
        "one out has missed what happened, however true the rest of it is.\n"
        "Give each one its own sentence, in this order, before the last line,\n"
        "citing the fact number shown here:\n" + "\n".join(lines) + "\n"
    )


#: The actions that put the ball at a player's feet. A narration telling the
#: whole move names everyone who had a touch, and these are the records that
#: say somebody did.
#:
#: `Dribbled Past`, `Pressure` and `Duel` are deliberately not here. Being
#: beaten, closing a player down or contesting a ball is not a touch, and the
#: defenders those records name reach the narration through `key_beats`
#: instead, which is where a dribble past an opponent is already required.
TOUCH_ACTIONS = frozenset(
    {
        "Ball Recovery",
        "Pass",
        "Ball Receipt*",
        "Carry",
        "Dribble",
        "Clearance",
        "Block",
        "Interception",
        "Goal Keeper",
        "Miscontrol",
        "Shot",
    }
)


@dataclass(frozen=True)
class MoveStep:
    """One step of the move: a player, and the facts recording their touches.

    `numbers` holds the consecutive touch facts this player had in one turn on
    the ball, so receiving, carrying and passing is one step rather than three.
    """

    player: str
    numbers: tuple[int, ...]


def move_steps(facts: Facts) -> tuple[MoveStep, ...]:
    """The passage as steps, in order, one per turn on the ball.

    A step is a run of consecutive touch records by one player. A fact that is
    not a touch ends the run, which is what keeps the 1986 goal honest: the
    scorer's touches either side of a `Dribbled Past` are two steps of the
    move and not one, because beating a defender happened between them. So
    that passage comes out as the two passes into it and then one step per
    defender beaten, which is the shape a listener would recognise.

    The goal shot is always the last step on its own, whoever touched the ball
    before it, because the narration ends on the goal.

    This is what the hero prompt counts sentences from. It is not a new source
    of truth: every number in it is a fact number, and every fact is one
    record in `data/raw/`.
    """
    goal = facts.goal_fact
    steps: list[MoveStep] = []
    previous: str | None = None
    for fact in facts.facts:
        if fact.number == goal.number:
            continue
        if fact.beat.action not in TOUCH_ACTIONS:
            previous = None
            continue
        if steps and previous == fact.beat.player:
            steps[-1] = MoveStep(
                steps[-1].player, steps[-1].numbers + (fact.number,)
            )
        else:
            steps.append(MoveStep(fact.beat.player, (fact.number,)))
        previous = fact.beat.player
    steps.append(MoveStep(goal.beat.player, (goal.number,)))
    return tuple(steps)


def touched_the_ball(facts: Facts) -> tuple[str, ...]:
    """Every player with a recorded touch, in the order of their first one.

    Named once each, however many touches they had, because this is the list
    the hero prompt asks a narration to name in full.

    These are the full recorded names, which is the identity a player is
    counted under. What a narration calls them is `Beat.name`, and
    `spoken_names` is that list for printing.
    """
    seen: list[str] = []
    for step in move_steps(facts):
        if step.player not in seen:
            seen.append(step.player)
    return tuple(seen)


def spoken_names(facts: Facts) -> Mapping[str, str]:
    """Full recorded name to the name a narration calls that player by.

    `Beat.name` answers it one beat at a time; this is the whole passage, for
    the places that hold a recorded name and have to print the spoken one.
    """
    return {fact.beat.player: fact.beat.name for fact in facts.facts}


def hero_block(facts: Facts) -> str:
    """The move printed as ordered steps, for the prompt that gets recorded.

    **Why the hero prompt gets this and the others do not.** The frozen
    narrations from Task 6 were grounded and thin: the 2022 one named three of
    the five players who touched the ball and left out Messi and Álvarez, who
    are both on the moment card, and the 1986 one did not name the scorer until
    its last line. Nothing in `app/grounding.py` was wrong about either. The
    check asks whether what a sentence says is true, not whether the narration
    told the move, so fullness is a thing to ask for in the prompt or not to
    get at all.

    So the steps are named rather than left to be found, the same way
    `beats_block` names the turning points. The two blocks overlap on purpose
    where a step is also a dribble past an opponent: one says this is a step of
    the move, the other says this is a turning point, and a narration that
    takes them both in order has told the passage end to end.

    Nothing here enforces anything. `app/grounding.py` is unchanged and still
    refuses on truth alone.
    """
    steps = move_steps(facts)
    spoken = spoken_names(facts)
    players = [spoken[player] for player in touched_the_ball(facts)]
    by_number = {fact.number: fact for fact in facts.facts}
    # The dribble beats, by the facts that record them, so a step that beat a
    # defender can be printed as that rather than as its own verbs. The live
    # run of 2026-10-30 is why: three of the five 1986 candidate slots failed
    # all three attempts the same way, writing "Peter Beardsley was dribbled
    # past and Diego Armando Maradona carried the ball" from a step printed as
    # "dribbled, carried the ball" beside a beat naming Beardsley. The check
    # refuses that, correctly, because no cited fact pairs Beardsley with a
    # Carry. Printing the step as the dribble past him names one action and
    # both players, which is the shape the one candidate that passed wrote.
    dribbles = [beat for beat in key_beats(facts) if beat.kind == DRIBBLE]
    lines = []
    for index, step in enumerate(steps, start=1):
        beaten = next(
            (
                beat
                for beat in dribbles
                if set(beat.numbers) & set(step.numbers)
            ),
            None,
        )
        if beaten is not None:
            numbers = tuple(sorted(set(step.numbers) | set(beaten.numbers)))
            said = beaten.label
        else:
            numbers = step.numbers
            # The verbs, so a step says what happened in it and not only who
            # had the ball. Without them the 1986 list reads as one name over
            # and over.
            said = ", ".join(
                EVENT_VERBS.get(
                    by_number[number].beat.action,
                    by_number[number].beat.action,
                )
                for number in numbers
            )
        printed = ", ".join(str(number) for number in numbers)
        plural = "facts" if len(numbers) > 1 else "fact"
        last = " (the goal)" if index == len(steps) else ""
        lines.append(
            f"  {index}. {spoken[step.player]}, from {plural} {printed}: "
            f"{said}{last}"
        )
    beat_note = (
        " A step that says \"dribbled past\" is one sentence about that one"
        " action, naming the player who beat the defender and the defender"
        " who was beaten. The carry recorded beside it does not need a"
        " sentence of its own."
        if dribbles
        else ""
    )
    return (
        "\nTHE WHOLE MOVE\n"
        + _wrapped(
            "This narration is the one that gets recorded, so it tells the"
            " move end to end and not a few steps of it. Take the steps in"
            " this order, one sentence each, citing the fact numbers shown:"
        )
        + "\n"
        + "\n".join(lines)
        + "\n"
        + _wrapped(
            "Every player in that list touched the ball, and the narration"
            " names every one of them: " + ", ".join(players) + "."
            + beat_note
        )
        + "\n"
    )


def style_block() -> str:
    """The one style every narration is written in, printed for the model.

    It is `NARRATION_STYLE`, wrapped, and it does not depend on the persona:
    three measured runs found no register reaching a model through this block,
    so the block says one thing and `app/personas.py` carries the sound
    instead. The constant is where the style is argued about and this function
    does not paraphrase it.
    """
    return "\nTHE STYLE\n" + _wrapped(NARRATION_STYLE) + "\n"


def _wrapped(text: str, indent: str = "") -> str:
    """One paragraph, hard wrapped the way the rest of the prompt is written.

    The prompt is a document somebody reads while working out why a narration
    was refused, and a style paragraph arriving as one four hundred character
    line is the only part of it that would not be. Nothing about the wrapping
    is load bearing; a model reads either.
    """
    return textwrap.fill(
        " ".join(text.split()),
        width=76,
        initial_indent=indent,
        subsequent_indent=indent,
    )


def _rule(number: int, *paragraphs: str) -> str:
    """One numbered rule, wrapped the way the rest of the prompt is written.

    The rules used to be written out inside the prompt string, already wrapped
    by hand, which was fine while every one of them was a constant. Three of
    them read differently for the recording, and a clause substituted into
    hand-wrapped text leaves one line running past the margin and the rest
    short. So the rules carry their words and this carries their shape.

    Several paragraphs stay several paragraphs, indented under the number.
    Nothing about the wrapping is load bearing; a model reads either.
    """
    head = f"{number}. "
    indent = " " * len(head)
    return "\n".join(
        textwrap.fill(
            " ".join(paragraph.split()),
            width=76,
            initial_indent=head if index == 0 else indent,
            subsequent_indent=indent,
        )
        for index, paragraph in enumerate(paragraphs)
    )


def rules_block(
    facts: Facts,
    sentences: int,
    hero: bool = False,
    target_characters: int | None = None,
) -> str:
    """The numbered rules, which are the rules `app/grounding.py` enforces.

    **Three of them read differently for the recording, and all three ask for
    less than the check allows.** That is the safe direction, and the reason it
    is safe is written down in `tests/test_grounding.py::TestTheHeroShape`: the
    check accepts a sentence with no clock and a goal sentence that says it
    scored, so neither hero rule needed a rule in the check bent to allow it.
    A prompt asking for more than the check enforces costs nothing; one asking
    for less sets the model up to fail, and the retry does not help it.

    Rule 2 gains the goal sentence saying it scored. The frozen narrations
    from Task 6 ended on "shot" and never said the ball went in, which is
    grounded (the check's ending rule is that the last sentence cites the
    goal's own shot fact) and is not what a listener needs to hear last.

    Rule 6 goes from a clock per cited fact to one clock on the first line.
    Both frozen narrations put a clock on every sentence, which is true of
    each sentence and reads as a log.

    Rule 8 has to be said more carefully once rule 2 asks for "scored", or the
    two contradict each other: the scoreline is still out, and the goal going
    in is still in. Nothing about what the goal meant for the match becomes
    sayable.
    """
    goal = facts.goal_fact

    scored = (
        " It says the shot scored: the fact it cites is the shot that went"
        " in, so the last sentence says so."
        if hero
        else ""
    )
    clock = (
        "Give the clock once, on the first line, and on no other line. Write"
        " it exactly as the fact that line cites writes it, digits and colon,"
        " so {} and not any other way. Do not write the time in words"
        " anywhere: no \"minute fifty-four\", no \"seconds two\", no clock"
        " spelled out. A clock on every sentence is true of every sentence"
        " and reads as a log rather than as a passage of play; a listener"
        " needs telling once when this happened. Write any count as a word,"
        " not a digit: \"past two defenders\", never \"past 2"
        " defenders\".".format(facts.facts[0].beat.clock)
        if hero
        else "A clock is written exactly as the fact you cite writes it, so a"
        " clock belongs only to a line citing the fact it was printed on."
        " Write any count as a word, not a digit: \"past two defenders\","
        " never \"past 2 defenders\". The only other digits allowed are the"
        " minute of a cited fact and the second the goal was scored at."
    )
    outcome = (
        "Say nothing about the scoreline, the result, or what the goal meant"
        " for the match. Saying the shot scored is rule 2 and is required;"
        " saying what it made the score is not. What you have is one passage"
        " of play, and it does not say who won. \"won a foul\" is fine,"
        " because the facts record one; \"won the match\" is not."
        if hero
        else "Say nothing about the score, the result, or what the goal meant"
        " for the match. What you have is one passage of play, and it does"
        " not say who won. \"won a foul\" is fine, because the facts record"
        " one; \"won the match\" is not."
    )
    per_step = (
        " One for each step of the move above, in that order." if hero else ""
    )
    # The length, which is a price rather than a style: three recordings a
    # match and a monthly allowance pays for them.
    if hero and target_characters:
        words = round(target_characters / CHARACTERS_PER_WORD)
        length = (
            " Aim at about {} characters in all, which is roughly {} words."
            " This narration gets recorded and a monthly character allowance"
            " pays for it, so a shorter telling of the whole move is better"
            " than a longer one. Do not drop a step to get there: say each"
            " one plainly instead.".format(target_characters, words)
        )
    else:
        length = ""

    return "\n".join(
        (
            _rule(
                1,
                "Write in the past tense, as the facts above are written."
                " This passage has already happened and you are telling a fan"
                " what they missed, so \"dribbled\", not \"dribbles\";"
                " \"shot\", not \"shoots\"; \"was dribbled past\", not \"is"
                " dribbled past\". A line in the present tense is rejected.",
            ),
            _rule(
                2,
                f"The last line is about the goal and cites fact"
                f" {goal.number}.{scored} Nothing follows it: no summary, no"
                " comment, no sentence addressed to the reader. The narration"
                " stops on the goal.",
                "Write about the players, never to the listener and never as"
                " one of the teams: \"you\", \"your\", \"we\", \"our\" and"
                " \"us\" are all rejected.",
            ),
            _rule(
                3,
                "Every name, action and clock in a sentence has to come from a"
                " fact that line cites, and a name has to sit in the same fact"
                " as the action you give it. \"dribbled past a defender\" needs"
                " one cited fact that records a dribble by or against that"
                " defender; if no single fact pairs them, the line is rejected"
                " even though both words appear somewhere in the list. A real"
                " player who is not in this passage is rejected like an"
                " invented one.",
            ),
            _rule(
                4,
                "Give each line one action, so every name in it belongs to"
                " that action. Two players doing two different things are two"
                " lines.",
            ),
            _rule(
                5,
                "Do not say the goal was a penalty, a free kick or a corner"
                " unless the shot type above says so. Do not name a body part"
                " other than the one above.",
            ),
            _rule(6, clock),
            _rule(
                7,
                "No nicknames and no verdicts for the goal, the players or the"
                " match. Say what the data records, not how good it was. Words"
                " like \"decisive\", \"brilliant\" and \"significant\" are"
                " rejected.",
            ),
            _rule(8, outcome),
            _rule(
                9,
                "No em dashes. Use a colon, a semicolon, parentheses or two"
                " sentences.",
            ),
            _rule(
                10,
                f"Write {sentences} sentences of plain past-tense commentary,"
                f" one per line.{per_step}{length} Output those lines only,"
                " with no preamble, heading or explanation.",
            ),
        )
    )


def build_prompt(
    facts: Facts,
    sentences: int = DEFAULT_SENTENCES,
    beats: bool = True,
    hero: bool = False,
    target_characters: int | None = None,
) -> str:
    """The prompt for one goal.

    **There is one prompt, whoever is listening.** It took no persona until
    Task 6b and takes none again: `NARRATION_STYLE` is the style it asks for
    in every voice, and the persona a listener picked changes the audio in
    Phase 5 rather than the words. Tasks 6c, 4b and 6d measured three ways of
    asking three models for three registers through this prompt and got one
    register back each time; `docs/narration_eval.md` holds the numbers.

    So the first person is refused here in every voice, the Buddy included.
    `app/grounding.py` still admits "we" from a partisan persona over that
    side's facts, which is a guard behind a prompt that asks for less than the
    check allows rather than a permission anything reaches for. A prompt
    asking for *more* than the check enforces costs nothing; one asking for
    less sets the model up to fail, and the retry does not help it.

    The rules in it are the rules `app/grounding.py` enforces afterwards, said
    plainly. A prompt that asked for less than the check requires would set the
    model up to fail, and the retry would not help it.

    Rule 1 is the voice: a buildup is playback of a passage that already
    happened, so it is told in the past tense. Rule 2 is where the narration
    stops. There is no closing line addressed to the fan, because the moment
    the goal lands the stadium takes over and the app has nothing to add;
    `docs/VOICE.md` carries that reasoning.

    Rule 4 is the one that exists for the check's sake rather than the voice's.
    The check pairs every name in a sentence with every action in it, because
    nothing in the text says which name goes with which action, so a sentence
    about one action is a sentence the check can read exactly.

    **The citation comes first on the line, and that is the shape live runs
    settled.** Three layouts were tried against `granite4:micro`. Asking for the
    tag at the end of the sentence, with the goal as the worked example, got the
    goal's number on all four sentences, the model having read the example as
    the answer. Adding a procedure and a no-shared-numbers rule to the same
    layout got sentences with no tag at all, which is the harder failure: a
    model that has written the sentence has nothing left to look up. Asking for
    the number first, as `WRITE IT LIKE THIS`, got a tag on every line and a
    grounded first attempt. The order matches the work: pick a fact, read its
    number, then say it.
    """
    moment = facts.moment
    set_piece = facts.set_piece or "Open Play"
    body_part = facts.body_part or "not recorded"
    first, goal = facts.facts[0], facts.goal_fact

    # One sentence per key beat plus the goal sentence, or the count asked
    # for, whichever is larger. A prompt that asked for four sentences and
    # then named five beats to cover would contradict itself, and the model
    # would have to drop one of the two instructions to obey the other.
    block = beats_block(facts) if beats else ""
    move = move_steps(facts) if hero else ()
    hero_text = hero_block(facts) if hero else ""
    style = style_block()
    # A prompt that names no beats asks for no sentence per beat either, so
    # the count stays where the caller put it. Raising it for beats the model
    # was never shown would ask for sentences with nothing to fill them.
    covered = (
        len([b for b in key_beats(facts) if b.kind != SHOT]) if beats else 0
    )
    sentences = max(sentences, covered + 1)
    # The hero prompt asks for the whole move, so it needs a line per step of
    # it rather than the four a shorter telling fits into. The steps already
    # include the dribbles past a defender, so this is not added to `covered`:
    # it is the other floor, and the larger of the two wins.
    sentences = max(sentences, len(move))
    # The target applies to the recording and nowhere else, so it is the
    # hero default rather than a default of the prompt.
    target = target_characters
    if hero and target is None:
        target = HERO_TARGET_CHARACTERS
    rules = rules_block(
        facts, sentences, hero=hero, target_characters=target
    )

    return f"""You are writing the narration for one goal in a football match.
The app this is for says only what the match data proves, so you may use the
facts below and nothing else. Anything you add from memory will be rejected.

THE GOAL
  Team:       {moment.team}
  Scorer:     {facts.goal_beat.name}
  Clock:      minute {moment.minute}, second {moment.second}
  Shot type:  {set_piece}
  Body part:  {body_part}

THE FACTS
One numbered line per recorded event, in the order it happened. Nothing
happened that is not here.
{fact_list(facts)}
{block}{hero_text}{style}
WRITE IT LIKE THIS
Write {sentences} lines. Each line starts with the numbers of the facts it is
about, in square brackets, and then says them in one sentence:

  {cited_line(first)}
  {cited_line(goal)}

Pick a fact, read the number at the start of its line, write the bracket, then
write the sentence. Never write a number you have not read off a line, and do
not put the same number on every line.

RULES
{rules}
"""


def template_narration(facts: Facts) -> str:
    """A short, plain narration assembled from the facts, with no model.

    This is the fallback for when a model cannot stay inside the data. It is
    grounded by construction: every name, clock and action in it is copied out
    of one fact, and each sentence cites that fact. It reads plainly rather than
    well, which is the trade being made, and it writes each player's name as
    the facts write it: the recorded nickname where the lineups file records
    one, and the full recorded name where it records none. Both are the data's
    own spellings, so the fallback still introduces no judgement call about
    what a player is called.

    One sentence per fact is also what keeps it inside the pairing rule: a
    sentence that cites one fact and names one player cannot pair a name with an
    action that fact does not record.

    The layout is the one `build_prompt` asks a model for, citation first, so
    narration has one shape in this repo whether a model wrote it or not. It
    ends on the goal, citing the shot the moment was built from, which is the
    last thing the narration says.

    **It reaches every key beat.** Grounded is not the same as complete, and
    the fallback used to be only the first. It collapsed a run of the same
    player doing the same thing into one sentence, so Maradona's four dribbles
    became one, and then trimmed the run-up from the front to fit a sentence
    budget, which could drop that one too. The result said nothing false and
    left out the reason the goal is remembered. A fallback assembled by code
    out of the facts has no excuse for that: it can see every beat.

    So `key_beats` is consulted first and every beat it names gets a sentence,
    before any other fact is considered. A dribble beat is said with its
    `Dribbled Past` record, which is the one naming the player who was beaten;
    a foul beat with its `Foul Won` record where there is one, because the
    side that won it is the side the narration is about, and otherwise with
    the `Foul Committed` record that the 117:05 penalty records it as.

    `TEMPLATE_MAX_SENTENCES` is a target rather than a ceiling now: the other
    facts fill the narration up to it, and a passage with more key beats than
    that runs longer rather than dropping one.
    """
    goal = facts.goal_fact
    beats = key_beats(facts)
    by_number = {fact.number: fact for fact in facts.facts}

    # Every key beat but the shot, which has its own closing sentence. One
    # fact per beat: the record that names the player the beat is about.
    required: list[Fact] = []
    for beat in beats:
        if beat.kind == SHOT:
            continue
        required.append(by_number[_beat_fact_number(beat, by_number)])

    spoken = {fact.number for fact in required} | {goal.number}
    # A beat is said once, whichever of its records was chosen for it.
    covered = {number for beat in beats for number in beat.numbers}

    candidates = [
        fact
        for fact in facts.facts[:-1]
        if fact.beat.action in TEMPLATE_KEY_ACTIONS
        and fact.beat.action in EVENT_VERBS
        and fact.number not in covered
    ]

    # A run of the same player doing the same thing would read as the same
    # sentence over and over. Collapsing it loses no fact: the events are still
    # what the label points at. Key beats are already out of this list, so the
    # collapse can no longer swallow one.
    filler: list[Fact] = []
    for fact in candidates:
        if filler and (fact.beat.player, fact.beat.action) == (
            filler[-1].beat.player,
            filler[-1].beat.action,
        ):
            continue
        filler.append(fact)

    # The minute line and the goal line are two of the budget, and the key
    # beats are not negotiable. Whatever is left over is filled from the front
    # of the run-up being trimmed, so the sentences nearest the goal survive.
    room = max(TEMPLATE_MAX_SENTENCES - 2 - len(required), 0)
    filler = filler[-room:] if room else []

    middle = sorted(required + filler, key=lambda fact: fact.number)

    lines = [f"[{goal.number}] Minute {goal.beat.minute}."]
    lines += [cited_line(fact) for fact in middle]
    lines.append(
        f"[{goal.number}] {goal.beat.name} shot and scored for "
        f"{goal.beat.team}."
    )
    return "\n".join(lines)


def beat_record(beat: KeyBeat, by_number: Mapping[int, Fact]) -> Fact:
    """The record a key beat is about, which is the one naming its player.

    A dribble beat holds two records and only one of them names the defender
    who was beaten, so "did the narration reach this beat" is a question about
    that record rather than about either. `scripts/narrator_candidates.py`
    asks it, and the fallback asks the same thing a line lower down.
    """
    return by_number[_beat_fact_number(beat, by_number)]


def _beat_fact_number(beat: KeyBeat, by_number: Mapping[int, Fact]) -> int:
    """Which of a beat's records the fallback says it with.

    A dribble beat is said with the `Dribbled Past`, which names the player who
    was beaten rather than only that someone went past somebody. A foul beat
    prefers the `Foul Won`, which names the side the penalty was given to, and
    falls back to the `Foul Committed` for the 117:05 penalty, which has no
    `Foul Won` record at all.
    """
    preferred = {DRIBBLE: "Dribbled Past", FOUL: "Foul Won"}.get(beat.kind)
    for number in beat.numbers:
        if by_number[number].beat.action == preferred:
            return number
    return beat.numbers[0]
