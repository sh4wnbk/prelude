# The narration voice

This is the written voice: what Prelude's narration sounds like, what it may
say, and what it may never say. It is not about audio. Turning narration into
speech is Phase 5, and nothing in the repo does it yet.

The voice has one rule behind it, and the rest of this document is that rule
worked out in detail: **the narration says only what the play data proves.**

Two decisions follow from what the narration is for. It is playback of a passage
that has already happened, so it is told in the **past tense**. And it stops on
the goal: there is **no closer**, no line addressed to the fan after the ball
goes in.

## Where the voice is enforced

The voice is not a style note someone is trusted to remember. It is written
into two places that have to agree:

| Where | What it does |
| ----- | ------------ |
| `app/narration_prompt.py` | builds the numbered facts, and states the rules to the model in the prompt |
| `app/grounding.py` | refuses a narration that broke them |
| `scripts/narrate_once.py` | runs one goal through a real model and prints every attempt |

A prompt that asked for less than the check enforces would set the model up to
fail and a retry would not help it, so the rules below appear in both. When one
changes, the other changes with it.

## What it sounds like

Plain past-tense commentary, four sentences by default. It describes the passage
of play the data recorded, in the order it happened, and stops.

> Maradona received the ball inside his own half. He dribbled past Beardsley. He
> dribbled past Butcher and Fenwick. Maradona shot and scored for Argentina.

Short sentences, one action each. Players named as the data names them, or
shortened to a surname the data contains. No scene setting that the data did
not record.

## Past tense, because it is playback

A fan opens Prelude after the moment has gone. The buildup they missed is a
record of something finished, and commentary in the present tense tells them it
is happening now, which is the one thing this app is not doing: there is no live
feed anywhere in the project.

So the facts are written as a record, and the narration follows:

```
  11. Diego Armando Maradona (Argentina) dribbled, 54:08
  14. Terry Butcher (England) was dribbled past, 54:13
```

`app/grounding.py` holds both halves of it. The past-tense forms are the ones
that ground an event, in `ACTION_CLAIMS`, and the present-tense forms are in
`PRESENT_TENSE` and are refused:
`tests/test_grounding.py::TestTense::test_a_present_tense_sentence_is_flagged`.
"dribbles" is not a weaker way of saying "dribbled", it is a claim about a
passage still in progress.

Refused: "dribbles", "shoots", "scores", "presses", "passes", "recovers",
"wins", and "is dribbled past", where the tense sits in the auxiliary rather
than in the participle the facts use
(`tests/test_grounding.py::TestTense::test_an_auxiliary_carries_the_tense_too`).
The participle on its own is fine, because the facts say it:
`tests/test_grounding.py::TestTense::test_the_past_participle_on_its_own_is_fine`.

**"Won" is the word that needed care.** "Won a foul" is a `Foul Won` record and
has to stay sayable, and "won the match" is a result no buildup carries. Both
hold, and both are tested:
`tests/test_grounding.py::TestTense::test_won_a_foul_is_allowed` and
`tests/test_grounding.py::TestTense::test_won_the_match_is_refused`. What
decides it is the object rather than the verb, so the refusal reaches past "won"
to what was won.

The one thing a tense check cannot do is read English. It covers the verbs the
facts and the narration actually use, not every verb there is, so "turned",
"advanced" or "went again" are unchecked prose either way.

## Every sentence cites its facts

The narration is not written from the match. It is written from a numbered list
of plain facts, one per recorded event, that `app/narration_prompt.py` builds
by code out of the records:

```
   1. José Luis Cuciuffo (Argentina) recovered the ball, 54:02
  ...
  10. Peter Beardsley (England) was dribbled past, 54:08
  11. Diego Armando Maradona (Argentina) dribbled, 54:08
  13. Peter Reid (England) pressed, 54:08
  14. Terry Butcher (England) was dribbled past, 54:13
  ...
  24. Diego Armando Maradona (Argentina) shot, 54:18
```

Each sentence starts with the numbers of the facts it is about:

```
[11] Maradona dribbled past Peter Beardsley.
[24] Maradona shot and scored for Argentina.
```

