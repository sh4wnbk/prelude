"""The prompt for a goal call: the move, the narrator's style, and the rules.

`app/narration_prompt.py` builds the prompt the cited reading is written from:
numbered facts, a citation on every line, a clock on the first one. The
framework in `docs/VOICE.md` asks for something else. A Prelude narration is
the recap stage of a goal call, it cites nothing, it carries no clock, and
**each narrator has its own text**: a Storyteller recapping a move and a Buddy
sitting beside a fan whose side just scored are not the same sentences spoken
differently.

So this module builds that prompt instead, one per narrator and situation. Four
of them, which are the four `app/delivery.py` already keys its table by:

| Key | Who is listening |
| --- | ---------------- |
| `storyteller_neutral` | anybody; the move told evenly, in the third person |
| `buddy_scored` | a fan of the side that scored, so "we" and the one cheer |
| `buddy_conceded` | a fan of the side that conceded: the same move, no cheering |
| `caller_neutral` | anybody; quick, chained, clipped |

**The style is shown through an invented match and never through a real one.**
`tests/test_reference_narrations.py` holds eight reference narrations of the
two hero goals, and they are the standard rather than the material: a reference
pasted into the prompt for the goal it describes is dictation, the model hands
it back, the check passes it and nothing has been measured. So the worked
example below is Harbour Town against Kestrel Bay, whose players do not exist,
and whose goal is a different shape from either real one: one recovery, two
passes with a long ball among them, one defender beaten, and a right-footed
finish. What the example teaches is the devices, not the sentence.

**What the model is shown about the move is read off the records.** The steps
come from `move_steps` and `key_beats` in `app/narration_prompt.py`, the same
two functions the cited prompt uses, and the extra fields on each line are the
ones Task 9b step 1 put on `Beat`: the pass recipient, the assist, the long
ball, the pressure, the first-time finish, the body part and the two field
positions. Nothing here is inferred.

**The rules ask for no less than `app/grounding.py` enforces.** A prompt asking
for more than the check requires costs nothing; one asking for less sets the
model up to fail, and the retry does not help it. Two of them are worth saying
twice:

* **The names that fit two players are printed.** "Terry" is Butcher and
  Fenwick and "Peter" is Beardsley, Reid and Shilton, so the goal-call grammar
  refuses both, and a model that has not been told cannot know. The list is
  computed from the recorded names rather than written down.
* **No clock and no digit.** The header already says when the goal came, and a
  colon between two numbers is read aloud as a colon between two numbers.

Standard library only, like the rest of `app/`.
"""

import textwrap
from dataclasses import dataclass
from typing import Mapping, Sequence

from app.narration_grammar import NUMBER_WORDS, fold, name_keys
from app.narration_prompt import (
    DRIBBLE,
    EVENT_VERBS,
    Facts,
    key_beats,
    move_steps,
    spoken_names,
    touched_the_ball,
)

#: The keys, which are `app/delivery.py`'s and `hero.voice_for`'s in
#: `app/web/matches.json`. A fifth combination does not exist: the Buddy is
#: `fans_only`, so there is no neutral Buddy to write a style for.
STORYTELLER_NEUTRAL = "storyteller_neutral"
BUDDY_SCORED = "buddy_scored"
BUDDY_CONCEDED = "buddy_conceded"
CALLER_NEUTRAL = "caller_neutral"

#: Characters a goal call comes to, measured off the eight references in
#: `tests/test_reference_narrations.py`: they run 202 to 269 characters and
#: average 232, in 37 to 51 words averaging 42. So the target is 230, and
#: 5.5 characters a word is what converts it into the word count the prompt
#: also states, because a model counts words rather better than characters.
#:
#: It is shorter than `HERO_TARGET_CHARACTERS`, which is 450 and was measured
#: off the cited narrations. A goal call says the same move in fewer words
#: because it joins its clauses instead of giving each step a sentence.
GOAL_CALL_TARGET_CHARACTERS = 230
GOAL_CALL_CHARACTERS_PER_WORD = 5.5


@dataclass(frozen=True)
class NarratorStyle:
    """One narrator and situation: how its text reads, and one worked example.

    `style` is what this narrator does that the others do not. `example` is the
    invented goal told in that voice, and it is the only example the prompt
    carries: `docs/VOICE.md` settles that the references are the standard and
    never the material.
    """

    key: str
    label: str
    style: str
    example: str


