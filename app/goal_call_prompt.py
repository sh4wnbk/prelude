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
| `storyteller_neutral` | anybody; the move told evenly, in the third person, in full sentences |
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

**What the model is shown is the story beats, not the records.**
`app/story_beats.py` curates the passage down to them: the recovery, each
pass, each run of ten yards or more, each dribble past an opponent, the
pressure on the player with the ball and the finish, with the recorded fields
a goal call says out loud on each one. The ball receipts and the touches on
the spot are left out, because the candidates of 2026-10-31 echoed the list
they were given and that list was every record in the passage, eight of them
receipts. Nothing is inferred and nothing is added: the curation can only
narrow what a narration may say, and `app/grounding.py` still verifies it
against every record.

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

from app.narration_grammar import (
    NUMBER_WORDS,
    fold,
    name_keys,
)
from app.narration_prompt import (
    EVENT_VERBS,
    Facts,
    move_steps,
    spoken_names,
    touched_the_ball,
)
from app.story_beats import beats_block, story

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
    "Kestrel Bay are the side that scored and Vance scored it, with his "
    "right foot, from open play. Five players: Odili, Brandt and Vance of "
    "Kestrel Bay, and Marrow and the goalkeeper Oyelaran, who defend for "
    "Harbour Town. The possession is recorded as from a counter, and it runs "
    "from the first beat to the shot in under ten seconds. Odili won the "
    "ball back in his own half and passed to Brandt. Brandt carried it "
    "forward under pressure from Marrow, far enough to be called a run, went "
    "past Marrow, and "
    "played a long ball forward to Vance, which is the pass recorded as the "
    "assist. Vance carried it into the box, went around Oyelaran, and scored "
    "with his right foot."
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
            " The reaction is restrained and ends on a full stop: this voice"
            " notices the goal rather than celebrating it. Tell it in full"
            " sentences, and write no pass as \"X to Y\": every pass this"
            " voice says has a verb in it, so \"he played it to Y\", \"he"
            " found Y\" or \"he gave it to Y\", never \"X to Y, Y to Z\"."
            " That shorthand is the Buddy's idiom and the Caller's, and"
            " keeping it out of this one is part of each narrator having its"
            " own text."
        ),
        example=(
            "Odili's recovery started the counter, and he gave it to Brandt "
            "just inside his own half, who carried it forward under pressure "
            "past Marrow and sent a long ball forward to Vance, who took it "
            "into the box, went around Oyelaran and scored with his right "
            "foot. Well, that was lovely."
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
            " place a listener cheers, so the sentence that lands it ends on"
            " an exclamation mark, and so may the reaction after it. This is"
            " the voice that gets both."
        ),
        example=(
            "We won it back through Odili, and he gave it to Brandt in his "
            "own half, who went past Marrow and sent a long ball forward to "
            "Vance, and from there it was all Vance: into the box, around "
            "Oyelaran, and he scored with his right foot! Oh, lovely!"
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
            " him, what the defence tried. The reaction is subdued and ends"
            " on a full stop, or there is none at all: \"Ah, no.\" is the"
            " whole of what this listener wants to hear about it."
        ),
        example=(
            "Odili won it back in his own half and found Brandt, and though "
            "Marrow closed him down and came back at him, Brandt got past "
            "Marrow and played a long ball forward to Vance, who carried it "
            "into the box, got around Oyelaran and scored. Ah, no."
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
            " listener supports neither side. It ends on the finish, the"
            " finish gets the exclamation mark, and the reaction after it may"
            " have one too."
        ),
        example=(
            "Odili won it back and the counter was on, Odili to Brandt, "
            "Brandt forward under pressure, past Marrow, a long ball forward "
            "to Vance, Vance into the box, around Oyelaran, and he finished "
            "with his right! What a finish!"
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
        "Start on the first beat and land on the last. The first thing that"
        " happened is that {} {}, and that is where the narration starts;"
        " nothing before it. The last thing is that {} scored, and that is"
        " where it stops.{}".format(
            spoken[first.player],
            opening[0] if opening else "had the ball",
            spoken[last.player],
            _nothing_won_back(facts),
        )
    )


