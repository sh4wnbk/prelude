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
| `app/narration_prompt.py` | builds the numbered facts, holds the one style in `NARRATION_STYLE`, and states the rules to the model in the prompt |
| `app/pitch_zones.py` | one recorded location as the phrase a narrator places the move with: eight bands up the pitch and three across it |
| `app/goal_call_prompt.py` | builds the goal-call prompt: a style and a worked example per narrator, the story beats with no clock on them, and the eighteen rules |
| `app/story_beats.py` | curates the passage down to the beats the prompt shows, so the model is not handed every recorded event |
| `app/narration_grammar.py` | reads a goal call that cites nothing, and holds the yard thresholds the words are measured against |
| `app/personas.py` | the three voices the one narration can be spoken in, which is Phase 5 and not this document |
| `app/grounding.py` | refuses a narration that broke them |
| `scripts/narrate_once.py` | runs one goal through a real model and prints every attempt |
| `scripts/narration_eval.py` | runs every goal several times and measures how often the rules held |

A prompt that asked for less than the check enforces would set the model up to
fail and a retry would not help it, so the rules below appear in both. When one
changes, the other changes with it.

## What it sounds like

**The recap stage of a goal call**: it starts at the catalyst, tells the
decisive part, and lands the finish, in the past tense, in the words the game
is talked about in. Chains for the passes, action before name, the shortest
recorded name that picks out one player, and repetition where repetition is
what a listener needs to hear. "The framework: Prelude is the recap stage of a
goal call" below is the whole of it, with the eight reference narrations that
are the standard.

What the code writes today is the style that framework replaces: plain
past-tense commentary, four sentences, one action each, in the order the events
happened.

> Maradona received the ball inside his own half. He dribbled past Beardsley. He
> dribbled past Butcher and Fenwick. Maradona shot and scored for Argentina.

Every word of that is grounded, and it reads like the log file it was assembled
from. Players are named as the data names them, which does not change: the
recorded name or the recorded nickname, and nothing shortened that the match
did not shorten. No scene setting that the data did not record, which does not
change either.

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
  prompt had to hide the seconds to avoid failing a model for quoting them. The
  framework below is narrower than this and asks for no clock in a narration at
  all. `tests/test_reference_narrations.py::TestNoClockReachesTheNarration`
  writes that down, and it passes today for the wrong reason: a clocked line is
  refused as `untagged` like every other uncited line, not because the clock is
  in it.
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

## It opens on one line, and that line says what the goal did to the score

One line comes before the narration, and every listener gets the same one. It
is not narration and it is not generated: it asserts nothing about the match
that the grounding check reads, and it carries no claim the "Verified from play
data" label is about.

### The header

**The header is game focused, and it is the same line for everybody.** It says
what the goal did to the score rather than how the fan should feel about it.

The header before this one was a prefix picked from the listener's side,
whether that side scored or conceded, and how far into the match the moment
came: "Great start.", "Good news.", "Still early.". It is gone, and so is the
table it was looked up in. Shawn's decision after
Phase 4 is that the app does not guess at a mood. A fan with a side and a
listener with none are looking at the same scoreboard, and the mood was the
part of that line the app had not earned. Allegiance no longer reaches the
header at all; what it picks is the persona, which Phase 5 turns into a voice.

Three sentences, joined by single spaces: what the moment did to the score,
then the score, then the tail.

The first sentence is read out of the score before the moment and the score
after it, from the scoring side's point of view, and out of nothing else:

| The scoring side went | The sentence |
| --------------------- | ------------ |
| level to ahead | `{scorer} take the lead.` |
| behind to ahead | `{scorer} take the lead.` |
| ahead to further ahead | `{scorer} extend the lead.` |
| behind to still behind | `{scorer} close the gap.` |
| behind to level | `{scorer} draw level.` |

The second is `{team_a} {score_a}, {team_b} {score_b}.`, both teams in the
order the fixture names them, so a listener with no side reads it the same way
as a listener with one. The third is "Here's how it happened.", which every header
ends on. It was "Here's the buildup." until the card's label above it came to
say "THE BUILDUP", and the word twice in two lines read as repetition. England's goal in 1986, at 80:37, is the whole line:

> England close the gap. Argentina 2, England 1. Here's how it happened.

**This is the starting wording and Shawn writes the final wording.** What is
settled is the shape: fixed sentences, looked up, with nothing generated and
nothing a model chooses. Changing a word is a one line edit to `HEADER_WORDING`
in the contract, which is why the implementation is told to read every sentence
out of the contract rather than writing any of them down.

**Taking the lead and overtaking share a sentence.** "Take the lead" is true of
both, and the difference between them is history the listener already has. They
stay two separate cases anyway, so a later wording that tells them apart does
not need the rule rewritten.

**The header says nothing about earlier goals.** No "again", no "back in front",
no "another". The two scores it is built from do not record whether this side
has led before, so nothing in the line may imply it. This is the mistake the old
table made: its late scored cell first read "Your side again.", which was false
for England's only goal in 1986.
`tests/test_orchestrator.py::TestTheHeader::test_no_header_claims_a_goal_before_this_one`
holds every goal in both demo matches to it.

**The score before the moment is given, never derived.** Subtracting one from
the scoring side would be reading football into a line meant to outlive it: a
score can move by any number of points.
`tests/test_orchestrator.py::TestAnotherSport` is a sixty minute sport that does
not exist, whose scores move three at a time, and it holds the behind-to-ahead
case that neither demo match contains.

**None of this is narration and none of it carries the label.** The header is
built from the fixture and the two scores, not from the event data, so "Verified
from play data" has nothing to say about it. It is also the one line in the app
addressed to the fan, which is what the ending rule above keeps out of the
narration itself: the header goes before the narration, and nothing goes after
it.

**What is built.** `app/orchestrator_contract.py` declares the wording above
along with `transition` and `header`, and both raise there. **IBM Bob built
both in `app/orchestrator.py` as Task 5 in `docs/bob_brief.md`, in `7f1b21e`**,
and `PreludeOrchestrator.opening` says the new line. The 72 tests in
`tests/test_orchestrator.py` all pass. The prefix table the old header read is
gone from the contract. No screen shows a header yet; Task 7 puts it on the
moment card.

## The framework: Prelude is the recap stage of a goal call

**The narration read like a log file, and that is what this section replaces.**
Every sentence was true, every sentence cited its record, and the result was a
list: "Maradona received the ball inside his own half. He dribbled past
Beardsley. He dribbled past Butcher and Fenwick." Nothing in it is wrong.
Nobody talks like that about a goal, and a fan who opens the app to hear what
they missed is owed the thing a commentator would have said.

So the framework below is the standard, settled by Shawn on 2026-10-30 after
researching how commentators actually call a goal. A commentator calling one
live does three things in order: the build while the move is alive, the shout
as it goes in, and then the recap, the move told back over the replay.
**Prelude is the recap.** The app arrives after the ball is in the net, so the
build and the shout are already behind it, and the stadium has the shout
anyway.

**Start at the catalyst, tell the decisive part, land the finish.** Three
positions, in that order, and nothing before or after them. The catalyst is
the touch the move came out of: a recovery, a counter starting. The decisive
part is what a listener would have asked about, which is the run past four
defenders in 1986 and the chain of five passes in 2022. The finish is the
shot, and the last thing said is that it went in.

### What it does

| | |
| --- | --- |
| **Chains** | "Molina to MacAllister", the shortest way to say a pass. A move made of passes is said as its passes. |
| **Action before name** | "a long ball from Álvarez", because the listener is watching the ball, not a team sheet. |
| **Short names, and "he"** | the shortest recorded name that picks out one player, and a pronoun once that player is the one being followed. |
| **Repetition that builds** | "past Beardsley, past Butcher, past Fenwick". The repeat is the point: it is how a listener hears four defenders rather than one. |
| **Past tense** | the passage has already happened, which is the rule the rest of this document was written around. |
| **Football idiom** | "finished with his left", "picked it up", "the counter was on". The words the game is talked about in. |

### What it never does

| | |
| --- | --- |
| **No clock times** | not "54:18", not "in minute 54", not spelled out. The header already says when; a colon between two numbers is read aloud as a colon between two numbers. |
| **No verdicts** | unchanged from `CLAUDE.md`: no nicknames, no epithets, no ranking the goal or the players. |
| **No backstory** | nothing about the match, the tournament or the player before this passage. |
| **No crowd** | the stadium is in the room already. |
| **No full names every time** | a name said in full six times is a document, not a call. |
| **No filler repetition** | the repetition that builds is "past, past, past". Saying "received the ball" four times is not that, and `app/story_beats.py` is what stops it: a receipt is not a beat and is not shown. |
| **No opener two goals share** | an opening line that would fit any goal is an opening line that says nothing about this one. |
| **No move hung off "who"** | "passed to Maradona, who carried it forward, who went past Beardsley" is grounded and is one shape repeated. Rule 14 of the goal-call prompt allows "who" once; the joins are a comma chain, "and", "on to" or a new clause. |

### The beats the model is shown, which are not the records

**A rule the model is told and a list that contradicts it is a rule that does
not hold.** The eighteen candidates of 2026-10-31 said "received, carried and
passed" in almost every telling, and the reason was in front of them: the
prompt printed every recorded event of the passage, and eight of the
twenty-four in 1986 are a ball receipt while seven more are a carry of under
a yard. Nothing in `app/grounding.py` was wrong about any of it. The records
are real; they are simply not beats.

So `app/story_beats.py` curates the passage first, and what the prompt shows
is the result. Each rule is a recorded field read against a threshold
`app/narration_grammar.py` already holds, which is the threshold
`app/grounding.py` refuses the matching word on:

