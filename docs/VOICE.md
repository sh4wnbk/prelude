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
| `app/personas.py` | the three registers the same facts can be said in |
| `app/narration_prompt.py` | builds the numbered facts, and states the rules to the model in the prompt |
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

## It opens on one line, and that line is a placeholder

One line comes before the narration, and for now it is:

> Here's the buildup.

It is not narration and it is not generated. It asserts nothing about the
match, so there is nothing in it for the grounding check to read and it carries
no claim the "Verified from play data" label is about. **No code produces it
yet.** It is recorded here because the wording is settled, not because a screen
or a script says it.

It is a placeholder in the exact sense that it is the neutral case of
something larger. An orchestrator picks the opening line from the listener's
allegiance, whether their side scored or conceded, and how far into the match
the moment was, and "Here's the buildup." is what a neutral listener gets. A
fan gets a header in front of it instead.

### The header table

**The module is built and no screen calls it yet.**
`app/orchestrator_contract.py` declares the table below, IBM Bob built
`app/orchestrator.py` against it, and `tests/test_orchestrator.py` asserts it,
all passing. No screen shows a header yet; Task 7 puts it on the moment
card.

| | early | middle | late |
| --- | --- | --- | --- |
| your side scored | Great start. | Good news. | Late one for your side. |
| your side conceded | Still early. | There's still time. | no prefix |
| neutral | no prefix | no prefix | no prefix |

A fan's prefix is followed by "Here's how it happened." A neutral listener
gets "Here's the buildup." and no prefix.

**This is the starting wording and Shawn writes the final wording.** What is
settled is the shape: a fixed table, looked up by allegiance, outcome and
phase, with nothing generated and nothing a model chooses. Changing a word is
a one line edit to `HEADER_PREFIXES` in the contract, which is why the
implementation is told to read the prefixes out of the table rather than
writing any of them down.

**The late scored cell says nothing about earlier goals.** It first read "Your
side again.", which was false for England's only goal in 1986, at 80:37: the
header is built from the kickoff time, the score after the moment and the
listener's side, and none of those says whether this side scored before.
`tests/test_orchestrator.py::TestTheHeader::test_a_late_first_goal_gets_no_again`
holds it to that.

**The late conceded cell is empty on purpose.** "There's still time" is a
kindness early and a lie late, and a phone telling somebody there is still
time when there is not is worse than a phone saying nothing. It is the one
cell with a test of its own in both directions.

**The phase is a share of regulation time, not a count of minutes.** Early is
the first third and late is the final quarter, so a sixty minute game is read
the same way as a ninety minute one without changing anything.
`tests/test_orchestrator.py::TestAnotherSport` is a sport that does not exist,
and it is what fails if a 90 is ever written into the rule.

**None of this is narration and none of it carries the label.** The header is
built from the kickoff time, the score and the listener's own answer, not from
the event data, so "Verified from play data" has nothing to say about it. It
is also the one line in the app addressed to the fan, which is what the
ending rule above keeps out of the narration itself: the header goes before
the narration, and nothing goes after it.

## The three personas

**The styles are in the prompt and no screen offers a choice yet.**
`app/personas.py` holds the three, `build_prompt` prints the chosen one's
style, `check` in `app/grounding.py` takes the persona and the listener's
side, and `narrate` passes both through. Nothing on a screen picks a persona:
that is Task 7.

A persona is a register, not a set of permissions. It changes how the same
facts are said and nearly nothing about which facts may be said:
`app/grounding.py` reads a narration against the facts it cited whoever asked
for it, and `BANNED_PATTERNS` refuses the same nicknames, epithets and outcome
claims in all three voices. The one difference is the first person, and the
section below is what keeps it from being a loophole.
`tests/test_narration_prompt.py::TestThePersonaInThePrompt::test_the_rules_are_the_same_in_every_voice`
takes the prompts apart and asserts that the rules, with the person rule
removed, are the same text in all three.

