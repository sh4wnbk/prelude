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
| `app/personas.py` | the three voices the one narration can be spoken in, which is Phase 5 and not this document |
| `app/grounding.py` | refuses a narration that broke them |
| `scripts/narrate_once.py` | runs one goal through a real model and prints every attempt |
| `scripts/narration_eval.py` | runs every goal several times and measures how often the rules held |

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

## The three personas, and the one style

**There is one narration style and the personas are separated by sound.**
`NARRATION_STYLE` in `app/narration_prompt.py` is the style every narration is
written in, whoever is listening, and `build_prompt` prints it under "THE
STYLE" in every prompt
(`tests/test_narration_prompt.py::TestTheOneNarrationStyle`). A persona
changes how that text is spoken, which is Phase 5: an IBM Text to Speech
voice, a rate, a pitch, and the pauses between sentences.

That is a decision and not a simplification. The three measured sections at
the end of this one are what it came out of: three ways of asking for three
registers were tried, and each gave one register back.

| Persona | Id | Voice | What it sounds like | Offered to |
| ------- | -- | ----- | ------------------- | ---------- |
| The Caller | `caller` | `en-AU_HeidiNatural` | quick play-by-play, keeping up with the move | everyone |
| The Storyteller | `storyteller` | `en-US_EmmaNatural` | calm documentary, unhurried and even | everyone |
| The Mate | `mate` | `en-US_EthanNatural` | warm, from the next seat | fans only |

**Nothing in the narration text differs between them.** `app/grounding.py`
reads a narration against the facts it cited whoever asked for it, and
`BANNED_PATTERNS` refuses the same nicknames, epithets and outcome claims in
all three. The prompt takes no persona at all:
`tests/test_narration_prompt.py::TestTheOneNarrationStyle::test_the_prompt_takes_no_persona_and_no_side`
holds it to that, because an argument that changed nothing would read as a
register still reaching the model.

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

**The Mate is the only one that needs a side.** It is the one voice that makes
no sense without an allegiance: told to a neutral listener it would be saying
they support a team they did not choose. `fans_only` is true for it and false
for the other two, and `available` in `app/personas.py` is what leaves it out
for a neutral listener.
`tests/test_personas.py::TestFansOnly::test_a_neutral_listener_is_not_offered_the_mate`
covers that, and
`tests/test_personas.py::TestFansOnly::test_the_default_for_a_neutral_listener_is_one_they_may_choose`
covers the disagreement that would not otherwise show up: `default_persona` in
`app/orchestrator.py` returns an id and reads nothing in this config, so a
default that was fans only would hand a neutral listener a persona the Profile
screen then refuses to show them.

### The first person is refused in the prompt and guarded in the check

No narration says "we", "our" or "us" any more, because the prompt rejects the
first person in the one voice it has
(`tests/test_narration_prompt.py::TestTheOneNarrationStyle::test_the_prompt_refuses_the_first_person_in_the_one_voice_it_has`).
The Mate was written as the listener's side from Task 6b to Task 6d, which is
the one thing that visibly separated it, and what a model wrote with that
permission is below: "Our Peter Beardsley was dribbled past at 54:08." and
"We were dribbled past, Peter Beardsley.", five times over. Partisan warmth is
something a voice can carry and that prose could not.

**The rule stays in `app/grounding.py` as a guard.** `check` still refuses
"we", "our" and "us" from every persona but a partisan one, and from a
partisan one unless a cited fact is recorded against the listener's side.
Nothing asks a model for the word, so the rule now exists to catch a model
that writes it anyway rather than to permit one that was told to.

| Voice | "we", "our", "us" | "you", "your" |
| ----- | ----------------- | ------------- |
| no persona | refused | refused |
| the Caller | refused | refused |
| the Storyteller | refused | refused |
| the Mate, with a side | admitted over that side's facts | refused |
| the Mate, with no side | the check itself is refused | refused |

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

**"You" is refused in every voice, the Mate included.** The narration is not
addressed to the fan in any register, which is the ending rule below: the
header goes before the narration and nothing goes after it.
`tests/test_grounding.py::TestThePartisanVoice::test_you_is_refused_from_the_mate_too`
holds the partisan voice to it.

**A Mate narration from a neutral listener is refused rather than softened.**
`check` raises `NoSideForAPartisanVoice`. Checking it as though nobody were
partisan would admit "we" with no side behind it, and picking a side would
tell a listener they support a team they did not choose.

### Measured once: the three voices came back nearly the same

The next three sections are the measurement behind the decision at the top of
this one. All three ran against code that has since been removed: each persona
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
| The Mate | scored | +10 | +10 | not available | not available |
| The Mate | conceded | -10 | 0 | not available | not available |

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

**The Mate lifts for your goal rather than dropping for theirs.** +10 rate and
+10 pitch when your side scored, -10 rate and pitch back to 0 when the other
side did. It goes up rather than down because down is not available: a
`pitch_percentage` below zero is ignored by the service, so 0 is the floor and
the only way for one row to sit under another is to let the other rise.