| Kept | What it carries |
| ---- | --------------- |
| the ball recovery | who won it |
| every pass | who it reached, "forward" or "back" off the change in x, "long" at `LONG_PASS_YARDS`, the assist, the box |
| every carry of `RUN_YARDS` or more | that it was a long carry, which way, and whether it ended in the box |
| every dribble past an opponent | both players, as one beat for the two records |
| pressure on the player on the ball | who pressed |
| the finish | the body part, whether it was struck first time, the box |

Dropped: `Ball Receipt*`, because the pass beat already names who the ball
reached, and a carry under `RUN_YARDS`, because a player taking a touch where
he stands is not a turn in the story. `play_pattern` and the own half are
said once, above the list, rather than on every line.

**Two things the beats do rather than leave to the model, and both came out of
reading the run of 2026-11-05 aloud.** No beat carries a yard figure: it
carried the distance in whole yards and every 1986 candidate read it out,
"carried forward thirty-five yards, evaded Reid, beat Butcher, ran forward
seventeen yards", which is grounded and is a stumble. And consecutive dribbles
past one player are one beat naming the defenders in order, with the carries
between them absorbed into it, because a list of beats is read out as a list
of beats: that run wrote "beat Butcher, ran forward seventeen yards, beat
Fenwick, ran forward seventeen yards" where the references say "past
Beardsley, Butcher and Fenwick". A carry that ended in the box ends the group,
which is why Shilton is beaten in a beat of his own.

**The curation can only narrow what a narration may say.** The check still
reads a narration against every record of the passage, so a line about a ball
receipt would still pass it; it will not be written, because the model was
never shown one. Read the two lists with:

    .\.venv-prelude\Scripts\python.exe -I scripts\story_beats_report.py

### How the sentences hold together

Four rules, and they are about the prose rather than about the data:

- **Each sentence carries its claim with its reason.** Not "he carried it
  forward" and then, separately, "he was under pressure": "he carried it
  forward under pressure".
- **Clauses join.** The log file was one claim per full stop. A recap runs
  clauses together, because the move ran together.
- **Each sentence picks up the last one's thread.** The thing the previous
  sentence ended on is what the next one starts from.
- **Setup builds to payoff.** The order is not decoration: the catalyst exists
  so that the finish lands.

**And a telling opens on a name.** Rule 18 of the goal-call prompt asks the
first word of a narration to be a player, a team or a country the records
hold, because a telling that opens on "We" or "It" starts with the listener
rather than with the match. It is not a claim rule: `app/grounding.py` says
nothing about an opener, and `opener_missing` in
`scripts/narrator_candidates.py` is what refuses a candidate that opens
elsewhere, beside the places rule and for the same reason. The six hero
narrations open on Cuciuffo, Maradona, Molina and Argentina. **Four of the
eight references below do not**, and the rule is newer than they are: the
1986 Argentina Buddy opens on "We", the 1986 Caller on "It", the 2022
Argentina Buddy on "We" and the 2022 France Buddy on "In". They are the
standard for the writing and they are still checked word for word; whether
rule 18 should reach them is Shawn's call and nothing here has changed them.

### Each narrator has its own text

**This is the rule that replaces one style for every persona.** The text was
one text from Task 6d, and the personas were separated by sound alone. They
are not any more: a Storyteller recapping a move and a Buddy sitting beside a
fan whose side just scored are not the same sentences spoken differently, and
the four slots below are four pieces of writing.

| Narrator and situation | What its text does |
| ---------------------- | ------------------ |
| The Storyteller | the move told evenly, start to finish, in the third person. |
| The Buddy, the side that scored | the listener's own move, so "we" and "us" are the register, and the finish is the one place a listener cheers. |
| The Buddy, the side that conceded | the same move told without cheering it, and without "we", because the passage records nothing the listener's side did. |
| The Caller | quick, chained, the repetition at its most clipped, ending on the shot. |

**"!" only where the listener would cheer.** That is the sentence that lands
the finish, and the reaction after it where there is one, and only for the
Caller or for the Buddy of the side that scored. The Storyteller does not get
one in any situation, and neither does a Buddy sitting with the side that
conceded. The next section is what the reaction is.

### Two layers: the play and the reaction

**Settled by Shawn on 2026-10-31, after reading the first eighteen candidates
aloud.** The narrations were correct and flat. Every one of them told the move
and stopped, because the framework above is entirely about the move, and a
commentator calling a goal does one more thing: he feels it.

So a narration has two layers, and they are held to different standards.

**THE PLAY** is who, what, where and how it finished. It is checked strictly,
claim by claim, against the records: the names, the chains, the defenders gone
past, the positions on the pitch, which way the ball went, how far a carry
ran, the body part, the first-time flag. Everything in the framework above is
this layer, and so are all eight references.

**THE REACTION** is the narrator feeling the moment: "Oh, lovely!", "What a
finish!", and for the side that conceded "Ah, no.". It follows the listener's
side, and it is not checked against the data, because it claims nothing about
the data. It is not a loosening of the label: "Verified from play data" says
every event happened as told, and the reaction tells no event.

What keeps that true is the shape of the sentence rather than anybody's good
intentions. A reaction is at most eight words, holds no digit, names no player
and no team, uses no "he", "his" or "who", and makes no claim about a recorded
field. A sentence that breaks any of those is play, and is read and refused as
play: "Lovely, Di María!" names somebody, so it is checked like any other
sentence.

**Where it may stand.** Once, at the goal, after the play has landed the
finish, with nothing after it. A reaction before the finish is refused,
because there is nothing yet to react to, and a second one is refused because
the first was the reaction.

**What is still banned in it.** A verdict about history, which needs knowledge
from outside the moment: "the best of all time", "historic", "Goal of the
Century". The data says nothing about where this goal stands among other
goals. Also physical manner the record does not hold: "smashed", "blasted",
"hammered". A shot record carries who struck it, with which foot, from where
and whether it went in, and nothing about how hard. "Finished", "scored",
"struck", "fired", "hit" and "slotted" all stay sayable. And "you", because no
narration is addressed to the fan.

**Which narrator reacts how.**

| Narrator and situation | Its reaction |
| ---------------------- | ------------ |
| The Storyteller | restrained, and it ends on a full stop: this voice notices the goal rather than celebrating it. |
| The Buddy, the side that scored | the one that cheers: the finish takes an exclamation mark and so may the reaction. |
| The Buddy, the side that conceded | subdued, ending on a full stop, or absent: "Ah, no." |
| The Caller | clipped, and it may cheer: "What a finish!" |

**"!" now has two places rather than one.** The sentence that lands the finish
and the reaction after it, for the Caller and for the Buddy of the side that
scored. Nowhere else, and never for the Storyteller or for a Buddy sitting
with the side that conceded.

**The eight references hold no reaction**, and they are still the standard for
the play layer.
`tests/test_reference_narrations.py::TestTheReactionLayer::test_the_eight_references_hold_no_reaction`
reads each one sentence by sentence and asserts so, which is what keeps the
layer an addition rather than a change to what was already settled.

### Which way, how far, and who gave the ball away

**Three claims that used to be prose, settled on 2026-10-31 for the same
reason.** The first eighteen candidates were read aloud and three kinds of
sentence turned out to be wrong in a way nothing could catch:

- **Direction.** "Carried it back to MacAllister" and "slipped it back to
  MacAllister", over a pass that went 38 yards up the pitch. "Forward" and
  "back" are now a claim about the change in x on a pass or a carry, and
  `DIRECTION_YARDS` in `app/narration_grammar.py` is how much of a change
  counts. Nothing in either hero passage moves the ball between 0.8 yards and
  9.0, so the threshold sits in the gap.
- **Distance.** "Drove forward" and "drove ahead", over carries of 0.7 yards.
  "Drove", "ran", "burst" and the words like them now need a recorded carry of
  `RUN_YARDS` or more. Maradona's three long carries are 34.9, 16.8 and 16.7
  yards; every other carry in either passage is 1.1 or less.
- **Who gave the ball away.** "Who carried it back to MacAllister". A carry is
  the record of a player moving with the ball at his own feet, so it never
  delivers the ball to anybody: only a pass does. A chain whose only verb is a
  carry is refused.

### The eight references are the standard

`tests/test_reference_narrations.py` holds eight narrations, the two hero goals
by each of the four narrator-and-side slots, written to the framework above.
They are what the standard means in practice, and the check is held to them
word for word (`tests/test_reference_narrations.py::TestTheReferences`).

The 1986 goal, as the Storyteller tells it:

> Cuciuffo's recovery started the counter, and Enrique played it to Maradona
> just inside his own half, who carried it forward under pressure past
> Beardsley, Butcher and Fenwick and took it into the box, where he went around
> Peter Shilton and scored with his left foot.

and as the Buddy tells it to somebody who supports Argentina:

> We won it back through Cuciuffo and Enrique gave it to Maradona in his own
> half, and from there it was all him: past Beardsley, Butcher and Fenwick, on
> into the box, around Shilton, and he scored with his left foot!

**They are the standard, not the recordings.** Shawn's words, not a model's,
and they never go into a prompt for the two goals they describe: a reference
pasted into that prompt would be dictation, the model would hand it back, and
nothing would have been measured. The style a narrator is shown is worked
through an invented match with invented players instead, which is planned as
Task 9c.

### The recorded fields a goal call says out loud

**Half of the framework is a claim about a field nothing used to read.** "Under
pressure", "a long ball forward", "he set up Di María", "first time", "into the
box", "in his own half" and "in under ten seconds" are not colour: each one is
a StatsBomb field, and a check that cannot see the field cannot hold a
narration to it. So `Beat` in `app/narration_prompt.py` carries them, copied
from the record and never derived:

| Said | Field | What the two hero passages hold |
| ---- | ----- | ------------------------------- |
| "on the counter" | `play_pattern` | "From Counter" on every record of both |
| "under pressure" | `under_pressure` | all nine of Maradona's records from his first touch; nothing in the 2022 counter |
| "Molina to MacAllister" | `pass.recipient` | the full recorded name of the player each of the five 2022 passes reached |
| "a long ball forward" | `pass.length` | 20.1, 11.6, 11.5, 38.5 and 26.0 yards in 2022; the 38.5 is the long ball |
| "he set up Di María" | `pass.goal_assist` | one pass per passage: Enrique's in 1986, MacAllister's in 2022 |
| "first time", "with one touch" | `shot.first_time` | true on the 2022 shot, absent on the 1986 one |
| "with his left foot" | `shot.body_part` | Left Foot on both goals |

Two of them are arithmetic rather than a copy, and the arithmetic is the
pitch's own rather than a reading of the play. **Field position** is one
coordinate against one line: StatsBomb's pitch is 120 by 80 and `x` runs
towards the goal the record's own team is attacking, so `x < 60` is that
player's own half and `x >= 102` is inside the box, and a defensive record is
mirrored so the same two lines read correctly for either side. Maradona
received it at `x` 55.2, which is "just inside his own half" by under five
yards, and the carry that ends his run ends at 112.8, which is "into the box".

**The same arithmetic at the resolution a commentator speaks at** is
`app/pitch_zones.py`, which Task 13 added after Shawn read the six
candidates of 2026-11-05 aloud and found that none of them places the
move: "dribbled past Butcher" and "a long ball to MacAllister" leave a
listener with nowhere on the pitch to stand. It is eight bands of `x`
and three of `y`, each one a phrase and each one a claim: "deep in his
own half" is `x` under 40, "just inside his own half" is 50 to 60,
"just inside their half" is 60 to 70, "in the final third" is 80 up,
"on the edge of the box" is 96 to 102 within the box's width, and "on
the left" and "on the right" are the pitch outside the sides of the
penalty area, `y` under 18 and over 62. The sides were the outer thirds
of the pitch first, 26.7 and 53.3, and Task 14 moved them: four beats
between `y` 54.9 and 60.5 were "on the right" by a yard or two, and
three of them fell in one line. A side is said only where the ball is
clear of the middle now, so nine of the twelve places the two hero
passages carry are said with no side at all. The bands are exclusive, so a phrase naming the wrong one is
refused: Cuciuffo won the ball back at `x` 35.2, and "just inside his
own half" over it is a wrong place although it is indeed his own half.
The two broad phrases above are not bands and are read as the half and
the box they always were, which is what three of the eight references
say.

**A half can be said with a possessive, and whose half it is depends on
who is listening.** "Deep in our own half" is the deep part of whichever
half the listener's side defends, so the one place Molina played the 2022
counter from is "deep in our own half" to an Argentina fan and "deep in
their own half" to a France fan; said the other way round, to an
Argentina fan, "deep in their own half" is a patch of France's half
ninety yards from the ball and is refused. "Our half" and "their half"
with no "own" in them are the same resolution: "just inside our half" to
a France fan is where the long ball was struck, `x` 63.2 from
Argentina's end and 56.8 from France's. The resolution is the listening
side the check was given, and a narration written for nobody cannot say
"our" at all, so there "their own half" is the half the side on the ball
defends and "their half" is the opponent's, which is what the vocabulary
spells them as. A half said with a team's own name is held to the side
being attacked, and a curly apostrophe in "France's" is read as a
straight one.

**Duration** is the difference between two timestamps. The `minute` and
`second` fields floor the clock, so the 2022 counter reads as exactly ten
seconds by them and "in under ten seconds" would be false; the timestamps say
00:35:12.890 to 00:35:22.647, which is 9.757. The 1986 run is 15.7 seconds,
which no reference says, because what is worth saying about that passage is who
was beaten.

`LONG_PASS_YARDS` is the one number here somebody could argue with, because it
is a threshold and not a record. It is thirty, which is in the gap between the
26.0 yard assist and the 38.5 yard ball a commentator calls long, so it
separates these two passages rather than settling what a long ball is in
general. Every field above has a test of its own in
`tests/test_narration_prompt.py::TestTheRecordedFieldsTheFrameworkSaysOutLoud`.

**All eight pass, and the check reads them as prose.** A goal call carries no
fact numbers, so `app/grounding.py` has two readings now and the narration's
own shape picks one: a sentence with a citation tag is read against the facts
it cited, and a narration with no tag anywhere is read as a goal call by
`app/narration_grammar.py`. What that grammar reads is the list under "What it
does" above, and the section after this one is how each piece of it works.

The other half of the standard is the lines the check has to keep refusing. Each
is one of the references with one thing changed, and every one of them is now
refused by the grammar reading the change rather than by the narration citing
nothing: the refusal names the chain, the shared forename, the curve in the
carries, the side the records put the play on, the exclamation mark or the
clock.

| Refused | Why | Test |
| ------- | --- | ---- |
| "Molina to Messi" | Molina's one pass in that passage has MacAllister as its recipient | `TestAChainTheRecordsDoNotHold` |
| "Terry", "Peter" | two and three players in the 1986 buildup answer to each | `TestANamePartTwoPlayersShare` |
| "straight into the box" | the carries run out to the touchline and back | `TestAClaimAboutTheShapeOfTheCarry` |
| "we" from the France fan's Buddy | all thirteen records in the 2022 passage are Argentina's | `TestTheFirstPersonNeedsTheListenersOwnPlay` |
| "!" before the last sentence, or from the Storyteller, or from a conceding Buddy | nobody cheers there | `TestWhereAnExclamationMarkMayStand` |
| any clock | the framework has none | `TestNoClockReachesTheNarration` |

### How the grammar reads a goal call

`app/narration_grammar.py` turns a sentence into the moves it makes, in the
order it makes them, and `app/grounding.py` refuses any move no record holds.
Six decisions in it are worth reading twice.

**A short name has to pick out one player.** Every contiguous run of words of
every recorded spelling is a name the narration may use, so "Shilton", "Peter
Shilton", "MacAllister" and "Di María" all resolve, and a run that fits two
players resolves to neither: "Terry" is Butcher and Fenwick, and "Peter" is
Beardsley, Reid and Shilton. That is the price of short names, and the narration
pays it rather than the listener
(`tests/test_narration_grammar.py::TestTheNamesAGoalCallMaySay`).

**"He" is the player with the ball.** It resolves to the most recently named
player with a recorded touch, which is the player the move is following. The
plainer rule, the most recently named player of any kind, gets the
Storyteller's own line wrong: "past Beardsley, Butcher and Fenwick and took it
into the box, where he went around Peter Shilton" names three defenders between
Maradona and the "he" that means him, and none of the three has a touch in the
passage. Being beaten is not having the ball
(`tests/test_narration_grammar.py::TestThePlayerAPronounMeans`).

**A chain is a recorded pass, in whichever words it was said.** "Molina to
MacAllister", "played it to", "gave it to", "moved it on to" and "found" are
one claim: a `Pass` by the first player whose recorded recipient is the second.
"Set up" is the same claim with `goal_assist` on it, and "a long ball" beside a
chain is folded into it, so one record has to be both long and the pass to that
player (`tests/test_narration_grammar.py::TestTheChain`).

