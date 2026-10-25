# The narration voice

This is the written voice: what Prelude's narration sounds like, what it may
say, and what it may never say. It is not about audio. Turning narration into
speech is Phase 5, and nothing in the repo does it yet.

The voice has one rule behind it, and the rest of this document is that rule
worked out in detail: **the narration says only what the play data proves.**

## Where the voice is enforced

The voice is not a style note someone is trusted to remember. It is written
into two places that have to agree:

| Where | What it does |
| ----- | ------------ |
| `app/narration_prompt.py` | states the rules to the model, in the prompt |
| `app/grounding.py` | refuses a narration that broke them |

A prompt that asked for less than the check enforces would set the model up to
fail and a retry would not help it, so the rules below appear in both. When one
changes, the other changes with it.

## What it sounds like

Plain present-tense commentary, four sentences by default. It describes the
passage of play the data recorded, in the order it happened, and stops.

> Maradona receives the ball, turns, and dribbles past Beardsley. He goes again
> past Butcher and Fenwick. Shilton comes out. Maradona shoots and scores for
> Argentina.

Short sentences. Players named as the data names them, or shortened to a
surname the data contains. No scene setting that the data did not record.

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

### No name, number or action that is not in the passage

- **Names.** Only players and teams in the buildup, including the previous
  possession when the goal came from a set piece. A real player who was not in
  this passage is as ungrounded as an invented one.
- **Numbers.** The minute of a recorded event, or the second the goal was
  scored at. Counts are written as words: "past two defenders", never
  "past 2 defenders". Every second a possession passes through is a number
  between 0 and 59, so admitting those would ground almost any count a model
  invented.
- **Actions.** Only what the records contain. No save, cross, header or tackle
  that is not there.
- **The shot.** The shot type and the body part come off the goal event. A goal
  does not become a penalty, a free kick or a corner, and a left foot does not
  become a header. This is the easiest thing in the list to get wrong, because
  the run of play does not reveal the shot type: a model can invent a penalty
  without contradicting anything it was shown.

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
is nothing for the label to be true about.

## What the check cannot do, and this matters

The check verifies that everything a line **names** is in the data. It does not
verify that the line's reading of those facts is right.

A worked example, from the 54:18 goal. The records show four players dribbled
past (Beardsley, Butcher, Fenwick, Shilton) and three applying pressure
(Beardsley, Reid, Butcher). This line passes the check:

> Maradona dribbles past Peter Beardsley, Peter Reid and Terry Butcher, and
> scores for Argentina.

Every name is in the buildup and a `Dribble` event is in it, so nothing is
invented. But Reid pressured and was never dribbled past, so the sentence
describes something that did not happen.

The check catches **invention**, which is the failure a language model actually
has. It does not catch **misdescription**. Any claim that the narration is
correct rests on more than `app/grounding.py`.

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
from the events:

> Minute 54. José Luis Cuciuffo passes. Héctor Adolfo Enrique passes. Diego
> Armando Maradona dribbles. Diego Armando Maradona shoots and scores for
> Argentina.

That is the fallback voice, and it is deliberately plainer than the voice above.
It is grounded by construction, because every name, number and action in it is
copied out of a recorded event, and it is run through the same check anyway. It
uses full recorded names rather than shortening them, so that a fallback is not
the thing that introduces a judgement about what a player is called.

Nothing ungrounded is ever voiced or labelled. If even the fallback failed the
check there would be nothing safe to say, and the pipeline raises rather than
returning something unverified.

## The label

The phrase is **"Verified from play data"**, written once in
`app/narration.py` so nothing spells it differently or softens it. There is no
partial credit and no shortened variant. It goes over narration that passed the
check, and over nothing else.