The citation comes first because that is the order the work happens in: pick a
fact, read its number, then say it. `app/grounding.py` then reads each sentence
against the facts that sentence cited. One fact per event and one player per
fact, because one record names one player: "Maradona dribbled past Butcher" is
two records (a `Dribble` on Maradona's, a `Dribbled Past` on Butcher's) and so
two facts, and pairing them into one would mean inferring which dribble went
past whom.

The tags are machinery, not copy. `strip_citations` takes them off and joins the
sentences into one paragraph before anything is shown or voiced, so what a
screen displays and a voice reads is the narration alone. The cited version is
kept beside it, as `Narrated.tagged_text`, because that is the version a reader
can audit line by line.

## What it never does

### No verdicts and no epithets

App output describes what the data shows. It does not rank the goal, the
players or the match. Nicknames are broadcast language, not findings, and
attaching one to a data-grounded line misrepresents the line as a judgement the
data did not make.

Refused: "the Goal of the Century", "a decisive moment", "a significant
moment", "a brilliant finish", "the greatest", "historic", "iconic".

The epithets are in the refusal list because of a real line. The first live run
that got past every other check still ended: "This decisive moment marked a
significant moment in the match's narrative." Two judgements in one sentence,
neither of them in the data.

### Nothing about the score or the result

A buildup is one passage of play. It carries no scoreline, so the result is
outside the facts the narration was written from, whatever a reader may know
about the match.

Refused: "securing Argentina's victory", "the winner", "the equaliser",
"sealing the trophy". Both narrations in the first live run that passed every
other check ended on an outcome claim.

"Wins a foul" is fine, because `Foul Won` is a recorded event. The refusal is
about the match result, not the word.

### No name, number or action that is not in the facts the sentence cited

Not "in the passage": in the facts that sentence named. A word that is in the
buildup but not in the cited facts is refused too, and the report says which of
the two it was, because an invented player and a miscited one want different
fixes.

- **Names.** Only players and teams in the cited facts, which for a set-piece
  goal includes the previous possession. A real player who was not in this
  passage is as ungrounded as an invented one.
- **Clocks.** Written exactly as the cited fact writes it: "54:13" belongs to a
  sentence citing fact 14 or 15 and to no other. This is new with the numbered
  facts; before them, a per-second clock could not be grounded at all, and the
  prompt had to hide the seconds to avoid failing a model for quoting them.
- **Counts.** Written as words: "past two defenders", never "past 2 defenders".
  A bare digit is grounded only by the minute of a cited fact or by the second
  the goal was scored at. Every second a possession passes through is a number
  between 0 and 59, so admitting those as bare digits would ground almost any
  count a model invented.
- **Actions.** Only what a cited fact records. No save, cross, header or tackle
  that is not there. A word that names both sides of one event grounds against
  either record: "X dribbled past Y" is satisfied by the `Dribble` on X's record
  or the `Dribbled Past` on Y's, which is what lets a sentence name the
  defender who was beaten.
- **The shot.** The shot type and the body part come off the goal event. A goal
  does not become a penalty, a free kick or a corner, and a left foot does not
  become a header. This is the easiest thing in the list to get wrong, because
  the facts do not reveal the shot type: a model can invent a penalty without
  contradicting anything it was shown.
- **A sentence that cites nothing** is refused whatever it says. There is
  nothing to read it against.

### No em dashes

Use a colon, a semicolon, parentheses or two sentences.

## A line can read well and still be refused

An early hand-written line, from before any of this existed, read:

> Just inside his own half, he turns away from two. Past one, past another,
> still going. And he is around the keeper.

It is good copy. It is also refused, and for an instructive reason: it names
nobody and quotes no clock, so there is nothing in it that traces back to the
data. "Inside his own half" is a spatial claim nothing checks. A narration that
asserts nothing checkable cannot carry "Verified from play data", because there
is nothing for the label to be true about. Giving it citations would not save
it: a sentence can cite every fact in the passage and still assert nothing those
facts could confirm.

## The misdescription the check used to miss

The check used to verify that everything a line **named** was somewhere in the
passage, and nothing more. That catches invention and nothing else. The worked
example, from the 54:18 goal: the records show four players dribbled past
(Beardsley, Butcher, Fenwick, Shilton) and three applying pressure (Beardsley,
Reid, Butcher). This line used to pass:

> Maradona dribbled past Peter Beardsley, Peter Reid and Terry Butcher, and
> scored for Argentina.