| Persona | Id | What it sounds like | Offered to |
| ------- | -- | ------------------- | ---------- |
| The Caller | `caller` | play-by-play pace, one action a line | everyone |
| The Storyteller | `storyteller` | documentary calm, measured and plain | everyone |
| The Mate | `mate` | partisan, a supporter in the next seat | fans only |

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

**The voices are empty and marked unconfirmed.** Each persona has an IBM Text
to Speech voice field, it is `None`, and `voice_confirmed` is false beside it.
A voice is chosen in Phase 5 by listening to candidates say a narration, and
nothing in this repo has listened to one. A plausible voice id written down now
would be a guess with the look of a decision, so the pair of fields says "not
chosen" instead:
`tests/test_personas.py::TestTheVoicesAreNotChosenYet::test_a_null_voice_is_never_confirmed`.

### The Mate says "we", and nothing else does

The Mate is written as the listener's side, so "we", "our" and "us" are what
that voice is made of. From the Caller or the Storyteller the same word is a
loyalty nobody declared: neither is written as either team, and "our goal"
from a voice with no side is the app claiming one.

So the first person is refused by default and admitted for a partisan persona
only, and then only where it has something to stand on. `FIRST_PERSON` in
`app/grounding.py` holds the words, as patterns rather than as a word list,
because an apostrophe is a word boundary and `we` is what catches
"we're".

| Voice | "we", "our", "us" | "you", "your" |
| ----- | ----------------- | ------------- |
| no persona | refused | refused |
| the Caller | refused | refused |
| the Storyteller | refused | refused |
| the Mate, with a side | allowed over that side's facts | refused |
| the Mate, with no side | the request itself is refused | refused |

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
addressed to the fan in any register, which is the ending rule above: the
header goes before the narration and nothing goes after it.
`tests/test_grounding.py::TestThePartisanVoice::test_you_is_refused_from_the_mate_too`
holds the partisan voice to it.

**A Mate request from a neutral listener is refused rather than softened.**
Both `build_prompt` and `check` raise `NoSideForAPartisanVoice`. Falling back
to a neutral register would hand back narration in a voice nobody asked for,
and picking a side would tell a listener they support a team they did not
choose.

**The prompt says what the check enforces, in each voice.** A prompt asking
for less than the check requires would set the model up to fail and a retry
would not help it, so `first_person_rule` in `app/narration_prompt.py` writes
the strict version for two voices and the partisan version, naming the side,
for the Mate.

**It loosens the first person and nothing else.** "We dribbled past Peter
Reid" is the misdescription from the section above, said as a supporter, and
it is refused for the same reason:
`tests/test_grounding.py::TestThePartisanVoice::test_a_partisan_narration_is_held_to_every_other_rule`.

### Measured: the three voices came back nearly the same

`docs/narration_eval.md` holds the run, 36 narrations over three goals, three
runs of each of four voices per goal, on `granite4:micro`. Two findings are
worth carrying into Phase 5, and both are numbers rather than impressions.

**The registers did not reach the model.** Words per sentence, the one thing
in these styles that can be measured without a judgement, came out between 4.9
and 5.5 for every voice, including the Caller, whose style asks for short
lines, and the Storyteller, whose style asks for measured ones. The sample
narrations printed in the report read alike for the same reason. Whether a
larger model separates them is what Task 4b is for; this says nothing about
`ibm/granite-4-h-small` or `openai/gpt-oss-120b`, only about a three billion
parameter model.

**The Mate never took the first person.** Of 18 narrations written in that
voice, none used "we", "our" or "us". The permission is in the prompt and in
the check, and nothing requires it: `app/grounding.py` refuses a partisan
narration that misuses the word and has no opinion about one that never
reaches for it. So the rule above is built and tested, and on this model it
has not yet had anything to rule on.

**The style block cost first-attempt grounding.** On the 54:18 goal, Task 4c
measured 3 of 3 first attempts grounded with no persona; with a persona, the
same goal came out 3 of 12. Retries absorb most of it, and the after-retry
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
different punctuation. The styles in `app/personas.py` are read and obeyed as
rules and not as a voice.