**The pauses are short, and short was measured rather than guessed.** The
probe found a requested 600 ms arriving as 1.36s on the Caller's voice, so a
request lands at roughly twice what it asks for: 200 and 400 are about 450 ms
between sentences and 900 ms before the goal.

**Eight rows and not nine.** The Mate is `fans_only`, so there is no neutral
Mate row to write: a partisan voice told to a listener with no side would be
telling them they support a team they did not choose. Asking for that row
raises, and the message says why rather than returning a default delivery that
would sound like nothing was chosen
(`tests/test_delivery.py::TestLookup::test_the_mates_neutral_row_says_why_it_does_not_exist`).

**The two break columns are the Caller's alone**, because `<break>` moves its
voice and neither of the other two. A pause written on the Storyteller or the
Mate is refused rather than sent and ignored
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

### The Mate is never cheerful when the other side scored

This is the one rule in the table that is about taste rather than about what
the service honours, and it is the one worth a test of its own. A voice that
brightens over a goal against your team is a voice that was not listening with
you.

Brighter and quicker is what cheerful is made of in the only two controls
there are, so the rule is written as a comparison between the Mate's own two
rows rather than as a fixed number: the conceded row may not carry more pitch
than the scored row, and may not carry more rate either
(`tests/test_delivery.py::TestTheMateIsNeverCheerfulWhenTheOtherSideScored`).

A comparison rather than a number is the only thing that can be stated while
the table is empty, and it is also the right shape once it is full: it survives
Shawn filling both rows in by ear in one sitting, whatever numbers he picks.

The rule is "never brighter", not "always duller". A Mate that sounds the same
either way is not cheerful about a goal against the listener's team; it is
even, and that is allowed
(`tests/test_delivery.py::TestTheMateIsNeverCheerfulWhenTheOtherSideScored::test_the_same_delivery_in_both_is_allowed`).

It does not fire on the other two personas. Neither is partisan, so a brighter
conceded row there is not a voice celebrating against its own listener. It may
still be wrong by ear; it is not wrong by rule.

## How a word is said, which is not what it says

`<phoneme>` is the one SSML element that works on all three of these voices,
and `app/pronunciation.py` is the table: word to IPA, with `lead` to `liːd` as
the first and so far only entry.

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

**The markup reaches the speech request and nothing else.** This is the whole
of the design, and the reason to say it twice is that applying it one step
earlier is the easy mistake and a quiet one:

| Reader | What it would see | Why that is wrong |
| ------ | ----------------- | ----------------- |
| the screen | `take the <phoneme ...>lead</phoneme>.` | a fan reading markup |
| `app/grounding.py` | the same | a name or a number inside an element is one the check cannot match, so a grounded narration would be refused for being pronounceable |
| a model | the same | nothing says a pronunciation to a model |

Neither of the first two failures announces itself. A header with markup in it
still reads correctly to anything that strips tags, and a narration marked up
before the check comes back refused with a message about an ungrounded name,
which sends a reader to the wrong file. So the guard is structural:
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
1,530 spoken, against a budget of 2,500.

| File | Voice | Listener | Length |
| ---- | ----- | -------- | -----: |
| `1986_caller_neutral.wav` | Heidi | no side | 20.37s |
| `1986_storyteller_neutral.wav` | Emma | no side | 17.42s |
| `1986_mate_scored.wav` | Ethan | supporting Argentina | 19.30s |
| `1986_mate_conceded.wav` | Ethan | supporting England | 19.30s |
| `2022_caller_neutral.wav` | Heidi | no side | 18.85s |
| `2022_storyteller_neutral.wav` | Emma | no side | 17.55s |
| `2022_mate_scored.wav` | Ethan | supporting Argentina | 18.15s |
| `2022_mate_conceded.wav` | Ethan | supporting France | 18.15s |

**The words are built by code and no model ran.** The header is the
orchestrator's, through `openings` in `scripts/write_headers.py`, and the
narration is `template_narration` in `app/narration_prompt.py`, the fallback
assembled out of the numbered facts. So a sample is reproducible, grounded by
construction, and costs nothing but the speech. These are for judging the
voices; `scripts/narrate_once.py` is for judging the words.

**Eight files came from six calls, and that is the finding.** The Mate's two
rows in the delivery table are both empty, so the two sides build the
identical request, and the two files are the same audio under two names.
Nothing in them is different because nothing has been set yet. The script
writes both anyway and says which names share a request, because paying twice
for identical audio would have hidden it and leaving one out would have hidden
it too.

**The three voices are the only thing a sample separates today.** Every
delivery value is a placeholder, so what Shawn is hearing is Heidi, Emma and
Ethan at their own default rate and pitch, reading the same words. That is the
right thing to listen to first: the delivery is tuned against voices that have
been chosen, not the other way round.

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