#: The invented match the styles are shown through. It is not a real fixture,
#: the five players are not real people, and the goal is a shape neither hero
#: goal has: a recovery, a pass, a defender beaten, a long ball, and a
#: right-footed finish from inside the box.
#:
#: Invented on purpose and said so on purpose. A made-up match in a prompt
#: that otherwise insists on the records is the one place a model could be
#: forgiven for thinking invention is allowed, so the block says what it is
#: and the rule after it says the move below is the only one to tell.
INVENTED_MATCH = (
    "Kestrel Bay are the side that scored. Five players: Odili, Brandt, "
    "Vance, and Marrow and the goalkeeper Oyelaran, who defend for Harbour "
    "Town. Odili won the ball back in his own half and passed to Brandt. "
    "Brandt carried it forward under pressure, went past Marrow, and played a "
    "long ball forward to Vance. Vance carried it into the box, went around "
    "Oyelaran, and scored with his right foot."
)

STYLES: Mapping[str, NarratorStyle] = {
    STORYTELLER_NEUTRAL: NarratorStyle(
        key=STORYTELLER_NEUTRAL,
        label="the Storyteller, to a listener with no side",
        style=(
            "Tell the move evenly, start to finish, in the third person. This"
            " is the calm one: the clauses join and carry the listener"
            " through, and the plainness is the register. Nobody is cheered"
            " for and nobody is cheered at, so there is no exclamation mark"
            " anywhere, and no \"we\": this listener supports neither side."
        ),
        example=(
            "Odili won it back in his own half and gave it to Brandt, who "
            "carried it forward under pressure past Marrow and hit a long "
            "ball to Vance, who took it into the box, went around Oyelaran "
            "and scored with his right foot."
        ),
    ),
    BUDDY_SCORED: NarratorStyle(
        key=BUDDY_SCORED,
        label="the Buddy, to a fan of the side that scored",
        style=(
            "You are in the next seat, and the move is the listener's own, so"
            " it is \"we\" and \"us\" where the side that scored did"
            " something: \"we won it back through Odili\". Warmer and looser"
            " than the Storyteller, and it builds: the finish is the one"
            " place a listener cheers, so the last sentence, and only the"
            " last sentence, ends on an exclamation mark."
        ),
        example=(
            "We won it back through Odili, and Brandt took it past Marrow and "
            "sent a long ball forward to Vance, who carried it into the box, "
            "got around Oyelaran and scored with his right foot!"
        ),
    ),
    BUDDY_CONCEDED: NarratorStyle(
        key=BUDDY_CONCEDED,
        label="the Buddy, to a fan of the side that conceded",
        style=(
            "The same seat and the same move, told to somebody whose side"
            " just conceded it. So no cheering: no exclamation mark anywhere,"
            " and nothing that admires the goal. And no \"we\", because this"
            " passage is the other side's play from end to end and the"
            " listener's team did not do it. What this voice can do that the"
            " Storyteller does not is tell it from the defending side's"
            " point of view: who closed the scorer down, who came back at"
            " him, what the defence tried."
        ),
        example=(
            "Odili won it back in his own half and found Brandt, who got past "
            "Marrow and played a long ball to Vance, and though Marrow came "
            "back at him Vance carried it into the box, got around Oyelaran "
            "and scored."
        ),
    ),
    CALLER_NEUTRAL: NarratorStyle(
        key=CALLER_NEUTRAL,
        label="the Caller, to a listener with no side",
        style=(
            "Quick play-by-play, keeping up with the move. The chains are at"
            " their shortest (\"Odili to Brandt\"), the repetition is clipped"
            " (\"past one, past another\"), and the whole thing runs as one"
            " sentence of clauses rather than several. No \"we\": this"
            " listener supports neither side. It ends on the finish and the"
            " finish gets the exclamation mark."
        ),
        example=(
            "Odili won it back, Odili to Brandt, Brandt past Marrow, a long "
            "ball forward to Vance, into the box, around Oyelaran, and he "
            "scored with his right!"
        ),
    ),
}


def slot_key(persona_id: str, situation: str) -> str:
    """The style key for a narrator and a situation, or a refusal.

    `situation` is `app/delivery.py`'s: `scored`, `conceded` or `neutral`. The
    Storyteller and the Caller read the same in all three, so they are keyed
    `_neutral` whoever is listening, which is also how `hero.voice_for` in
    `app/web/matches.json` names the Storyteller's recording.
    """
    if persona_id == "buddy":
        key = "buddy_{}".format(situation)
    else:
        key = "{}_neutral".format(persona_id)
    if key not in STYLES:
        raise KeyError(
            "there is no goal-call style for {} in the {} situation; the "
            "styles are {}".format(
                persona_id, situation, ", ".join(sorted(STYLES))
            )
        )
    return key