def _nothing_won_back(facts: Facts) -> str:
    """Said when the passage holds no recovery, because the example does.

    The worked example opens on "won it back", which is a `Ball Recovery`,
    and the 2022 counter holds none: Molina's first record in it is a pass.
    The model wrote "we won it back through Molina" three times in the run of
    2026-10-31 and twice more in the run at effort high, and `catalyst_and_
    finish` saying which step comes first was not enough to stop it. So the
    records say the thing that is not there as well as the thing that is.
    """
    if any(fact.beat.action == "Ball Recovery" for fact in facts.facts):
        return ""
    return (
        " No record in this passage is a ball recovery, so nothing in it was"
        " won back and nobody won the ball: the example below opens that way"
        " and this move does not."
    )


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

    Sixteen of them are the same for every narrator and rule 11 is the
    narrator's own. The one that reads differently per narrator is the one
    the check reads differently: the first person, the exclamation mark and
    how the reaction ends.

    **Rules 15 and 16 are about the two beats a telling kept flattening.**
    Both are general: they say what to do when the records mark a pass long
    or a finish first time, and the beats say which pass and which finish
    that is in this move. The run of 2026-11-05 is what asked for them. The
    2022 move turns on Álvarez's 38 yard ball back to MacAllister and every
    candidate told it as one more comma in a list of five passes, and the
    2022 shot is the one of the two recorded as struck first time and no
    candidate said so.

    **Rule 17 is what Shawn asked for after reading the six candidates of
    2026-11-05 aloud.** None of them places the move: "dribbled past
    Butcher" and "a long ball to MacAllister" leave a listener with nowhere
    on the pitch to stand. The beats say where now, from the coordinates,
    and the second half of the rule is as load bearing as the first: every
    record in both passages carries a location, so a telling that places
    every beat reads as a list of coordinates with words around it. Two or
    three is what the references do.

    **Rule 14 is a cadence rule and not a claim rule**, which is why nothing
    in `app/grounding.py` answers to it. Every candidate of 2026-10-31 hung
    the move off "who": "passed to Maradona, who carried it forward, who went
    past Beardsley". It is grammatical, it is grounded, and read aloud it is
    one shape repeated. The rest of the cadence is untouched: a long sentence
    is still allowed and nothing asks for a full stop after each pass.
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
                " finish. The last thing you say about the play is that the"
                " ball went in. One thing may follow it and one only, which"
                " is rule 3: no summary, no comment, no sentence addressed to"
                " the listener.",
            ),
            _rule(
                3,
                "You are writing two layers. THE PLAY is everything the"
                " records hold, and every word of it is checked against them."
                " THE REACTION is you feeling the moment, and it is not"
                " checked, because it says nothing about the match: \"Oh,"
                " lovely!\", \"What a finish!\", \"Ah, no.\". One reaction at"
                " most, and it is the last thing you write: it comes after"
                " the sentence that lands the finish, never before the play"
                " and never in the middle of it, and nothing follows it. At"
                " most eight words, and it may hold no player or team name, no"
                " \"he\" or \"his\", no number, and nothing about where the"
                " ball was or what anybody did. A reaction that names"
                " somebody is read as play and checked as play.",
            ),
            _rule(
                4,
                "Say only what the records above hold. Every player, every"
                " pass from one named player to another, every defender gone"
                " past, every position on the pitch and the body part all"
                " have to be up there. Anything you add from memory is"
                " rejected. The goal was scored with the {}.".format(
                    body_part.lower()
                ),
            ),
            _rule(
                5,
                "Which way and how far are claims as well, and the records"
                " above say both. Write \"forward\" or \"back\" only over a"
                " pass or a carry the records show going that way."
                " \"Drove\", \"ran\" and \"burst\" need a carry of at least"
                " ten yards, which the records mark as a run. And a carry"
                " never gives the ball to another player: write \"carried it"
                " forward and played it to Y\", never \"carried it to Y\".",
            ),
            _rule(
                6,
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
                7,
                "\"He\", \"his\" and \"who\" mean the player who last had the"
                " ball. Say a name once and then follow him with a pronoun;"
                " saying a full name six times is a document rather than a"
                " call. A defender you have just said somebody went past is"
                " not what the next \"he\" means.",
            ),
            _rule(
                8,
                "Write a pass as a chain, \"X to Y\", or as \"X played it to"
                " Y\", \"found Y\", \"gave it to Y\" or \"set up Y\". Only"
                " for a pass the records show from X to Y: both names being"
                " up there is not enough. {}".format(_assist_rule(facts)),
            ),
            _rule(
                9,
                "No clock and no digit anywhere. Not a minute, not a second,"
                " not a count: the line before this narration already says"
                " when the goal came, and a colon between two numbers is read"
                " aloud as a colon between two numbers. Write a count as a"
                " word if you need one.",
            ),
            _rule(
                10,
                "No nicknames for the goal or the players, no verdicts, no"
                " words like \"decisive\", \"brilliant\" or \"historic\", and"
                " nothing about where this goal stands among other goals: you"
                " know about this one. No words for how hard the ball was"
                " struck, so not \"smashed\", \"blasted\", \"hammered\","
                " \"rifled\" or \"thumped\": the records say who shot, with"
                " which foot and that it went in, and nothing about force."
                " \"Finished\", \"scored\", \"struck\", \"fired\", \"hit\""
                " and \"slotted\" are all fine. Nothing about the score, the"
                " result or what the goal meant for the match. Nothing about"
                " the crowd, the weather or anybody's intentions. No em"
                " dashes. Never \"you\" or \"your\".",
            ),
            _rule(11, style.style),
            _rule(
                12,
                "One or two sentences of play, clauses joined rather than one"
                " claim per full stop, coming to about {} words, with the"
                " reaction on top if you write one. Do not count the"
                " characters and do not count the words out: about is as"
                " exact as this needs to be, and a line this length is"
                " several seconds of speech. This gets recorded and a monthly"
                " character allowance pays for it, so a shorter telling of"
                " the whole move is better than a longer one. Do not drop a"
                " step to get there. Output the narration only, with no"
                " preamble, heading or explanation.".format(words),
            ),
            _rule(
                13,
                "Several narrations are being written for this slot and they"
                " have to be different tellings of the move, not one telling"
                " with the words swapped. Differ in structure: where the"
                " first sentence starts, whether it is one sentence or two,"
                " whether a pass is \"X to Y\" or \"X played it to Y\","
                " whether the defenders are a list or a repetition, where the"
                " pronoun takes over from the name, whether there is a"
                " reaction at all. Two narrations that differ only in a"
                " synonym are one narration, and only one of them is kept.",
            ),
            _rule(
                14,
                "Use the word \"who\" at most once in the narration. Join the"
                " play with other connections: a comma chain, \"and\", \"on"
                " to\", or a new clause.",
            ),
            _rule(
                15,
                "When a pass is marked long, it is the turn of the move; give"
                " it its own clause.",
            ),
            _rule(
                16,
                "When the finish is first time, say so, with the foot.",
            ),
            _rule(
                17,
                "Place the move on the pitch two or three times: where it"
                " started, where the decisive action happened, and where it"
                " finished. Do not give every beat a place.",
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


def already_written(avoid: Sequence[str]) -> str:
    """The tellings of this move already kept for this slot, or nothing.

    Rule 13 asks for narrations that differ in structure rather than in
    wording, and a model writing each candidate in a separate call cannot
    know what the other calls produced unless it is shown. The run of
    2026-10-31 is what this is for: the three storyteller candidates for 1986
    differed by one full stop and one word.

    This is not the dictation `docs/VOICE.md` forbids. What may never go into
    the prompt is a reference, because the references are the standard and a
    model handing one back measures nothing. These are the model's own
    earlier answers, shown so that it writes a different one.
    """
    if not avoid:
        return ""
    lines = [
        "ALREADY WRITTEN FOR THIS SLOT",
        _wrapped(
            "These tellings of this same move are already kept. Write one"
            " that differs from them in structure, as rule 13 asks: not the"
            " same sentence with other words in it."
        ),
        "",
    ]
    for number, text in enumerate(avoid, start=1):
        lines.append(_wrapped("{}. {}".format(number, text), indent="  "))
    return "\n".join(lines) + "\n"


def build_goal_call_prompt(
    facts: Facts,
    key: str,
    target_characters: int = GOAL_CALL_TARGET_CHARACTERS,
    avoid: Sequence[str] = (),
) -> str:
    """The prompt for one goal in one narrator's voice.

    `key` is one of `STYLES`, which is a narrator and a situation together.
    Everything above the style is the same for all four, because the records
    are the records; what changes is rule 11 and the worked example.

    `avoid` is the narrations already kept for this slot, which the prompt
    asks the model to differ from. It is empty for the first candidate of a
    slot and for every caller that wants one narration.
    """
    style = STYLES[key]
    moment = facts.moment
    players = [
        spoken_names(facts)[player] for player in touched_the_ball(facts)
    ]
    span = _seconds_phrase(facts)
    # The play pattern and the own half are said once, in the beats block:
    # they are facts about the passage rather than about a beat, and they were
    # on every line of the record list this replaced.
    extra = []
    if span:
        extra.append(
            "The move ran from the first beat to the shot in {}.".format(span)
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

{beats}

{extra}

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

{already}
RULES
{rules}
""".format(
        already=already_written(avoid),
        label=style.label,
        team=moment.team,
        scorer=facts.goal_beat.name,
        body_part=facts.body_part or "not recorded",
        set_piece=facts.set_piece or "Open Play",
        beats=beats_block(story(facts)),
        extra=_wrapped(" ".join(extra)),
        anchor=_wrapped(catalyst_and_finish(facts)),
        who_had_it=_wrapped(
            "Every player named here had the ball: "
            + ", ".join(players)
            + "."
        ),
        invented=_wrapped(INVENTED_MATCH, indent="  "),
        example=_wrapped(style.example, indent="  "),
        rules=rules(facts, style, target_characters),
    )
