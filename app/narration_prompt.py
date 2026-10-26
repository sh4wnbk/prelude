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

Standard library only, like the rest of `app/`.
"""

from dataclasses import dataclass
from typing import Mapping

from app.event_feed import Buildup, Moment, RawEvent

#: How a StatsBomb event type is said in a fact and in the fallback narration.
#: Every type that occurs in a buildup across the two matches in `data/raw/` is
#: here; a type with no entry falls back to naming the type itself rather than
#: being guessed at, and `tests/test_narration_prompt.py` checks that fallback
#: is unreachable with the data in the repo.
EVENT_VERBS: Mapping[str, str] = {
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

    @property
    def beats(self) -> tuple[Beat, ...]:
        return tuple(fact.beat for fact in self.facts)

    @property
    def goal_fact(self) -> Fact:
        """The fact for the shot the moment was built from, which is the last."""
        return self.facts[-1]

    @property
    def goal_beat(self) -> Beat:
        return self.goal_fact.beat


def _goal_shot(buildup: Buildup) -> RawEvent:
    """The goal shot in a buildup, which the contract puts last."""
    return buildup.events[-1]


def fact_text(beat: Beat) -> str:
    """One recorded event said plainly, with its clock.

    The phrasing comes from `EVENT_VERBS`, so a fact a model reads and the
    fallback narration say the same event the same way.
    """
    verb = EVENT_VERBS.get(beat.action)
    if verb is None:
        # Unreachable with the data in the repo, and a guess would be worse than
        # naming the type: a reader can look a type up, an invented verb points
        # at nothing.
        verb = f"is recorded with a {beat.action} event"
    return f"{beat.player} ({beat.team}) {verb}, {beat.clock}"


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

    facts = tuple(
        Fact(number=number, beat=beat, text=fact_text(beat))
        for number, beat in enumerate(beats, start=1)
    )

    players: dict[str, str] = {}
    for beat in beats:
        players.setdefault(beat.player, beat.team)

    teams: list[str] = []
    for beat in beats:
        if beat.team not in teams:
            teams.append(beat.team)

    shot = _goal_shot(buildup)
    body_part = (shot.get("shot") or {}).get("body_part", {}).get("name")

    return Facts(
        moment=buildup.moment,
        facts=facts,
        players=players,
        teams=tuple(teams),
        actions=frozenset(beat.action for beat in beats),
        set_piece=buildup.set_piece,
        body_part=body_part,
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
    return f"[{fact.number}] {fact.beat.player} {verb}."


def build_prompt(facts: Facts, sentences: int = DEFAULT_SENTENCES) -> str:
    """The prompt for one goal.

    The rules in it are the rules `app/grounding.py` enforces afterwards, said
    plainly. A prompt that asked for less than the check requires would set the
    model up to fail, and the retry would not help it.

    Rule 2 is the one that exists for the check's sake rather than the voice's.
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

    return f"""You are writing the narration for one goal in a football match.
The app this is for says only what the match data proves, so you may use the
facts below and nothing else. Anything you add from memory will be rejected.

THE GOAL
  Team:       {moment.team}
  Scorer:     {moment.player}
  Clock:      minute {moment.minute}, second {moment.second}
  Shot type:  {set_piece}
  Body part:  {body_part}

THE FACTS
One numbered line per recorded event, in the order it happened. Nothing
happened that is not here.
{fact_list(facts)}

WRITE IT LIKE THIS
Write {sentences} lines. Each line starts with the numbers of the facts it is
about, in square brackets, and then says them in one sentence:

  {cited_line(first)}
  {cited_line(goal)}

Pick a fact, read the number at the start of its line, write the bracket, then
write the sentence. Never write a number you have not read off a line, and do
not put the same number on every line.

RULES
1. Every name, action and clock in a sentence has to come from a fact that line
   cites, and a name has to sit in the same fact as the action you give it.
   "dribbles past a defender" needs one cited fact that records a dribble by or
   against that defender; if no single fact pairs them, the line is rejected
   even though both words appear somewhere in the list. A real player who is
   not in this passage is rejected like an invented one.
2. Give each line one action, so every name in it belongs to that action. Two
   players doing two different things are two lines.
3. Do not say the goal was a penalty, a free kick or a corner unless the shot
   type above says so. Do not name a body part other than the one above.
4. A clock is written exactly as the fact you cite writes it, so a clock
   belongs only to a line citing the fact it was printed on. Write any count as
   a word, not a digit: "past two defenders", never "past 2 defenders". The
   only other digits allowed are the minute of a cited fact and the second the
   goal was scored at.
5. No nicknames and no verdicts for the goal, the players or the match. Say
   what the data records, not how good it was. Words like "decisive",
   "brilliant" and "significant" are rejected.
6. Say nothing about the score, the result, or what the goal meant for the
   match. What you have is one passage of play, and it does not say who won.
7. No em dashes. Use a colon, a semicolon, parentheses or two sentences.
8. Write {sentences} sentences of plain, present-tense commentary, one per line.
   Output those lines only, with no preamble, heading or explanation.
"""


def template_narration(facts: Facts) -> str:
    """A short, plain narration assembled from the facts, with no model.

    This is the fallback for when a model cannot stay inside the data. It is
    grounded by construction: every name, clock and action in it is copied out
    of one fact, and each sentence cites that fact. It reads plainly rather than
    well, which is the trade being made, and it uses the full recorded player
    names rather than shortening them, because a fallback should not be the
    thing that introduces a judgement call about what a player is called.

    One sentence per fact is also what keeps it inside the pairing rule: a
    sentence that cites one fact and names one player cannot pair a name with an
    action that fact does not record.

    The layout is the one `build_prompt` asks a model for, citation first, so
    narration has one shape in this repo whether a model wrote it or not.
    """
    goal = facts.goal_fact
    candidates = [
        fact
        for fact in facts.facts[:-1]
        if fact.beat.action in TEMPLATE_KEY_ACTIONS
        and fact.beat.action in EVENT_VERBS
    ]

    # A run like Maradona's is four separate Dribble events, which would read as
    # the same sentence four times over. Collapsing a run of the same player
    # doing the same thing loses no fact: the events are still what the label
    # points at, and the sentence still describes them.
    chosen: list[Fact] = []
    for fact in candidates:
        if chosen and (fact.beat.player, fact.beat.action) == (
            chosen[-1].beat.player,
            chosen[-1].beat.action,
        ):
            continue
        chosen.append(fact)

    # The goal is the point of the narration, so it keeps its place and the
    # run-up is trimmed from the front to fit around it.
    room = max(TEMPLATE_MAX_SENTENCES - 2, 0)
    chosen = chosen[-room:] if room else []

    lines = [f"[{goal.number}] Minute {goal.beat.minute}."]
    lines += [cited_line(fact) for fact in chosen]
    lines.append(
        f"[{goal.number}] {goal.beat.player} shoots and scores for "
        f"{goal.beat.team}."
    )
    return "\n".join(lines)