def situation_for(side: str | None, scoring_team: str) -> str:
    """Which of `app/delivery.py`'s three situations this listener is in."""
    if not side:
        return "neutral"
    return "scored" if fold(side) == fold(scoring_team) else "conceded"


def shared_name_parts(facts: Facts) -> tuple[str, ...]:
    """The parts of a recorded name that fit more than one player.

    Printed in the prompt because the grammar refuses them and a model cannot
    guess which they are. Read off `name_keys`, so this says what the check
    says rather than a second opinion about it.
    """
    shared = [
        key for key, players in name_keys(facts).items() if len(players) > 1
    ]
    return tuple(sorted(part.title() for part in shared))


def _seconds_phrase(facts: Facts) -> str | None:
    """"under ten seconds", for the span the timestamps give, or `None`.

    The smallest number word the span is under, so the phrase is true and as
    tight as the words allow. The 2022 counter is 9.757 seconds and comes out
    "under ten seconds"; the 1986 run is 15.7 and comes out "under twenty",
    which is the closest the number words get.
    """
    span = facts.seconds
    if span is None:
        return None
    above = sorted(
        word for word, value in NUMBER_WORDS.items() if value > span
    )
    if not above:
        return None
    tightest = min(above, key=lambda word: NUMBER_WORDS[word])
    return "under {} seconds".format(tightest)


def _where(facts: Facts, beat) -> str:
    """Where a record happened, for the side in possession only.

    StatsBomb mirrors a defensive record's coordinates, so "his own half" on a
    defender's `Pressure` means the half his team is attacking, which is the
    opposite of what the words say. Printing it for the possession team alone
    keeps every line in the prompt readable in the way the narration will say
    it.
    """
    if beat.team != facts.moment.team:
        return ""
    for place in (beat.end, beat.start):
        if place is None:
            continue
        if place.in_the_box:
            return ", in the box"
        if place.in_own_half:
            return ", in his own half"
        return ""
    return ""


def record_line(facts: Facts, beat) -> str:
    """One record, said plainly, with the fields a goal call can use.

    The clock is left off, because no narration carries one. Everything else is
    read: the recipient of a pass, whether it was the assist, whether it was a
    long ball, whether the record is under pressure, whether the shot was
    struck first time, the body part, and where on the pitch.
    """
    verb = EVENT_VERBS.get(beat.action, beat.action)
    parts = ["{} ({}) {}".format(beat.name, beat.team, verb)]
    if beat.recipient:
        parts.append(" to {}".format(spoken_names(facts).get(
            beat.recipient, beat.recipient
        )))
    extras = []
    if beat.goal_assist:
        extras.append("the assist")
    if beat.long_pass:
        extras.append("a long ball")
    if beat.under_pressure:
        extras.append("under pressure")
    if beat.first_time:
        extras.append("first time")
    if beat.body_part and beat.action == "Shot":
        extras.append("with his {}".format(beat.body_part.lower()))
    if extras:
        parts.append(", " + ", ".join(extras))
    parts.append(_where(facts, beat))
    return "".join(parts)


def records_block(facts: Facts) -> str:
    """Every record of the passage, in order, with no clock on any of them."""
    width = len(str(len(facts.facts)))
    lines = [
        "  {:>{}}. {}".format(fact.number, width, record_line(facts, fact.beat))
        for fact in facts.facts
    ]
    return "\n".join(lines)


def catalyst_and_finish(facts: Facts) -> str:
    """Where this narration starts and what it lands on, said plainly.

    The framework says start at the catalyst and land the finish, and the live
    run of 2026-10-31 showed why the records have to say which: the worked
    example opens on a recovery, and the model opened the 2022 counter with
    "we won it back through Molina" three times over. Molina's first record in
    that passage is a pass. The example taught the shape and the records were
    where the shape had to come from, so now they say so.
    """
    steps = move_steps(facts)
    spoken = spoken_names(facts)
    first, last = steps[0], steps[-1]
    opening = [
        EVENT_VERBS.get(
            fact.beat.action, fact.beat.action
        )
        for fact in facts.facts
        if fact.number == first.numbers[0]
    ]
    return (
        "Start on the first step and land on the last. The first thing that"
        " happened is that {} {}, and that is where the narration starts;"
        " nothing before it. The last thing is that {} scored, and that is"
        " where it stops.".format(
            spoken[first.player],
            opening[0] if opening else "had the ball",
            spoken[last.player],
        )
    )