**Which player owns a claim is read from the words around it.** A name before
it owns it, two names before it both own it ("Beardsley and Reid closed him
down" is two `Pressure` records), a name after it owns it when none came
before, which is the framework's action before name, and with no name either
side it belongs to the player with the ball. A name on the other side of a
comma owns nothing: without that, "picked it up in his own half, and though
Beardsley and Reid closed him down" puts Beardsley in his own half, where this
passage never records him
(`tests/test_narration_grammar.py::TestTheActorOfAClaim`).

**"Past X" is two records, paired by the clock.** A `Dribbled Past` on the
defender and a `Dribble` by the player following the move, at the same minute
and second. That is the misdescription rule the cited reading already had, said
in the goal call's own words: "past Peter Reid" is refused because Reid's one
record in the passage is a `Pressure`
(`tests/test_narration_grammar.py::TestPastAndAround`).

**A position is where the player was, not where the ball went.** The start of
each of their records, and the end of each of their carries, because a carry is
the one record that moves the player rather than the ball alone. MacAllister's
assist ends inside the box and he played it from four yards outside it, so
counting a pass's end would put him in the box
(`tests/test_narration_grammar.py::TestWhereOnThePitch`).

**And "straight" is refusable, which is the one claim about a shape.** The
largest distance from the line between where a run started and where it ended:
Maradona's five carries stray sixteen yards from it, out towards the touchline
and back, so "straight into the box" is refused over a run that curves
(`tests/test_narration_grammar.py::TestTheShapeOfTheRun`).

**What it still cannot read.** Direction. "Forward" is prose here, so a
narration that said "backward" would not be refused for it, and the same goes
for "turned", "advanced" and "the whole way": the lexicon is narrow on purpose,
like `ACTION_CLAIMS`, and a word that is not in it is checked against nothing.
The pairing is blunt in the same way the cited reading's is: a clause with two
claims and two free names pairs both with both. And one rule is specified and
unexercised, because this data cannot exercise it: `play_pattern` belongs to
the possession, so every record of a passage carries the same one and both hero
passages are "From Counter" throughout, which leaves no false pattern claim to
make
(`tests/test_narration_grammar.py::TestTheRecordedFieldsSaidOutLoud::test_no_pattern_claim_can_be_refused_with_this_data`).

### What is still one style in the code

`NARRATION_STYLE` in `app/narration_prompt.py` is the Storyteller's text and is
printed under "THE STYLE" in every prompt, whoever is listening, and
`build_prompt` still takes no persona
(`tests/test_narration_prompt.py::TestTheOneNarrationStyle::test_the_prompt_takes_no_persona_and_no_side`).
That is the code as it stands, not the standard: a style per narrator is
planned as Task 9c, and until it lands the prompt asks for one register and
the four slots above exist only in this document, in the references and in what
the check will now accept.

The three measured sections further down are why one style was the rule before
this one, and they are worth reading before a style per narrator is written:
three ways of asking for three registers were tried against three models, and
each gave one register back. What is different now is that the registers are
written out as finished text rather than described to a model as an
instruction.

## The three personas and their voices

| Persona | Id | Voice | What it sounds like | Offered to |
| ------- | -- | ----- | ------------------- | ---------- |
| The Caller | `caller` | `en-AU_HeidiNatural` | quick play-by-play, keeping up with the move | everyone |
| The Storyteller | `storyteller` | `en-US_EmmaNatural` | calm documentary, unhurried and even | everyone |
| The Buddy | `mate` | `en-US_EthanNatural` | warm, from the next seat | fans only |

**What does not differ between them is what is refused.** The text is four
texts now, and `app/grounding.py` holds all four to the same records:
`BANNED_PATTERNS` refuses the same nicknames, epithets and outcome claims
whoever is listening, and no narrator may say a name, an action or a body part
the data does not hold. A narrator picks the words; it never widens what the
words may claim, because "Verified from play data" cannot mean one thing for a
fan and another for a neutral listener.

**The three voices are Shawn's picks and the config records them.** `voice` is
set on all three and `voice_confirmed` is true, which says the value was chosen
by somebody entitled to choose it rather than that this repo listened to it:
`tests/test_personas.py::TestTheVoices`. The ids are pinned to the three the
probe measured, because a voice nothing has measured has no known delivery
controls
(`tests/test_personas.py::TestTheVoices::test_every_voice_is_one_the_probe_measured`).

**Comprehension comes first.** The Caller is the quick one, and its energy
comes from emphasis and pitch rather than from speed: a rate far above the
Storyteller's would cost a listener the names and the clock, which are the
whole of what the narration carries. So the rate sits only modestly above the
Storyteller's and has a ceiling. Breaks between sentences let each beat land,
with a slightly longer one before the goal sentence, and the probe is why that
is the Caller's alone: `<break>` works on its voice and on neither of the other
two. Shawn sets the numbers by ear, words per minute is measured from the real
audio, and the measured ceiling goes into config.

**The four prosody fields are empty and marked unconfirmed.** Each persona
carries `rate`, `pitch`, `sentence_break` and `goal_break`, every one of them
`None`, with `prosody_confirmed` false beside them. Nobody has set them by ear
yet, and a plausible value written down now would be a guess with the look of a
decision: `tests/test_personas.py::TestTheProsodyIsSet`. The two breaks
are milliseconds so the one before the goal can be read against the one
between sentences; the rate and the pitch are percentages written as the
strings the request carries, and they are request parameters rather than SSML,
because `<prosody>` is ignored on all three of these voices.

**Inspired by styles, never named after anybody.** Each name is what the
persona does rather than who it resembles. Naming a real commentator would
claim a likeness this repo has no data for, and it would put a judgement about
a person into app output.
`tests/test_personas.py::TestProfileCopy::test_no_persona_is_named_after_a_person`
holds the names to "The" and one common noun, and
`tests/test_personas.py::TestProfileCopy::test_no_verdict_nickname_or_epithet`
scans the Profile lines for the words `CLAUDE.md` keeps out of app output.

**It is the Buddy, in the app and in the code.** "Mate" read British in a
North American market, so on 2026-10-30 `app/personas.py` renamed the display
name to "The Buddy", and Bob's Task 13 renamed the id to `buddy` with it, in
`4e61a10`. No live file says Mate, and
`tests/test_buddy_rename.py::test_no_live_file_says_mate` is what holds that.

**The run records below keep the old name**, because the past is not renamed.
A run made while the persona was the Mate is reported as it happened, and the
sample files it wrote are still called `1986_mate_scored.wav`. Everything in
this file that describes how the app works now says the Buddy, which is what
the code says.

**The Buddy is the only one that needs a side.** It is the one voice that makes
no sense without an allegiance: told to a neutral listener it would be saying
they support a team they did not choose. `fans_only` is true for it and false
for the other two, and `available` in `app/personas.py` is what leaves it out
for a neutral listener.
`tests/test_personas.py::TestFansOnly::test_a_neutral_listener_is_not_offered_the_buddy`
covers that, and
`tests/test_personas.py::TestFansOnly::test_the_default_for_a_neutral_listener_is_one_they_may_choose`
covers the disagreement that would not otherwise show up: `default_persona` in
`app/orchestrator.py` returns an id and reads nothing in this config, so a
default that was fans only would hand a neutral listener a persona the Profile
screen then refuses to show them.

### The first person belongs to the Buddy, over the listener's own play

**"We" is the Buddy's register again, and it is earned record by record.** The
framework gives the Buddy of the side that scored the listener's own move, so
"We won it back through Cuciuffo" is the reference rather than a drift to be
caught. What the word may stand on has not moved: the listener's side has to
have done something the records hold, and the Buddy of the side that conceded
gets no "we" in these two passages at all, because every record in the 2022
counter is Argentina's
(`tests/test_reference_narrations.py::TestTheFirstPersonNeedsTheListenersOwnPlay`).

**The prompt still refuses it, and that is the gap.** `build_prompt` rejects
the first person in the one voice it has
(`tests/test_narration_prompt.py::TestTheOneNarrationStyle::test_the_prompt_refuses_the_first_person_in_the_one_voice_it_has`),
which is the rule from Task 6d and not the framework above. A style per
narrator, with the first person allowed to the one narrator that has a side, is
planned as Task 9c.

The word was taken out for a reason worth keeping in view. The Mate was written
as the listener's side from Task 6b to Task 6d, and what a model wrote with
that permission was "Our Peter Beardsley was dribbled past at 54:08." and "We
were dribbled past, Peter Beardsley.", five times over. That is the first
person attached to the wrong records, which is exactly what the side rule
below refuses; the references show the same permission used on the right ones.

**The guard in `app/grounding.py` is what the framework now leans on.** `check`
refuses "we", "our" and "us" from every persona but a partisan one, and from a
partisan one unless a cited fact is recorded against the listener's side. It
was written as a guard behind a prompt that asked for less; it is the live rule
now.

| Voice | "we", "our", "us" | "you", "your" |
| ----- | ----------------- | ------------- |
| no persona | refused | refused |
| the Caller | refused | refused |
| the Storyteller | refused | refused |
| the Buddy, with a side | admitted over that side's facts | refused |
| the Buddy, with no side | the check itself is refused | refused |

**A partisan sentence has to cite the listener's side.** One cited fact
recorded against that side is enough, which is the same shape as a name claim:
a name is grounded when some cited fact holds it, not when every cited fact
does. Requiring all of them would refuse "[10, 11] We dribbled past Peter
Beardsley", which cites the two records of one dribble and is true for an
Argentina listener
(`tests/test_grounding.py::TestThePartisanVoice::test_both_records_of_one_dribble_ground_it`).

The pair of tests that makes the rule concrete is one sentence cited two ways.
"[11] Our captain dribbled past a defender." is grounded for an Argentina
listener, because fact 11 is Maradona's `Dribble`. The same sentence citing
fact 10, Beardsley's `Dribbled Past`, is refused, because that record is
England's
(`tests/test_grounding.py::TestThePartisanVoice::test_our_citing_the_listeners_team_passes`
and
`tests/test_grounding.py::TestThePartisanVoice::test_the_same_sentence_citing_the_other_team_fails`).
Nothing in the words tells the two apart. What decides it is the team on the
record the sentence cited.

**"You" is refused in every voice, the Buddy included.** The narration is not
addressed to the fan in any register, which is the ending rule below: the
header goes before the narration and nothing goes after it.
`tests/test_grounding.py::TestThePartisanVoice::test_you_is_refused_from_the_buddy_too`
holds the partisan voice to it.

**A Buddy narration from a neutral listener is refused rather than softened.**
`check` raises `NoSideForAPartisanVoice`. Checking it as though nobody were
partisan would admit "we" with no side behind it, and picking a side would
tell a listener they support a team they did not choose.

### Measured once: the three voices came back nearly the same

The next three sections are the measurement behind one style for every
persona, which is the rule "The framework" above replaced. All three ran against code that has since been removed: each persona
carried a `style` that the prompt printed, and from Task 6d a worked `example`
of its register as well. `docs/narration_eval.md` holds the numbers and labels
every section of them the same way.

The first run is 36 narrations over three goals, three runs of each of four
voices per goal, on `granite4:micro`.

**The registers did not reach the model.** Words per sentence, the one thing
in those styles that could be measured without a judgement, came out between
4.9 and 5.5 for every voice, including the Caller, whose style asked for short
lines, and the Storyteller, whose style asked for measured ones. The sample
narrations printed in the report read alike for the same reason.

**The Mate never took the first person.** Of 18 narrations written in that
voice, none used "we", "our" or "us". The permission was in the prompt and in
the check, and nothing required it.

**The style block cost first-attempt grounding.** On the 54:18 goal, Task 4c
measured 3 of 3 first attempts grounded with no persona; with a persona, the
same goal came out 3 of 12. Retries absorbed most of it, and the after-retry
figure is 10 of 12, which is why the report prints both.

### Measured again on the paid models

Task 4b ran both watsonx candidates over the same goals, through the chat
endpoint, with the decoding pinned the same for each. `docs/narration_eval.md`
holds it. Three things it settles about this document.

**A bigger model honours the rules.** `openai/gpt-oss-120b` wrote 33
narrations and `app/grounding.py` accepted every one on the first attempt,
with no retry and no fallback, at full coverage. Everything above (the
citations, the past tense, the ending on the goal, the pairing rule) is
reachable; the thin and refused narrations in the earlier sections are a
three billion parameter model's limit rather than the prompt asking for the
impossible.

**The registers still did not separate, on either paid model.** Words per
sentence spread 2.0 across the voices for `openai/gpt-oss-120b`, against 0.6
on the development model, and the narrations it wrote for the Caller, the
Storyteller and the Mate on the 54:18 goal are the same five sentences with
different punctuation. The styles were read and obeyed as rules and not as a
voice.

**The Mate did take the first person, and it read badly.** It used "we",
"our" or "us" in 9 of its 12 narrations on `openai/gpt-oss-120b`, against none
on either smaller model, so the permission was reachable too. What it produced
is "Our Peter Beardsley was dribbled past at 54:08." and "We, Nicolás Hernán
Otamendi, pressed, 78:11.": the possessive grafted onto a name rather than a
supporter telling a friend what happened. The grounding check accepted it,
correctly, because every cited fact was the listener's side. The rule was
doing its job and the prose was not, and nothing in this repo refuses a
narration for being stilted.

### Measured a third time: showing the register changed almost nothing

Task 6d gave each persona a worked example of its register, a short narration
of an invented passage, printed in the prompt for the model to copy rather
than to interpret. Measured the same way, on `openai/gpt-oss-120b`, over the
two goals the persona arm used, 16 narrations. `docs/narration_eval.md` holds
it.

| | Described | Shown |
| --- | ---: | ---: |
| grounded on the first attempt | 16 of 16 | 16 of 16 |
| narrowest voice, words per sentence | 5.9 | 5.6 |
| widest voice | 8.0 | 7.5 |
| spread across the voices | 2.1 | 1.9 |
| the Mate's narrations using the first person | 5 of 8 | 6 of 8 |

**The voices did not separate.** The spread narrowed rather than widened, and
on the 54:18 goal the Caller, the Storyteller and the Mate for an Argentina
listener wrote the same five sentences, differing in whether a clock is
introduced by a comma or by "at". Showing the register did not work where
describing it had not.

**The one thing that did move is the Mate, and not in the direction the
example was written for.** The example said "We recovered it through
Quillan". What came back for an England listener is:

> We were dribbled past, Peter Beardsley. We were dribbled past, Terry
> Butcher. We were dribbled past, Terry Fenwick. We were dribbled past, Peter
> Shilton. Diego Armando Maradona shot.

That is an apposition inverted: the name trails the clause instead of
interrupting it. It was grounded, because every cited fact is England's, and
it is five sentences of the same sentence.

**Nothing was paid for in grounding.** All 16 passed on the first attempt, as
all 16 did before the examples, so the examples were inert rather than
harmful. That is the whole of what three attempts showed: the grounding rules
leave no room for a writing style, so the style text and the examples came out
and the personas became voices.

## What the three voices can actually be told to do

The personas are separated by sound, so the first question of Phase 5 is which
controls the service will take. It is not a question a spec sheet answers:
IBM's own documentation says the `<prosody>` element is not supported for
Natural voices and that the service **silently ignores** unsupported SSML, so a
delivery table written against it would be a page of numbers that change
nothing, and the request would be well formed and the response would be audio.
Nothing would fail.

`scripts/tts_probe.py` is what measured it instead. Six arms per voice, the
same sentence in each, 18 calls and 642 submitted characters. The numbers below
are its output.

| Control | en-AU_HeidiNatural | en-US_EmmaNatural | en-US_EthanNatural |
| ------- | ------------------ | ----------------- | ------------------ |
| `rate_percentage`, both ways | works | works | works |
| `pitch_percentage`, upward | works | works | works |
| `pitch_percentage`, downward | ignored | ignored | ignored |
| `<break time="600ms"/>` | works | ignored | ignored |
| `<phoneme>` | works | works | works |
| `<prosody rate>` | ignored | ignored | ignored |
| `<prosody pitch>` | ignored | ignored | ignored |

"Ignored" is not a reading below a threshold. Those responses came back **byte
for byte identical** to the plain request, same SHA-256: the same voice, asked
for something different, returned the same file. That is the only evidence that
settles the question, because a control that does nothing and a control that
does something too small to hear look alike in any other measure.

**Duration cannot see a pitch change, so the probe measures f0 as well.** A
pitch shift leaves the length of the audio exactly where it was. The estimate
is an autocorrelation over the voiced frames, and it checks out against the
service's own arithmetic: a 20 percent rise predicts 3.16 semitones and the
three voices measured 3.16, 2.67 and 3.16.

| Voice | plain | `rate_percentage` -20 | +20 | `pitch_percentage` +20 | `<break>` 600ms |
| ----- | ----: | --------------------: | --: | ---------------------: | --------------: |
| en-AU_HeidiNatural | 2.16s, 222.2 Hz | 2.46s | 1.91s | 266.8 Hz | 3.52s |
| en-US_EmmaNatural | 2.30s, 214.3 Hz | 2.62s | 1.85s | 250.0 Hz | no change |
| en-US_EthanNatural | 2.30s, 166.7 Hz | 2.85s | 1.87s | 200.0 Hz | no change |

Three things in that table are worth saying out loud, because each one costs
the delivery something.

**The break works on one voice of the three.** IBM labels `<break>` beta for
Natural voices and says the timing may vary. On Heidi a 600 ms break added
1.36s, so "may vary" is doing real work; on Emma and Ethan it changed nothing
at all. A pause between sentences and a longer one before the goal are
therefore available to the Caller and to nobody else.

**Pitch moves up and not down.** `pitch_percentage` of +20 works on all three
voices and -20 is ignored on all three, which was measured twice in two
separate runs. It is not simply that negatives are refused: an earlier arm at
-50 halved Heidi's pitch exactly, 222.2 Hz to 111.1 Hz, which is the -12.00
semitones IBM documents. Somewhere between -50 and -20 the parameter stops
being honoured, and this repo does not know where. So a persona that wants to
sit lower than another cannot be set there by lowering it; what it can do is
leave it alone while the others rise.

**The two parameters are per request, not per sentence.** They go in the
address rather than in the text, which is why they cost no billable
characters, and it is also why one narration gets one rate and one pitch. A
rate that changed at the goal would be two requests and two files.

**Nothing above is a delivery.** It is the list of what a delivery may be
written in. The values are Shawn's, by ear.

**One arm of the probe is worth copying the next time, and one is worth not
repeating.** Asking a control for what the voice already does cannot tell
"honoured" from "ignored": both give identical audio. The pronunciation arm
fell into exactly that, and the fix was to ask for something plainly wrong and
watch the audio change. Any future control gets measured that way.

The second mistake was reading one sentence as a verdict on a word, which
nearly cost the pronunciation table its only entry. The probe speaks a fixed
sentence; the app speaks a different one. A control measured here is measured
on that fixed sentence, and that is all it is measured on.

## The delivery table: persona by situation

`app/delivery.py` is the table. Eight rows, keyed by persona and situation,
and the values are Shawn's, set by ear. The shape and the rules were built
first and the numbers went in afterwards, which is what made filling it in an
edit to one file and a run of the suite.

**The situation is read off the moment and the listener, never from a model.**
`situation` in `app/delivery.py` takes a `ScoringMoment` and a `Listener` and
has no parameter for the narration text, which is what makes that a property
of the signature rather than a promise in a comment
(`tests/test_delivery.py::TestNothingHereReadsTheNarration::test_situation_takes_a_moment_and_a_listener_only`).
A delivery chosen from the text would be a model deciding how a fan should
feel about a goal, off the same text `app/grounding.py` is holding to the
records.

| Situation | What it is | Where it comes from |
| --------- | ---------- | ------------------- |
| `scored` | the listener's side scored | `outcome` in `app/orchestrator.py` |
| `conceded` | the other side scored | the same |
| `neutral` | the listener has no side | the listener's allegiance |

The same goal is two situations for two listeners, which is the whole reason
the table is keyed this way
(`tests/test_delivery.py::TestTheSituations::test_the_same_moment_is_two_situations_for_two_listeners`).

**Only the controls the probe found working are in the table.** The columns
are not a plan; they are what the three voices honour.

| Persona | Situation | `rate` | `pitch` | `sentence_break` | `goal_break` |
| ------- | --------- | -----: | ------: | ---------------: | -----------: |
| The Caller | scored | +10 | | 200 | 400 |
| The Caller | conceded | 0 | | 200 | 400 |
| The Caller | neutral | +10 | | 200 | 400 |
| The Storyteller | scored | 0 | | not available | not available |
| The Storyteller | conceded | 0 | | not available | not available |
| The Storyteller | neutral | 0 | | not available | not available |
| The Buddy | scored | +10 | +10 | not available | not available |
| The Buddy | conceded | -10 | 0 | not available | not available |

An empty pitch cell is `None`, the parameter not sent at all. `0` is the
parameter sent at the voice's own value, which the re-recorded golden shows
produces byte-identical audio: `rate_percentage=0` and no `rate_percentage`
sound the same. They are still different requests, and the table keeps the
difference because "this was decided and it is zero" and "this was not
decided" are different statements.

Three things in that table are decisions worth reading twice.

**The Caller slows to the voice's own rate when the other side scored.**
Hurrying a fan through a goal against them is the Caller's version of being
cheerful about it. Its pauses do not change with the situation, because a
pause is about letting a sentence land and that does not depend on who scored
(`tests/test_delivery.py::TestTheValuesAreShawnsAndTheTableSaysSo::test_the_caller_pauses_the_same_way_in_every_situation`).

**The Storyteller is the same in all three situations**, which is what makes
it the one the other two are set against. Three identical rows are not a table
that wants collapsing: the Storyteller sounding the same whoever scored is a
decision about this persona, and a row per situation is what lets that change
for one situation later without the shape changing.

**The Buddy lifts for your goal rather than dropping for theirs.** +10 rate and
+10 pitch when your side scored, -10 rate and pitch back to 0 when the other
side did. It goes up rather than down because down is not available: a
`pitch_percentage` below zero is ignored by the service, so 0 is the floor and
the only way for one row to sit under another is to let the other rise.

**The pauses are short, and short was measured rather than guessed.** The
probe found a requested 600 ms arriving as 1.36s on the Caller's voice, so a
request lands at roughly twice what it asks for: 200 and 400 are about 450 ms
between sentences and 900 ms before the goal.

**Eight rows and not nine.** The Buddy is `fans_only`, so there is no neutral
Buddy row to write: a partisan voice told to a listener with no side would be
telling them they support a team they did not choose. Asking for that row
raises, and the message says why rather than returning a default delivery that
would sound like nothing was chosen
(`tests/test_delivery.py::TestLookup::test_the_buddys_neutral_row_says_why_it_does_not_exist`).

**The two break columns are the Caller's alone**, because `<break>` moves its
voice and neither of the other two. A pause written on the Storyteller or the
Buddy is refused rather than sent and ignored
(`tests/test_delivery.py::TestOnlyTheCallerMayPause`). That rule reads
`breaks_work` on the persona, which is where the measurement lives, beside the
voice it is about.

**Pitch has a floor of zero**, which is not a view about how low a voice
should sit. A lowered pitch is ignored by the service, so writing one would be
a value that looks like a decision and does nothing, and a value that does
nothing is worse than no value at all
(`tests/test_delivery.py::TestTheBounds::test_a_lowered_pitch_is_refused`). A
persona meant to sit under another gets there by leaving its own pitch alone
while the others rise.

**The rate's bounds are IBM's**, not this app's: below -50 begins to cost
pronunciation and above 100 sounds no different from 100. The Caller has a
tighter ceiling than that, because comprehension comes first, and the number
is owed rather than invented: it is words per minute measured off real audio,
nothing has measured it, and `CALLER_RATE_CEILING` is `None` until something
does
(`tests/test_delivery.py::TestTheValuesAreShawnsAndTheTableSaysSo::test_the_callers_rate_ceiling_is_not_measured_yet`).

**`None` is not zero.** `None` is the parameter not being sent; zero is
sending it at its neutral value. They are different requests, so they are
different values in the table
(`tests/test_delivery.py::TestTheBounds::test_none_is_not_zero`).

### The Buddy is never cheerful when the other side scored

This is the one rule in the table that is about taste rather than about what
the service honours, and it is the one worth a test of its own. A voice that
brightens over a goal against your team is a voice that was not listening with
you.

Brighter and quicker is what cheerful is made of in the only two controls
there are, so the rule is written as a comparison between the Buddy's own two
rows rather than as a fixed number: the conceded row may not carry more pitch
than the scored row, and may not carry more rate either
(`tests/test_delivery.py::TestTheBuddyIsNeverCheerfulWhenTheOtherSideScored`).

A comparison rather than a number is the only thing that can be stated while
the table is empty, and it is also the right shape once it is full: it survives
Shawn filling both rows in by ear in one sitting, whatever numbers he picks.

The rule is "never brighter", not "always duller". A Buddy that sounds the same
either way is not cheerful about a goal against the listener's team; it is
even, and that is allowed
(`tests/test_delivery.py::TestTheBuddyIsNeverCheerfulWhenTheOtherSideScored::test_the_same_delivery_in_both_is_allowed`).

It does not fire on the other two personas. Neither is partisan, so a brighter
conceded row there is not a voice celebrating against its own listener. It may
still be wrong by ear; it is not wrong by rule.

## How a word is said, which is not what it says

`<phoneme>` is the one SSML element that works on all three of these voices,
and `app/pronunciation.py` is the table: word to IPA, with three entries,
`lead` to `liːd`, `minute` to `ˈmɪnɪt` and `close` to `kloʊz`. `lead` was the
first, and it is the one Shawn has heard both ways.

It is there because "lead" is two words in English. The metal is `lɛd` and the
thing a team takes is `liːd`, and the header says "take the lead" on two of
the five transitions in `app/orchestrator_contract.py` and "extend the lead"
on a third. That is a word the app says out loud on most goals.

**That the element works took two measurements, and the first one was
worthless.** Asking for `liːd` returned audio byte for byte identical to the
same sentence with no element at all, on all three voices, which reads exactly
like the `<prosody>` result and means nothing of the kind. An element asking
for the pronunciation a voice already uses produces identical audio whether it
was honoured or thrown away, so the arm could not tell the two apart.

The arm that could is the one asking for the wrong pronunciation: `lɛd`, the
metal. That changed the audio on all three voices, 96538 bytes to 94138 on
Heidi, 77938 to 82738 on Emma and 93538 to 101938 on Ethan. The element is
honoured.

### The entry is needed, and the probe is not what shows it

**The sentence the probe measured is not the sentence the app says.** The
pronunciation arms spoke "Argentina take the lead.", and the identical audio
for a `liːd` request on that sentence means the three voices say *that*
sentence correctly unaided. It says nothing about any other sentence, and the
header both hero goals actually carry is "Argentina **extend** the lead."

Shawn listened to that one, which is the measurement that counts here:

| Sentence | Without the entry | With the entry |
| -------- | ----------------- | -------------- |
| "Argentina extend the lead." | "led" | "leed" |

So the entry is doing real work on the shipped path, and a context one word
away from the probe's is enough to change which word the voice picks.

**An earlier version of this section had it backwards.** It read the probe's
identical audio as proof that the entry changes nothing audible and said Shawn
could drop it and lose nothing. That was a conclusion about "take the lead"
written as though it were a conclusion about "lead", and the sentence the app
ships says "extend". The entry stays, and nothing is spent re-proving it: a
listener heard the difference, which is the evidence this question takes.

**It is also the general lesson twice over.** The first mistake was asking a
control for what the voice already did; the second was measuring one sentence
and generalising to a word. A pronunciation is a property of a word in a
context, so the next entry gets judged on the sentence the app will actually
say.

### The second entry: "minute"

| Word | IPA | Sentence | What the voices did | Heard by |
| ---- | --- | -------- | ------------------- | -------- |
| `lead` | `liːd` | "Argentina extend the lead." | "led" | Shawn |
| `minute` | `ˈmɪnɪt` | "Minute 54." | "my-NEWT" | Shawn, all three voices |

All three voices read "Minute 54." as the adjective meaning tiny. In this app
the word only ever means the unit of time: it reaches speech from
`template_narration` in `app/narration_prompt.py`, which opens a narration on
the clock, so this is the first sentence of most of what a fan hears.

**The voices were not misreading it.** The CMU Pronouncing Dictionary lists
`M AY0 N UW1 T` and `M AY0 N Y UW1 T` beside `M IH1 N AH0 T` for that
spelling. Both are real pronunciations of the written word, and nothing in
"Minute 54." tells a voice which one is meant: the written form is genuinely
ambiguous and no amount of context resolves it, which is exactly what the
`<phoneme>` element is for.

That is the pattern worth noticing. Both entries so far are heteronyms, both
were caught by a person listening after the fact, and both were predictable
from a dictionary before anybody listened. Which is what the check below is.

### Looking the vocabulary up instead of waiting to hear it

`scripts/check_vocabulary.py` collects every word the app can speak and reads
it against the CMU Pronouncing Dictionary. A spelling with more than one
listed pronunciation is a word that may come out wrong, so it is reviewed
once: it either gains an entry in `app/pronunciation.py` or goes on
`CHECKED_NO_ENTRY_NEEDED` there with the reason it needs none.

None of the vocabulary is typed out in the checker, which is what keeps it
honest as the app grows:

| Source | What it contributes |
| ------ | ------------------- |
| `HEADER_WORDING`, `SCORE_LINE`, `HEADER_TAIL` | the header, every transition |
| `EVENT_VERBS` | how each event type is said |
| `template_narration`'s own words | "Minute", "shot and scored for" |
| `app/web/matches.json` | the team names |
| `tests/golden/` | the words in the recorded narrations |

On this commit that is 54 words, of which the dictionary flags 19.

**One of the nineteen was a real find.** "close" is a heteronym, `K L OW1 S`
against `K L OW1 Z`, and the app says it in exactly one place:
`HEADER_WORDING[CLOSE_GAP]`, which is "{scorer} close the gap." That is the
verb, so a voice reading it as the adjective would be saying a different word.
It is the third entry in the table and the first that came from the dictionary
rather than from a listener. Nobody has heard it, and nobody has heard
"minute" either; Shawn confirms both after the November 1 reset. "lead" is
not waiting on anything: he heard that one with its entry in his own test and
again in the hero samples, which carry it.

**Sixteen are reviewed and need nothing**, and the reasons are in
`app/pronunciation.py` beside each one. They fall into two kinds, neither of
which is a risk:

| Kind | Words | Why it does not matter |
| ---- | ----- | ---------------------- |
| full against reduced forms | a, an, and, as, for, in, it, the, was | every speaker alternates by position in a sentence, and forcing one would make the delivery worse: "thee gap" is wrong in a way "the gap" never is |
| unstressed vowels and accents | carried, ended, intercepted, received, recovered, victory, won | the syllable that differs is the one nobody hears |

**A reason rather than a bare list.** A word on the reviewed list with its
reason is a review somebody can disagree with. A word on a bare list is a word
somebody silenced, and there would be no way to tell the two apart later.

**One word is not in the dictionary at all**: "miscontrolled", which is
`EVENT_VERBS["Miscontrol"]` and is a coinage of StatsBomb's. It is reported as
unchecked rather than flagged, because a dictionary that does not list a word
has said nothing about it either way.

**The test is the half that runs every time.** The script prints a report
somebody reads;
`tests/test_vocabulary.py::TestEveryFlaggedWordHasBeenReviewed::test_no_flagged_word_is_unreviewed`
fails when a flagged word is on neither list, naming the word, its
pronunciations and where it is spoken. Change a header wording, add an event
verb or add a match with a new team name, and the word is either already
reviewed or the suite goes red. That was checked by removing "the" from the
reviewed list and watching it fail.

**The dictionary is never fetched.** `cmudict` is a dev dependency and ships
the data inside the package, so the check runs offline and so does the suite:
`tests/conftest.py` blocks the network for every test, which a dictionary
downloaded at test time would have tripped.

**It is a dictionary lookup and not a verdict about audio.** A flag means two
pronunciations exist for a spelling, which is a reason to listen rather than
evidence that a voice gets it wrong. The check cannot replace Shawn's ear; it
can stop a word reaching his ear unnoticed.

**No synthesis was spent on this entry.** October's allowance is near its
limit, and the element itself is already proven on all three voices by the
`lɛd` arm. Shawn confirms "minute" by ear from the hero recordings, which
open on "Minute 54" and "Minute 35"; until then what stands behind it is his
hearing of the problem and the dictionary's agreement that the spelling is
ambiguous. Those recordings exist now: the six were recorded on 2026-11-07,
after the run of 2026-10-30 was refused with 403, which `HANDOFF.md` records
under "Phase 5, task 5". The header they open on is the orchestrator's and
says no minute, so "minute" is still waiting for a line that speaks it.

**The markup reaches the speech request and nothing else.** This is the whole
of the design, and the reason to say it twice is that applying it one step
earlier is the easy mistake and a quiet one:

| Reader | What it would see | Why that is wrong |
| ------ | ----------------- | ----------------- |
| the screen | `take the <phoneme ...>lead</phoneme>.` | a fan reading markup |
| `app/grounding.py` | the same | a sound narration refused for markup it never wrote |
| a model | the same | nothing says a pronunciation to a model |

**The second row was the quiet one and is now the loud one.** This document
once said a narration marked up before the check would come back refused for
an ungrounded name, which would at least have been a failure. That was wrong:
the plain and the marked-up 1986 narration both came back grounded, on the
same 35 claims, because the check reads names, actions, clocks and numbers
against the facts a sentence cited and `phoneme`, `alphabet` and `ipa` are
none of those. The markup was accepted, carried "Verified from play data" and
would have been read out with the tags in it.

**So the check refuses markup outright.** `BANNED_PATTERNS` in
`app/grounding.py` refuses any narration containing `<` or `>`, labelled
"markup", beside the em dash rule. It is the characters and not an element,
because nothing the prompt or the template writes holds either one, so there
is no good narration to lose and a half-written tag is caught with a whole
one.
`tests/test_pronunciation.py::TestTheClockInARealNarration::test_the_check_refuses_markup_in_the_text_it_reads`
is the measurement: the marked-up 1986 narration is refused with "markup" and
nothing else, and the plain narration it was made from still passes on its 35
claims. `tests/test_grounding.py::TestNotGrounded::test_markup` and
`::test_either_bracket_on_its_own` hold the rule itself.

**The structural test stays as the second layer**, because the check is only
reached by narration and the other two rows of the table never reach it. A
marked-up header goes straight to the screen and still reads correctly to
anything that strips tags.
`tests/test_pronunciation.py::TestNothingElseAppliesIt::test_no_text_producing_module_imports_it`
reads the source of the seven modules that produce displayed or checked text
and fails if any of them imports the table, and
`tests/test_pronunciation.py::TestNothingElseAppliesIt::test_the_header_the_screen_shows_carries_no_markup`
builds the real 54:18 header and asserts it says "lead" and carries no
element.

**It says the same words.** `spoken_text` takes the markup back off, and a
round trip returns the input exactly
(`tests/test_pronunciation.py::TestItSaysTheSameWords`, which parametrizes
the round trip over eight texts).
That is not a convenience: an entry that changed a word rather than its
pronunciation is exactly what this repo must not ship, and it would show up as
a round trip that did not return what it was given.

**Text with no listed word is returned identically**, the same string and not
an equal one
(`tests/test_pronunciation.py::TestItTouchesNothingElse::test_text_with_no_listed_word_is_returned_identically`).
Every element costs billable characters, around 40 each time on a plan that
charges by the character, and SSML escaping is only needed once there is
markup to escape. So the common case sends what the screen shows and pays
nothing for the feature.

## The speech backend

`app/tts.py` is the one module that turns text into audio. It takes the
header, the narration, a persona and a situation, and returns the WAV bytes
the service sent, unexamined: a backend that inspected its own output would be
deciding whether the service had done its job.

**The citation tags are refused rather than spoken.** `Narrated.text` is the
stripped narration and `Narrated.tagged_text` is the one kept for the audit
trail, and the two are one character apart at a call site. "Open bracket
fourteen comma fifteen close bracket" read aloud over a goal is the kind of
thing that ships, so any text `strip_citations` would change is refused
(`tests/test_tts.py::TestItRefusesTaggedText`).

**The delivery reaches the request in two places**, and that is the service's
shape rather than a choice: the rate and the pitch are query parameters, so
they are per request, and the pauses are elements inside the text, so they are
per sentence and go only to the Caller.

**The order of the two markups matters**, and it is the one subtle thing in
the file. The pronunciation table escapes the text when it marks a word up.
Inserting the pauses first and marking up second would escape them into
`&lt;break ...`, which the service would read out rather than honour, so
pronunciation goes first and the pauses are joined between marked-up sentences
(`tests/test_tts.py::TestOnlyTheCallerGetsPauses::test_the_pause_markup_is_not_escaped`).

**Nothing secret is in the request object.** `SpeechRequest` carries the path,
the query and the body, and the host is added when the request is sent;
`TTS_URL` holds an instance id, so a request object holding the full URL could
not be printed, recorded or committed. The `Authorization` header reads
`Basic <redacted>` and the real one is built inside `send`, where it lives for
the length of one call
(`tests/test_tts.py::TestNothingSecretIsInTheRequest`).

**The test replays a real exchange.** `tests/golden/tts_synthesize.json` was
recorded by `scripts/record_tts_golden.py`, one call, 83 submitted characters.
The request is rebuilt from the backend and compared against the recorded one,
because a recording is worth nothing if the replay sends something else
(`tests/test_tts.py::TestTheReplaySendsWhatWasRecorded::test_the_request_matches_the_one_that_was_recorded`).

What the golden holds of the response is its first 128 bytes, the RIFF header
and the start of the audio, with the full length and SHA-256 of what it did
not keep. `app/tts.py` returns the bytes it was handed without examining them,
so what a replay has to assert is exactly that, and a hundred bytes do it as
well as the ninety thousand the service sent. The fixture says so in its own
provenance block and
`tests/test_tts.py::TestTheGoldenIsARecording` holds it to that, including
that it holds no credential.

## The hero samples, and what they do not yet tell apart

`scripts/tts_samples.py` wrote eight files outside the repo, in
`C:\Users\shawn\prelude_voice\samples`: both hero goals, the 1986 Maradona
goal at 54:18 and the 2022 Di Maria goal at 35:22, in all three voices, with
the Mate heard from both sides. Six calls, 1,794 submitted characters and
1,530 spoken, against a budget of 2,500. The four Mate files were then
regenerated once the delivery table was filled in, four calls and 1,196
submitted characters; `--personas` is what reruns one voice's files without
paying for the rest.

| File | Voice | Listener | Length | Median f0 |
| ---- | ----- | -------- | -----: | --------: |
| `1986_caller_neutral.wav` | Heidi | no side | 20.37s | |
| `1986_storyteller_neutral.wav` | Emma | no side | 17.42s | |
| `1986_mate_scored.wav` | Ethan | supporting Argentina | 17.75s | 162.2 Hz |
| `1986_mate_conceded.wav` | Ethan | supporting England | 21.05s | 150.0 Hz |
| `2022_caller_neutral.wav` | Heidi | no side | 18.85s | |
| `2022_storyteller_neutral.wav` | Emma | no side | 17.55s | |
| `2022_mate_scored.wav` | Ethan | supporting Argentina | 16.87s | 162.2 Hz |
| `2022_mate_conceded.wav` | Ethan | supporting France | 20.02s | 146.3 Hz |

The four Caller and Storyteller files are from before the delivery table was
filled in, so they are those voices at their own rate with no pauses. The four
Mate files were regenerated afterwards, at a cost of 1,196 submitted
characters, and they are the only ones that carry a delivery.

**The words are built by code and no model ran.** The header is the
orchestrator's, through `openings` in `scripts/write_headers.py`, and the
narration is `template_narration` in `app/narration_prompt.py`, the fallback
assembled out of the numbered facts. So a sample is reproducible, grounded by
construction, and costs nothing but the speech. These are for judging the
voices; `scripts/narrate_once.py` is for judging the words.

**The first run was eight files from six calls, and that was the finding.**
With the delivery table empty the Mate's two rows were both empty, so its two
sides built the identical request and the two files were the same audio under
two names. The script wrote both anyway and said which names shared a request,
because paying twice for identical audio would have hidden that there was
nothing to hear between the sides, and leaving one out would have hidden it
too.

**Now there is something to hear.** The regenerated Mate files are four
distinct calls, and the difference is in the numbers as well as in the ear: a
goal for your side arrives about three seconds shorter and a tone higher than
the same goal against you. That is +10 rate against -10, and +10 pitch against
0, doing exactly what it was set to do.

**The Caller and the Storyteller files are still from the first run.** They
were not regenerated: 1,196 characters bought the comparison that had none,
and the other four would have been another 1,196 to hear a rate of 0 and a
rate of +10 with short pauses. They are worth a rerun once Shawn has heard the
Mate and knows whether the numbers are close.

## The hero recordings the site serves

`scripts/tts_hero.py` writes the recordings the moment card plays: three per
match, one per listener, as MP3 under `app/web/assets/`, with `hero.audio` in
`app/web/matches.json` filled from the files on disk. Same delivery table and
same pronunciation markup as the samples above; the format is smaller because
these are committed and served rather than listened to once.

**The words are no longer the samples' words.** The samples speak
`template_narration`. These speak the narration written for this listener,
one per `hero.voice_for` key, frozen in `app/web/narrations.json` by
`scripts/freeze_narrations.py --authored` and shown on the moment card under
the grounding label by the same lookup. What a judge hears and what a judge
reads are one text.

**All six exist, recorded on 2026-11-07 for 2,403 billed characters.** The
run on 2026-10-30 was refused with HTTP 403 on its first call, and a five
character request in both formats was refused the same way, so it was the
account and not the request; `HANDOFF.md` holds that evidence under "Phase 5,
task 5". The six files are in `app/web/assets/audio/` and `hero.audio` names
all of them.

**The run of the Task 6 narrations costs 1,959 characters**, which is the
figure IBM bills: it counts the SSML and not the whitespace, so the price is
the submitted 2,268 less its spaces. `billed_characters` in `app/tts.py` is
that number and `--budget` is set on it.

**The default budget is 3,500, raised from 3,000 for Task 9c and from 2,000
for Task 7 before that.** The Task 6 narrations cleared 2,000 by 41
characters, which was close enough that one more pronunciation entry on a word
either of them says would have pushed it over. Task 7 asked for fuller
narrations, which run 1,488 to 1,605 billed characters for a match against the
918 and 1,041 the frozen pair cost.

What changed for Task 9c is not the length but the count. The framework gives
each narrator its own text, so the six recordings are six narrations rather
than two spoken three ways each, and the budget is divided six ways instead of
two: 3,500 leaves 583 a recording. The eight references are what that is
measured against, and the six that get recorded bill 271 to 364 each and 1,873
together
(`tests/test_narrator_candidates.py::TestTheSlotPrice::test_the_six_references_together_fit_the_budget`).
The monthly Lite allowance is 10,000, so 3,500 is still a fraction of it; the
budget exists to refuse a run that is unexpectedly large, not to be the
smallest number that fits.

**The spoken count is now below the billed one**, 1,746 against 1,959, where
it used to be above it. Nothing changed in how either is counted: the frozen
narrations carry more markup than the template did, because the 2022 one says
"Di" twice and each occurrence costs a `<phoneme>` element, and markup counts
toward the price while the whitespace it displaces does not.

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

What the check can hold is where the narration stops. Under the cited reading
that is the last sentence citing the goal's own shot fact, so a sentence after
the goal is refused.

**Under the goal-call reading it is what the last sentence claims, not which
verb it used.** A narration lands the finish when it makes a claim the goal's
own record holds: the `Shot` itself, the body part, or the first-time flag. The
live run of 2026-10-31 is why it is a rule rather than a verb list. Nine of
eighteen candidates were refused on this one rule, and every one of the nine
ended "with his left foot", after "firing", "struck", "smashed it home" or
"blasting it home". None of those four words is in `ACTION_CLAIMS`, so none of
them claimed a shot, so the check decided a narration that said the goal was
scored with the left foot had not reached the goal. Adding the four would have
worked for the four and found four more on the next run.

So the body part counts, the first-time flag counts, and "the ball went in"
counts, which is a `Shot` claim in `app/narration_grammar.py` now and was not
before. `FINISH_KINDS` in `app/grounding.py` is the list, and what it cannot
catch is in the comment beside it: a last sentence naming the body part without
saying the ball went in lands the finish by this rule and does not say it in
words (`tests/test_reference_narrations.py::TestTheFinishMayBeSaidPlainly`).

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
[10] Peter Beardsley was dribbled past.
[14] Terry Butcher was dribbled past.
[17] Terry Fenwick was dribbled past.
[21] Peter Shilton was dribbled past.
[24] Diego Armando Maradona shot and scored for Argentina.
```

which is shown and voiced as:

> Minute 54. Peter Beardsley was dribbled past. Terry Butcher was dribbled
> past. Terry Fenwick was dribbled past. Peter Shilton was dribbled past. Diego
> Armando Maradona shot and scored for Argentina.

That is the fallback voice, and it is deliberately plainer than the voice above.
It is grounded by construction, because every sentence is one fact said in the
words that fact used, citing that fact and no other, and it is run through the
same check anyway. One fact per sentence is also what keeps it inside the
pairing rule. It uses full recorded names rather than shortening them, so that a
fallback is not the thing that introduces a judgement about what a player is
called.

### Grounded was not enough: it has to be complete

The fallback above used to read "Minute 54. José Luis Cuciuffo passed. Héctor
Adolfo Enrique passed. Diego Armando Maradona dribbled. Diego Armando Maradona
shot and scored for Argentina." Every word of that is grounded, and it leaves
out three of the four defenders Maradona went past, which is the reason anyone
remembers the goal. It collapsed the run of four `Dribble` events into one
sentence, then trimmed the run-up from the front to fit a five-sentence budget,
and the one surviving dribble was nearly trimmed too.

A model writing a thin narration is a model limit. A fallback writing one is a
bug, because it is assembled by code out of the facts and can see every beat.
So `key_beats` in `app/narration_prompt.py` names the beats of a passage that a
narration has to reach (the shot, every dribble past an opponent, and the foul
for a penalty), the fallback gives every one of them a sentence before any
other fact is considered, and the sentence budget became a target rather than a
ceiling. The fallback now reaches every key beat on all nine goals:
`tests/test_narration_prompt.py::TestTemplateNarration::test_it_cites_every_key_beat_of_the_passage`
and, through the measure the evaluation uses,
`tests/test_narration_eval.py::TestCoverage::test_the_fallback_scores_full_coverage_on_every_goal`.

A dribble beat is said with the `Dribbled Past` record, which names the player
who was beaten rather than only that someone went past somebody. A foul beat
prefers the `Foul Won` record, naming the side the penalty was given to, and
falls back to the `Foul Committed` record for the 117:05 penalty, which has no
`Foul Won` side recorded at all.

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
were changed for.

## What the measured run shows

Six runs are not a rate. `scripts/narration_eval.py` narrates every goal three
times and writes `docs/narration_eval.md`, which is where the numbers live and
what any claim about this prompt should be read against. The first full run on
`granite4:micro`, twenty-seven narrations:

| | |
| --- | --: |
| grounded on the first attempt | 22 of 27 |
| fell back to the template | 1 |
| mean tokens per narration | 1,941 |
| mean wall clock per narration | 32s on CPU |

**Grounding is not the problem; completeness is.** Five of the nine goals have
the shot as their only key beat, so coverage can only move on the other four
plus the 117:05 penalty. Across those, the model wrote fourteen narrations and
**all fourteen cited the shot and no other key beat**: not one dribble past a
defender, and not one of the three penalty fouls. Every grounded narration
cites the shot, because the ending rule makes it, so those narrations reached
nothing the rule did not force.

That is the thin narration quoted above, and it was the normal case rather
than an unlucky run. Nothing here refuses a narration for leaving the story
out, and `docs/narration_eval.md` exists so that the gap is a number rather
than an impression.

The fallback used to have the same gap and no longer does: it reaches every
key beat on all nine goals, which is the section above.

## Naming the beats closed most of the gap, and cost some grounding

The facts were all in the prompt and the model walked past them. So the beats
are named rather than left to be found: `beats_block` in
`app/narration_prompt.py` prints the key beats of the passage with the fact
number to cite for each, and asks for one sentence on each before the last
line. The requested sentence count rises to fit, because a prompt asking for
four sentences and then naming five beats would have the model drop one
instruction to obey the other.

**The check did not change.** `app/grounding.py` still refuses on truth alone.
Coverage is reported, not enforced, and a narration that reaches every beat
and miscites one of them is still refused.

The block is empty for a goal whose only key beat is the shot, which is five
of the nine, so those prompts are untouched and were not rerun. The other five
goals, three runs each, before and after:

| | Task 4a | Task 4c |
| --- | --: | --: |
| grounded on the first attempt | 12 of 15 | 10 of 15 |
| coverage of the model's narrations | 42% | 95% |
| cited the shot and no other key beat | 14 of 14 | 1 of 14 |

The 54:18 goal went from 1 of 3 grounded at 20% coverage to 3 of 3 at 100%:
the narration now names all four defenders, which is the first time any model
output in this repo has told that run.

**The trade is real and it is in the table on purpose.** Asking for more
sentences is asking for more chances to cite the wrong fact, and the pass rate
fell from 12 of 15 to 10 of 15. All of the loss is on the 22:24 penalty, which
went from 2 of 3 to 0 of 3. That goal has a hundred facts and a prompt of some
nine thousand tokens, and it is the one where naming the beats asks the most
of a three billion parameter model. The other four goals held or improved.

Both numbers are reported together for that reason: a prompt change that
bought coverage with grounding would be a bad trade dressed as a good one, and
`docs/narration_eval.md` shows the pair goal by goal so it cannot hide.

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

**What it claims is that every event in the narration happened as told.** That
is why the reaction layer does not weaken it: "Oh, lovely!" tells no event, so
there is nothing in it for the label to be true or false about. The play layer
is where every event is, and every claim in it is traced to a record.
"Two layers: the play and the reaction" above is the whole of that rule, and
`REACTION_WORDS` in `app/grounding.py` is where the shape test lives.