Every name is in the buildup and a `Dribble` event is in it, so nothing is
invented. Reid pressured and was never dribbled past, so the sentence describes
something that did not happen.

**It is refused now.** Every name in a sentence is paired with every action in
it, and the pair has to meet inside one cited fact:

| Name | A cited fact pairing it with a dribble |
| ---- | -------------------------------------- |
| Maradona | fact 11, `Dribble` |
| Beardsley | fact 10, `Dribbled Past` |
| Butcher | fact 14, `Dribbled Past` |
| Reid | none: his only record in this passage is fact 13, a `Pressure` |

So the sentence fails, and it fails on Reid alone: the report names him and
leaves the two defenders it was right about out of it, because a refusal that
listed all three would send a retry to rewrite the true part. No choice of
citations rescues it either. Reid has one record in that passage and it is a
`Pressure`, so there is no fact to cite that pairs him with a dribble. This is
the named example in `tests/test_grounding.py::TestMisdescription`.

### What pairing costs

Pairing every name with every action is blunt on purpose. Nothing in the text
says which name goes with which action, so a sentence holding two actions and
three names is one the check cannot read exactly, and refusing it is the
conservative answer. That means the check refuses some true sentences:

> Di Maria won a foul and Messi scored for Argentina.

is true, and is refused, because no one fact pairs Messi with the foul. Written
as two sentences, each citing its own fact, both pass. This is why the prompt
asks for one action per sentence, and why the voice above is short sentences.
The trade is deliberate: a refused true sentence costs a regeneration, and an
accepted false one would be labelled "Verified from play data".

## It ends on the goal, and there is no closer

The narration's last sentence is about the goal, and nothing follows it. No
summary, no comment, no line addressed to the fan.

There was an argument for a closer: one sentence in the present tense, spoken to
the fan, handing the moment back to them. It is dropped, and the reason is the
room the app is standing in. The goal has just gone in. The stadium is doing the
only thing a stadium does at that moment, and a phone adding "that is the moment
you came for" is competing with 80,000 people and losing. **The stadium takes
over, and the app gets out of the way.** A closer would also be the one sentence
in the narration that no fact could ground, which is the opposite of what the
label over it promises.

What the check can hold is where the narration stops: the last sentence has to
cite the goal's own shot fact, so a sentence after the goal is refused.

| Narration | Verdict | Test |
| --------- | ------- | ---- |
| ends on the sentence citing the shot | passes | `tests/test_grounding.py::TestEnding::test_a_narration_that_ends_on_the_shot_passes` |
| a sentence after the goal | refused | `tests/test_grounding.py::TestEnding::test_a_last_sentence_that_does_not_cite_the_shot_is_refused` |
| stops before reaching the goal | refused | `tests/test_grounding.py::TestEnding::test_a_narration_that_stops_before_the_goal_is_refused` |
| a line addressed to the fan | refused | `tests/test_grounding.py::TestEnding::test_a_closing_line_addressed_to_the_fan_is_refused` |

Citation placement alone cannot catch a closer, because a closer can cite the
goal's fact as easily as the goal sentence can. What catches it is the second
person: there is no line spoken to the fan, so "you", "your" and "yours" are
refused wherever they appear. A closing line that cites the goal's fact, keeps
out of the second person and asserts nothing checkable is caught by nothing
here, which
`tests/test_grounding.py::TestEnding::test_what_the_ending_rule_alone_cannot_catch`
records rather than leaves to be discovered.

## What the check still cannot do

It reads a sentence against the facts that sentence cited. It does not read the
sentence's grammar.

- **Direction survives.** "Maradona passed to Enrique" and "Enrique passed to
  Maradona" cite the same facts and both pass, and only one of them is what
  happened.
- **Relations the records do not hold are not checkable.** StatsBomb records a
  `Pressure` against the player applying it and names nobody being pressed, so
  "Butcher presses Maradona" is refused for naming Maradona over a fact that
  does not hold him, not because the check knows who was pressed.
- **Prose that asserts nothing about an event** is outside its reach entirely.
  "as he approaches the goal" names no player, action or clock, so there is
  nothing in it to refuse and nothing in it to confirm.
- **Some verbs are prose, not claims.** `ACTION_CLAIMS` is deliberately narrow
  and grows from live failures rather than from a wish to be complete. A verb
  that is not in it, such as "turns" or "advances", is not checked against
  anything.