def steps_block(facts: Facts) -> str:
    """The move as the steps a narration tells, in order.

    `move_steps` is one step per turn on the ball and `key_beats` names every
    dribble past an opponent, which is the same pair the cited prompt's hero
    block is built from. Here the two are merged into one list of plain
    sentences with no fact numbers on them, because a goal call has none.
    """
    spoken = spoken_names(facts)
    dribbles = [beat for beat in key_beats(facts) if beat.kind == DRIBBLE]
    by_number = {fact.number: fact for fact in facts.facts}
    steps = move_steps(facts)
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
        name = spoken[step.player]
        if beaten is not None:
            # `KeyBeat.label` is already "dribbled past X".
            said = "{} {}".format(name, beaten.label)
        else:
            beats = [by_number[number].beat for number in step.numbers]
            verbs = []
            for beat in beats:
                verb = EVENT_VERBS.get(beat.action, beat.action)
                if beat.recipient:
                    verb += " to {}".format(
                        spoken.get(beat.recipient, beat.recipient)
                    )
                verbs.append(verb)
            said = "{} {}".format(name, ", ".join(dict.fromkeys(verbs)))
        last = " (the goal)" if index == len(steps) else ""
        lines.append("  {}. {}{}".format(index, said, last))
    return "\n".join(lines)


def _wrapped(text: str, indent: str = "") -> str:
    return textwrap.fill(
        " ".join(text.split()),
        width=76,
        initial_indent=indent,
        subsequent_indent=indent,
    )


def _rule(number: int, text: str) -> str:
    head = "{}. ".format(number)
    return textwrap.fill(
        " ".join(text.split()),
        width=76,
        initial_indent=head,
        subsequent_indent=" " * len(head),
    )


def rules(
    facts: Facts, style: NarratorStyle, target_characters: int
) -> str:
    """The rules, which are the ones `app/grounding.py` holds a goal call to.

    Nine of them are the same for every narrator and the tenth is the
    narrator's own. The one that reads differently per narrator is the one the
    check reads differently: the first person and the exclamation mark.
    """
    shared = shared_name_parts(facts)
    words = round(target_characters / GOAL_CALL_CHARACTERS_PER_WORD)
    body_part = facts.body_part or "not recorded"
    return "\n".join(
        (
            _rule(
                1,
                "Write in the past tense. This has already happened and you"
                " are telling a fan what they missed, so \"dribbled\", not"
                " \"dribbles\"; \"scored\", not \"scores\". A line in the"
                " present tense is rejected.",
            ),
            _rule(
                2,
                "Start at the catalyst, tell the decisive part, land the"
                " finish. The last thing you say is that the ball went in,"
                " and nothing follows it: no summary, no comment, no sentence"
                " addressed to the listener.",
            ),
            _rule(
                3,
                "Say only what the records above hold. Every player, every"
                " pass from one named player to another, every defender gone"
                " past, every position on the pitch and the body part all"
                " have to be up there. Anything you add from memory is"
                " rejected. The goal was scored with the {}.".format(
                    body_part.lower()
                ),
            ),
            _rule(
                4,
                "Name a player as the records print them, or by any part of"
                " that name that fits only one of them: \"{}\" is fine."
                " Never use a part that fits two players, which here"
                " means: {}.".format(
                    _one_safe_part(facts),
                    ", ".join('"{}"'.format(part) for part in shared)
                    or "nothing, every part of every name is unambiguous",
                ),
            ),
            _rule(
                5,
                "\"He\", \"his\" and \"who\" mean the player who last had the"
                " ball. Say a name once and then follow him with a pronoun;"
                " saying a full name six times is a document rather than a"
                " call. A defender you have just said somebody went past is"
                " not what the next \"he\" means.",
            ),
            _rule(
                6,
                "Write a pass as a chain, \"X to Y\", or as \"X played it to"
                " Y\", \"found Y\", \"gave it to Y\" or \"set up Y\". Only"
                " for a pass the records show from X to Y: both names being"
                " up there is not enough. {}".format(_assist_rule(facts)),
            ),
            _rule(
                7,
                "No clock and no digit anywhere. Not a minute, not a second,"
                " not a count: the line before this narration already says"
                " when the goal came, and a colon between two numbers is read"
                " aloud as a colon between two numbers. Write a count as a"
                " word if you need one.",
            ),
            _rule(
                8,
                "No nicknames for the goal or the players, no verdicts, no"
                " words like \"decisive\", \"brilliant\" or \"historic\"."
                " Nothing about the score, the result or what the goal meant"
                " for the match. Nothing about the crowd, the weather or"
                " anybody's intentions. No em dashes. Never \"you\" or"
                " \"your\".",
            ),
            _rule(9, style.style),
            _rule(
                10,
                "One or two sentences, clauses joined rather than one claim"
                " per full stop, coming to about {} characters in all, which"
                " is roughly {} words. This gets recorded and a monthly"
                " character allowance pays for it, so a shorter telling of"
                " the whole move is better than a longer one. Do not drop a"
                " step to get there. Output the narration only, with no"
                " preamble, heading or explanation.".format(
                    target_characters, words
                ),
            ),
        )
    )