**The Mate did take the first person, and it reads badly.** It used "we",
"our" or "us" in 9 of its 12 narrations on `openai/gpt-oss-120b`, against none
on either smaller model, so the permission is reachable too. What it produced
is "Our Peter Beardsley was dribbled past at 54:08." and "We, Nicolás Hernán
Otamendi, pressed, 78:11.": the possessive grafted onto a name rather than a
supporter telling a friend what happened. The grounding check accepts it,
correctly, because every cited fact is the listener's side. The rule is doing
its job and the prose is not, and nothing in this repo refuses a narration for
being stilted.

### Each persona shows its register as well as describing it

Task 4b is why. A model that followed every other rule exactly wrote the same
narration in all three voices, so what reached it was the rules and not the
prose. Each persona now carries an `example` beside its `style`: a short
narration in that voice, cited the way a real one has to be, which
`build_prompt` prints under "THE REGISTER, ON A PASSAGE FROM ANOTHER MATCH".

**The passage in it never happened.** The players and the teams are invented,
so nothing in the example can be read as a fact about the goal being
narrated, and a model that lifts a name out of it is refused by
`app/grounding.py` like any other invention. That makes copying the content
rather than the voice a visible failure instead of a silent one.
`tests/test_narration_prompt.py::TestTheWorkedExamples::test_the_examples_name_nobody_in_either_demo_match`
holds the names apart from both demo matches.

**The examples are held to the rules they are teaching.**
`tests/test_narration_prompt.py::TestTheWorkedExamples::test_each_example_passes_the_real_grounding_check`
runs each one through `app/grounding.py` against the invented passage it
narrates, the Mate's with its side. It earned its place immediately: the first
draft of the Caller's example read "Quillan won it back", which the check
reads as a claim about a `Foul Won` event over a fact recording a recovery.
An example that breaks a rule is the prompt teaching a model to fail the
check.

**The Mate's example is where the first person is shown, not just allowed.**
It reads "We recovered it through Quillan", never "We, Quillan, recovered
it", because the second is what `openai/gpt-oss-120b` produced in Task 4b
with no example to copy: "Our Peter Beardsley was dribbled past at 54:08."
The check accepts that, correctly, and it reads as a label stuck on a name
rather than as a supporter talking.
`tests/test_narration_prompt.py::TestTheWorkedExamples::test_the_mate_never_puts_a_name_in_apposition`
holds the example to the better shape.

### What the examples changed: almost nothing

Measured the same way, on `openai/gpt-oss-120b`, over the two goals the
persona arm used, 16 narrations. `docs/narration_eval.md` holds it.

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
example was written for.** The example says "We recovered it through
Quillan". What came back for an England listener is:

> We were dribbled past, Peter Beardsley. We were dribbled past, Terry
> Butcher. We were dribbled past, Terry Fenwick. We were dribbled past, Peter
> Shilton. Diego Armando Maradona shot.

That is the apposition the example was meant to replace, inverted: the name
now trails the clause instead of interrupting it. It is grounded, because
every cited fact is England's, and it is five sentences of the same sentence.
The first person is reachable and the register is not, which is the same
finding as before with one more thing ruled out.

**Nothing was paid for in grounding.** All 16 passed on the first attempt,
as all 16 did before the examples, so the examples are not harmful; they are
inert. Whether three personas are worth shipping is a product decision rather
than a prompt problem, and it is Shawn's.

**The style text is prompt copy and the Profile line is app output.** They are
checked differently on purpose. The Profile line is read by a fan, so the
no-nicknames rule applies to it. The style is said to a model, where naming a
banned word can be the only way to forbid it, which is what rule 7 of the
prompt in `app/narration_prompt.py` already does; scanning it for those words
would refuse the instruction that keeps them out of the narration. Both are
held to the no-em-dash rule:
`tests/test_personas.py::TestNoDashes::test_no_em_or_en_dash_in_any_field`.

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