So the check catches invention and it now catches the misdescriptions that come
from attaching a name or a clock to the wrong record. It does not make the
narration correct, and no claim that it is should rest on this module alone.

## When the model will not comply

The narration fails whole, never line by line. A line is not dropped and not
kept unlabelled:

- Dropping it breaks the flow and can mislead. A run recorded as past one
  defender, then another, then the goalkeeper reads as a different move with
  the middle cut out.
- Keeping it unlabelled breaks the rule that the app says only what the play
  data proves.

So a failing narration is generated again, up to twice. If it still fails, the
fallback in `app/narration_prompt.py` assembles a short plain narration straight
from the facts, in the same cited layout the prompt asks a model for:

```
[24] Minute 54.
[3] José Luis Cuciuffo passed.
[6] Héctor Adolfo Enrique passed.
[11] Diego Armando Maradona dribbled.
[24] Diego Armando Maradona shot and scored for Argentina.
```

which is shown and voiced as:

> Minute 54. José Luis Cuciuffo passed. Héctor Adolfo Enrique passed. Diego
> Armando Maradona dribbled. Diego Armando Maradona shot and scored for
> Argentina.

That is the fallback voice, and it is deliberately plainer than the voice above.
It is grounded by construction, because every sentence is one fact said in the
words that fact used, citing that fact and no other, and it is run through the
same check anyway. One fact per sentence is also what keeps it inside the
pairing rule. It uses full recorded names rather than shortening them, so that a
fallback is not the thing that introduces a judgement about what a player is
called.

Nothing ungrounded is ever voiced or labelled. If even the fallback failed the
check there would be nothing safe to say, and the pipeline raises rather than
returning something unverified.

## What the live runs show

`scripts/narrate_once.py` runs this against the local development model,
`granite4:micro`, and prints every attempt. Two runs over the 1986 54:18 goal,
with the facts and the prompt in the past tense:

| Run | Model attempts | What came back |
| --- | -------------- | -------------- |
| 1 | 1 grounded | four past-tense lines, labelled |
| 2 | 1 and 2 refused, 3 grounded | four past-tense lines, labelled |

Run 1's first attempt:

```
[1] José Luis Cuciuffo recovered the ball.
[2] José Luis Cuciuffo carried the ball.
[3] José Luis Cuciuffo passed.
[24] Diego Armando Maradona shot.
```

Every verb is past tense, every citation is right, and it stops on the goal. It
is also thin: the model takes the first three facts in order and then jumps to
the shot, so the run that the goal is famous for is the one thing the narration
skips. That is a model limit rather than a check limit, and nothing in the repo
refuses a narration for being dull.

Run 2's first attempt is the one worth reading, because the ending rule caught a
real mistake rather than a hypothetical one: the model wrote the goal sentence
and then added another after it, citing fact 18, and the refusal says so. Its
second attempt cited a `Carry` for a dribble. Both are the same kind of error
as before, the right words against the wrong fact number.

Across these runs and the four under the present-tense prompt, every refusal was
a real one and none was a false positive. The tense rule has not yet refused a
live attempt: with the facts written in the past tense, the model wrote past
tense without being corrected, which is the outcome the prompt and the facts
were changed for. The pass rate is still the number that matters, six runs are
not a rate, and nothing measures it over the nine goals; that is Task 4, and
`Narrated.first_attempt_grounded` is what it has to count.

## The screens have not caught up

The moment card's hero quote is the slot narration will occupy: it is what
`scripts/scan_copy.py` counts as the narration field when it decides whether
"Verified from play data" is sitting over narration. Today it is fixed demo copy
in `app/web/matches.json`, written by hand in the broadcast register and in the
present tense, and no screen reads `app/narration.py` at all.

So nothing on a screen follows this document yet. When narration is wired to a
screen, that copy goes past tense or is replaced by generated narration; the
names in it are already checked against the data by
`scripts/check_match_copy.py`, and the tense is not checked by anything. It is
recorded here rather than quietly fixed, because changing demo copy would not
make the screen any more connected to the narration than it is now.

## The label

The phrase is **"Verified from play data"**, written once in
`app/narration.py` so nothing spells it differently or softens it. There is no
partial credit and no shortened variant. It goes over narration that passed the
check, and over nothing else.