def _assist_rule(facts: Facts) -> str:
    """Which pass "set up" may be said about, named rather than described.

    One pass per passage carries `goal_assist`, and the live run of
    2026-10-31 had the model calling three other passes a set-up. Rule 6 said
    "the pass marked the assist"; it now says which pass that is.
    """
    spoken = spoken_names(facts)
    assist = next(
        (fact.beat for fact in facts.facts if fact.beat.goal_assist), None
    )
    if assist is None or not assist.recipient:
        return (
            "No pass in this passage is recorded as the assist, so nothing in"
            " it may be called a set-up."
        )
    return (
        "\"Set up\" is for one pass and no other: {} to {}. Every other pass"
        " is a chain, so write it as \"X to Y\" or \"found Y\".".format(
            assist.name, spoken.get(assist.recipient, assist.recipient)
        )
    )


def _one_safe_part(facts: Facts) -> str:
    """A short name that fits one player, as an example for rule 4.

    The scorer's, where any part of it is unambiguous, so the example in the
    rule is a name the narration is certain to need.
    """
    keys = name_keys(facts)
    scorer = facts.goal_beat
    parts = [
        part
        for part, players in keys.items()
        if players == (scorer.player,) and " " not in part
    ]
    if not parts:
        return scorer.name
    return max(parts, key=len).title()


def build_goal_call_prompt(
    facts: Facts,
    key: str,
    target_characters: int = GOAL_CALL_TARGET_CHARACTERS,
) -> str:
    """The prompt for one goal in one narrator's voice.

    `key` is one of `STYLES`, which is a narrator and a situation together.
    Everything above the style is the same for all four, because the records
    are the records; what changes is rule 9 and the worked example.
    """
    style = STYLES[key]
    moment = facts.moment
    players = [
        spoken_names(facts)[player] for player in touched_the_ball(facts)
    ]
    span = _seconds_phrase(facts)
    pattern = ", ".join(sorted(facts.play_patterns)) or "not recorded"
    extra = []
    if span:
        extra.append(
            "The move ran from the first record to the shot in {}.".format(span)
        )
    extra.append(
        "The possession is recorded as {}.".format(pattern)
    )

    return """You are writing the narration for one goal in a football match, for a fan
who missed it. It is the recap a commentator gives over the replay: the app
this is for says only what the match data proves, so you may use the records
below and nothing else.

YOU ARE WRITING FOR
{label}

THE GOAL
  Team:       {team}
  Scorer:     {scorer}
  Body part:  {body_part}
  Shot type:  {set_piece}

EVERY RECORD OF THE PASSAGE
In the order it happened, with no clock on any of it, because the narration
carries none. Nothing happened that is not here.
{records}

{extra}

THE MOVE TO TELL
The same records as the steps a narration tells. Take them in this order and
reach all of them; the numbers are for reading and never for writing.
{steps}

{anchor}

{who_had_it}

WRITE IT LIKE THIS
Here is a different goal, in a match that does not exist, to show the voice
rather than the words, and the records above are still the only move you may
narrate.

{invented}

Told by {label}:

{example}

That example is about players who do not exist. The only move you may narrate
is the one above it.

RULES
{rules}
""".format(
        label=style.label,
        team=moment.team,
        scorer=facts.goal_beat.name,
        body_part=facts.body_part or "not recorded",
        set_piece=facts.set_piece or "Open Play",
        records=records_block(facts),
        extra=_wrapped(" ".join(extra)),
        steps=steps_block(facts),
        anchor=_wrapped(catalyst_and_finish(facts)),
        who_had_it=_wrapped(
            "Every player in that list had the ball: "
            + ", ".join(players)
            + "."
        ),
        invented=_wrapped(INVENTED_MATCH, indent="  "),
        example=_wrapped(style.example, indent="  "),
        rules=rules(facts, style, target_characters),
    )
