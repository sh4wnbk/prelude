# Phase 4: the narration, the grounding check and the orchestrator

Moved out of `HANDOFF.md` unchanged, when that file was restructured as a
running snapshot plus the latest record. **This is the record as it was written
when each task closed, not a description of the repo today**: present tense in
it means the day of the task. `HANDOFF.md` carries the current state, and
`docs/history/README.md` says where each decision from here now lives.

Every Phase 4 record, in the order the tasks ran, including both of Bob's sessions and the two follow-ups after them.

---

### Phase 4, task 1

**Config and the provider layer.** `docs/narration.md` is the full account; this
is what changed in the repo.

**`app/narration_config.py`**: the model ids, committed. Two watsonx comparison
candidates (`ibm/granite-4-h-small` and `openai/gpt-oss-120b`), with
`ACTIVE_CANDIDATE` naming the one in use, and one development model
(`granite4:micro` on Ollama, `num_gpu` 0). Values only, no behaviour.

**`app/narration_provider.py`**: `NarrationProvider` and two backends,
`OllamaProvider` and `WatsonxProvider`. `provider()` with no argument returns
Ollama; watsonx comes back only from `provider("watsonx")`, and building it
raises `MissingCredentials` naming whichever of `WATSONX_API_KEY`,
`WATSONX_PROJECT_ID` and `WATSONX_URL` is unset, before any request is sent.
Standard library only. The watsonx request and response shapes were read from
IBM's published OpenAPI schema, which `docs/narration.md` cites, not written
from memory.

**Model ids moved out of the credentials file.** A model id is not a
credential, so `GRANITE_MODEL_ID` and `OPENAI_MODEL_ID` are gone from
`.env.example` and from the scrub list in `bob_sessions/README.md`. **Shawn
still has the two lines in his own credentials file and should delete them;**
nothing in the repo may open that file to check. The file itself moved out of
the repo in task 2c, below; at this commit it was still at the repo root.

**The tests make no network calls, and that is enforced.**
`tests/test_narration_provider.py` is 65 tests, and `tests/conftest.py`
replaces `urllib.request.urlopen` and `socket.socket.connect` with functions
that raise, for every test in the suite. Two tests check the guard itself.

**The two golden files are different kinds of thing, and the tests say so.**
`tests/golden/ollama_development_model.json` is a real recording: a live call to
a local Ollama server running `granite4:micro` with `num_gpu` 0, written by
`scripts/record_narration_golden.py`, which can run again. It returned
`The football match ended in a thrilling 2-1 victory for the home team.`, which
is coherent English and is the evidence that `num_gpu` 0 works.
`tests/golden/watsonx_text_generation.json` is a schema fixture written by hand
from IBM's documentation, because no watsonx call has been made from this repo:
that would be a paid call against live credentials. Its response half is not
evidence of what watsonx returns, only of what IBM documents, and a test
asserts the file declares that about itself.

**`scripts/check_docs.py` now reads test counts per file.** There are two test
files, so a bare count in a doc had to be read as a count of something rather
than of the whole suite. A count claim that names one test file is checked
against that file; one that names none is checked against the suite total. Its `all N pass` pattern was also case-sensitive, so a
sentence that opened with the word `All` had never been checked. It is now, and
the brief's sentence about the import guard was reworded to put the file name
before the count so the claim is both scoped and visible to the gate.

### Phase 4, task 2

**The buildup contract, declared for Bob to implement.** This closes the Phase
3 finding that a penalty's event window holds only the kick. Bob built it in
task 3 below; what this section records is what the contract fixed and why.

**`app/event_feed.py`** gains `SET_PIECE_SHOT_TYPES`, a `Buildup` shape, and
`BuildupFeed`, which is `EventFeed` plus one `buildup(match_id, moment)`
method. `Buildup` carries the moment, the raw events, the possession numbers
included, and the goal's recorded shot type when it is a set piece.

**It is a second protocol rather than a line added to `EventFeed`.** Adding
`buildup` to `EventFeed` would have made
`test_satisfies_the_event_feed_protocol` fail, because a `runtime_checkable`
protocol's `isinstance` check wants every member present, and
`StatsBombEventFeed` has no `buildup`. That failure would have been truthful
but it would have broken a test that proves something separate and still true.
Keeping them apart meant the pending work failed on its own tests and nothing
else. **Merging the two was the right change once `buildup` was built**, the
brief said so, and task 3 did it.

**The rules the contract fixes**, each with a test: the goal's possession
truncated at the shot; the previous possession in full, only for a set piece
read from `shot.type.name`; raw source records in feed order; no crossing a
period boundary; no padding.

**Read from the data, for Bob's brief and the tests:**

| Match | Goal | `shot.type.name` | Possessions | Events |
| ----- | ---- | ---------------- | ----------- | -----: |
| 1986 | 54:18 Maradona | `Open Play` | 117 | 24 |
| 2022 | 22:24 Messi | `Penalty` | 31, 32 | 100 |
| 2022 | 79:24 Mbappé | `Penalty` | 162, 163 | 10 |
| 2022 | 117:05 Mbappé | `Penalty` | 237, 238 | 11 |

Each penalty's own possession holds exactly one event, the kick. The foul is in
the possession before, and all three have a `Foul Committed` record:
Dembélé at 20:53, Otamendi at 78:13, Montiel at 115:39. **Only two of the three
also have a `Foul Won` record;** the 117:05 penalty does not, so the tests key
on `Foul Committed`.

**Two of the three set piece types have no goal to test.** Among goals in these
two matches `shot.type.name` is only `"Open Play"` or `"Penalty"`.
`"Free Kick"` appears on six 1986 shots, none of which scored, and `"Corner"`
appears in neither match. The contract specifies all three branches; the tests
reach one of them.

**Possessions really do span period boundaries,** which is why the no-crossing
rule is a rule and not a formality: possession 99 of the 1986 match spans half
time, and four possessions of the 2022 final span a boundary. None of the four
covered goals hits the case, so the rule is specified and untested by data.

**The suite.** `tests/test_event_feed.py::TestBuildup` was thirteen tests at this point. While the
method was unbuilt, 12 failed with
`No buildup implementation yet: StatsBombEventFeed has no buildup method` and
nothing else. The thirteenth checks the written-down expected values against
`data/raw/` without touching the implementation, so a wrong expectation fails
on its own line rather than looking like a bug in Bob's code; it passed
throughout and has to keep passing.

**`scripts/check_docs.py` now resolves a count claim to a test class as well as
a test file,** because one file holds two contracts in two states and the only
honest numbers are the file total and the per-class breakdown.

### Phase 4, task 3

**Bob built `buildup`** (`24e1a8d`, 1.22 Bobcoins), against the Task 3 section
of `docs/bob_brief.md`. The export and the task-summary screenshot are in
`bob_sessions/`, and `bob_sessions/README.md` lists them.

**The whole suite passed at that commit.**

The 13 that cover `buildup` are in `tests/test_event_feed.py::TestBuildup`.

**Bob merged the two protocols, which the brief asked for.** `buildup` is now
declared on `EventFeed` itself, and `BuildupFeed` survives in
`app/event_feed.py` as an alias of `EventFeed`. The alias is why the tests
needed no change: their `BuildupFeed` imports and `isinstance` checks still
resolve. One consequence worth knowing is that
`test_satisfies_the_event_feed_protocol` and
`test_the_implementation_satisfies_the_buildup_protocol` now assert the same
thing. That is harmless duplication, not a defect, and collapsing it is a test
change nobody needs yet.

**A latent gap, found while reviewing and left alone.** The previous possession
is filtered to the goal's period, which rule 4 requires. The goal's **own**
possession is not. A goal whose possession began in the period before would
therefore carry events from across the boundary. This is unreachable with the
data in the repo, and that was checked rather than assumed:

| Match | Possessions spanning a period | Goal possessions |
| ----- | ----------------------------- | ---------------- |
| 1986 `3750191` | 99 | 109, 117, 168 |
| 2022 `3869685` | 79, 196, 222, 247 | 32, 52, 163, 165, 228, 238 |

The two sets do not intersect, and every buildup returned for all nine goals is
single-period. So no test fails and nothing is wrong in the output today. It is
recorded here because a third match could reach it, and because the fix belongs
to Bob under the reserved-module rule rather than being patched in from outside.

**No credentials were scrubbed from the export**, because a scan found none: no
variable name from `.env.example`, no bearer token, key, project id or URL
carrying a query string. The export's two mentions of `.env` are the rule text
telling Bob not to open it.

**`.claude/settings.json` now denies reading `.env`:**

```json
{
  "permissions": {
    "deny": ["Read(./.env)"]
  }
}
```

It is committed, so it applies to every Claude Code session in this repo rather
than one machine's local settings. **It closes the file-tool path, not the shell
path.** A `Read(...)` deny covers Read, Grep and Glob; it does not stop a Bash
command such as `grep -r` from sweeping the file. One did, earlier in Phase 4,
which is what prompted the rule: two lines of the file reached a transcript at a
time when it was still at the repo root. The values were the two model ids being
removed anyway, so nothing secret was exposed, but the rule was broken and the
gap is real.

**The shell path was closed in task 2c, by moving the file out of the repo, not
by a hook.** A `PreToolUse` hook on `Bash` reading the command string was the
first idea and it is the wrong one: the command that leaked never named the
file. The deny rule above stays as a second layer.

### Phase 4, task 3

**The written voice, the prompt and the grounding check.** "Voice" here means
how the narration reads, not audio: `docs/VOICE.md` is the voice, and turning
narration into speech is Phase 5.

| Module | What it does |
| ------ | ------------ |
| `app/narration_prompt.py` | the facts a narration may use, the prompt, the fallback |
| `app/grounding.py` | whether a narration's claims trace back to the data |
| `app/narration.py` | generate, check, retry, fall back, record every attempt |

**The failure rule is whole-narration.** A failing line is not dropped, because
a narration with a hole in it tells a different story: the 54:18 run recorded
as past one defender, then another, then the goalkeeper reads as a different
move with the middle cut out. Nor is it kept unlabelled, because the app says
only what the play data proves. So the narration fails together, is regenerated
up to twice, and then falls back to a short plain narration assembled straight
from the events. That fallback is grounded by construction and is checked
anyway. If even it failed, `narrate` raises rather than returning something
unverified.

**The pass rate counts first attempts only.** `Narrated.first_attempt_grounded`
is the number; counting retries would hide how often a model drifts. Nothing in
the repo measures it yet over the nine goals, which is Task 4.

**Three of the check's rules exist because of a live run, not a guess.** The
first end-to-end run against `granite4:micro` failed three attempts and fell
back, and every failure was this repo's bug rather than the model's:

| What failed | Why it was wrong | Fix |
| ----------- | ---------------- | --- |
| `Finally` reported as an invented player | sentence-initial adverbs are not names | the stopword list, now much larger |
| `Argentina's` matched no recorded name | the word pattern keeps apostrophes so O'Brien survives | possessive endings are stripped before lookup |
| `54:04` rejected | the prompt printed per-second clocks and the rules then forbade them | the run of play shows the minute only |

A false positive is the expensive kind here. The narration is thrown away
whole, so a wrongly failed attempt costs good copy and makes a model look worse
than it is. Each of the three is now a named test in
`tests/test_grounding.py`.

**Two rules were added after reading narration that passed.** Both live runs
that got past the name checks still ended on a judgement or a result:
"This decisive moment marked a significant moment in the match's narrative",
and "securing Argentina's victory". Editorial epithets and claims about the
score or the result are now refused. "Win" and "won" are deliberately not in
that list, because `wins a foul` is a recorded `Foul Won` event and banning the
word would fail every penalty buildup.

**What the check could not do, and task 3b changed.** It verified that
everything a line named was in the data; it did not verify that the line's
reading of those facts was right. The worked example was a line that passed:
the records show Beardsley, Butcher, Fenwick and Shilton dribbled past and
Beardsley, Reid and Butcher applying pressure, so "dribbles past Peter
Beardsley, Peter Reid and Terry Butcher" was grounded in every token and still
described something that did not happen. That line is refused now; see the task
3b section below for how, and `docs/VOICE.md` for what is still out of reach.

### Phase 4, task 3b

**The narration cites its facts, and each sentence is checked against the ones
it cited.** The buildup becomes a numbered list of plain facts, one per
recorded event, built by code out of the records:

```
   1. José Luis Cuciuffo (Argentina) recovers the ball, 54:02
  ...
  10. Peter Beardsley (England) is dribbled past, 54:08
  11. Diego Armando Maradona (Argentina) dribbles, 54:08
  13. Peter Reid (England) presses, 54:08
  14. Terry Butcher (England) is dribbled past, 54:13
  ...
  24. Diego Armando Maradona (Argentina) shoots, 54:18
```

The model narrates from that list and starts each sentence with the numbers it
used: `[11] Maradona dribbles past Peter Beardsley.` The check then reads the
sentence against those facts and nothing else.

| Where | What changed |
| ----- | ------------ |
| `app/narration_prompt.py` | `Fact`, the numbered list, `cited_line`, and a prompt built round it |
| `app/grounding.py` | `sentences`, `strip_citations`, and a per-sentence check |
| `app/narration.py` | `Narrated.text` is stripped for showing, `tagged_text` keeps the citations |
| `scripts/narrate_once.py` | new: one goal through a real model, every attempt printed |

**Pairing is what catches misdescription.** Every name in a sentence is paired
with every action in it, and the pair has to meet inside one cited fact. Reid's
only record in that passage is a `Pressure`, so no fact pairs him with a
dribble and no choice of citations rescues the sentence. It fails on Reid alone:
the two defenders it was right about are left out of the report, because a
refusal listing all three would send a retry to rewrite the true part.
`tests/test_grounding.py::TestMisdescription` is that case by name.

**Pairing is blunt, and the cost is in the repo rather than left to be found.**
Nothing in the text says which name goes with which action, so "Di Maria wins a
foul and Messi scores for Argentina" is true and is refused: no one fact pairs
Messi with the foul. Rule 2 of the prompt asks for one action per sentence
because of this, and `TestPairingRefusesSomeTrueSentences` holds both halves,
the refusal and the same words in two sentences passing.

**Per-second clocks are groundable now, which reverses an earlier decision.**
The run of play used to print minutes only, because a per-second clock could
not be checked and a model that quoted one was failed for it. A clock is now
checked against the cited fact's own clock, so the facts print it and "54:13"
belongs to a sentence citing fact 14 or 15 and to no other. `Facts.numbers` is
gone with it: a bare digit is grounded by a cited fact's minute or the goal's
second, and the set of minutes for the whole buildup no longer decides anything.

**Three words were added to `ACTION_CLAIMS`:** "carry", "receive" and "press".
`EVENT_VERBS` says those events in those words, so a model reads them off the
facts and writes them back, and a word the facts use to state an event is a
word that asserts it. The noun "pressure" is deliberately not there: "under
pressure" is as often scene setting as a claim about a `Pressure` record.

**Two parser bugs came out of live runs, not from review.** Both were false
positives, which is the expensive kind here, and both are named tests:

| What failed | Why it was wrong | Fix |
| ----------- | ---------------- | --- |
| every citation shifted by one | the model wrote `... defender. [15] He carries ...`, and a tag was read as part of the chunk it started | a tag at the start of a chunk belongs to the sentence before it |
| four sentences reported as untagged | the model numbered its own lines "1." to "4.", and a bare number before a full stop read as a sentence | a chunk that is only a number is a list marker |

**The prompt's shape was settled by live runs, and three layouts lost.** Asking
for the tag at the end of the sentence, with the goal as the worked example,
got the goal's number on all four sentences: the model read the example as the
answer. Adding a procedure and a no-shared-numbers rule to the same layout got
sentences with no tag at all, which is worse, because a model that has finished
the sentence has nothing left to look up. Asking for the number first got a tag
on every line. Two more variants (one example from the middle of the list, and
the shape with no example at all) were tried and dropped: 0 of 3 each.

**What the live runs actually produced.** Two runs of
`scripts/narrate_once.py` over the 1986 54:18 goal with the prompt as it
stands:

| Run | Model attempts | What came back |
| --- | -------------- | -------------- |
| 1 | 1 refused, 2 grounded | four lines, every citation right, labelled |
| 2 | 1 grounded | one line, labelled |

Run 1's second attempt is the narration this task was for:

```
[1] José Luis Cuciuffo recovers the ball.
[7] Diego Armando Maradona receives the ball.
[9] Peter Beardsley presses.
[24] Diego Armando Maradona shoots.
```

Its first attempt failed on one claim, `[18] Diego Armando Maradona shoots`,
where fact 18 is a dribble and the shot is fact 24.

Two earlier runs under the same layout, before a line of the prompt was
rewrapped, went one each way: one returned model narration of one line, the
other failed all three attempts and fell back to the template. So the fallback
has been exercised live as well as over all nine goals in the tests. Counting
every model attempt across the four runs, 10 of 42 lines carried a bad
citation. **No run produced a false positive:** every refusal named the right
words against the wrong fact number.

So the pipeline works end to end against a real model, and one of the two
first attempts in the table was grounded. Four runs are not a rate; nothing
measures the rate over the nine goals yet, which is still Task 4. What the runs
do say about `granite4:micro` is that it produces the format reliably and
miscites about one line in four: it can say the facts and cannot always copy an
index out of 24 lines.

**One live pass was a degenerate one, and it is worth knowing.** Run 2's
attempt was `[24] Diego Armando Maradona shoots.` and nothing else: grounded,
labelled, and barely a narration, where the prompt asked for four sentences. The
check refuses narration that asserts nothing checkable, not narration that
asserts too little, and nothing enforces the sentence count. Adding a floor
would mean the check refusing copy for its length rather than its grounding,
which is a different job; if it is wanted, it belongs in `app/narration.py`
beside the retry rule.

### Phase 4, task 3d

**The narration is past tense, and it ends on the goal.**

A buildup is playback. A fan opens Prelude after the moment has gone, and
commentary in the present tense tells them it is happening now, which is the one
thing this project is not doing. So `EVENT_VERBS` writes the facts as a record
("dribbled", "was dribbled past", "shot"), the prompt asks for past-tense
narration, and `app/grounding.py` refuses a present-tense verb instead of
grounding it: `ACTION_CLAIMS` holds the past forms and the tenseless nouns, and
`PRESENT_TENSE` holds the present forms with the past form to use instead.

| What was added | Where |
| -------------- | ----- |
| past-tense facts | `EVENT_VERBS` in `app/narration_prompt.py` |
| past-tense action words, and "scored", "recovered", "won" | `ACTION_CLAIMS` in `app/grounding.py` |
| the present forms, refused | `PRESENT_TENSE` in `app/grounding.py` |
| the two auxiliary phrasings, refused | `PRESENT_TENSE_PHRASES` in `app/grounding.py` |
| the ending rule | `check` in `app/grounding.py` |
| the second person, refused | `BANNED_PATTERNS` in `app/grounding.py` |

**"Won" was the word that needed care.** "Won a foul" is a `Foul Won` record and
has to stay sayable; "won the match" is a result no buildup carries. So "won"
grounds against a `Foul Won`, and the outcome-claim pattern reaches past the
verb to its object rather than refusing the word. Both halves are tested, in
`tests/test_grounding.py::TestTense::test_won_a_foul_is_allowed` and
`tests/test_grounding.py::TestTense::test_won_the_match_is_refused`.

**There is no closer.** A closing sentence in the present tense, spoken to the
fan, was the obvious thing to add and is dropped. The goal has just gone in, the
stadium is doing what a stadium does, and a phone saying "that is the moment you
came for" is competing with 80,000 people and losing. It would also be the one
sentence in the narration that no fact could ground. So the narration stops on
the goal: the last sentence has to cite the shot the moment was built from.

Citation placement cannot catch a closer on its own, because a closer can cite
the goal's fact as easily as the goal sentence can. What catches one is the
second person, now refused wherever it appears. A closer that cites the goal,
avoids "you" and asserts nothing checkable is caught by nothing, and
`tests/test_grounding.py::TestEnding::test_what_the_ending_rule_alone_cannot_catch`
records that rather than leaving it to be found.

**One latent parser bug came out of writing the tests.** A tag between two
sentences is ambiguous: in "A. [15] B." the tag can close A or open B, and both
layouts occur. The rule was per tag, which misread a citation-first narration
with an untagged sentence in the middle, binding the next sentence's tag
backwards and so flagging the wrong sentence while hiding the one that cited
nothing. The layout is now settled once per narration by the first chunk, since
a tag opening the first chunk has no sentence before it to belong to.
`tests/test_grounding.py::TestSentences::test_an_untagged_sentence_in_a_citation_first_narration`
is that case.

**The live runs.** Two over the 1986 54:18 goal, both returning grounded,
labelled, past-tense model narration:

| Run | Model attempts | What came back |
| --- | -------------- | -------------- |
| 1 | 1 grounded | four past-tense lines, labelled |
| 2 | 1 and 2 refused, 3 grounded | four past-tense lines, labelled |
| 3 | 1 grounded | four past-tense lines, labelled |

Run 3 is the exit check for this task, run again in a later session against the
same model and the same goal. It came back grounded on the first attempt, in
the past tense, ending on fact 24:

```
[1] José Luis Cuciuffo recovered the ball.
[2] José Luis Cuciuffo carried the ball.
[3] José Luis Cuciuffo passed.
[24] Diego Armando Maradona shot.
```

The tense rule has not refused a live attempt yet: with the facts in the past
tense the model wrote past tense without being corrected, which is what changing
the facts was for. The ending rule did refuse one, and on a real mistake rather
than a hypothetical: run 2's first attempt wrote the goal sentence and then
added another after it. `docs/VOICE.md` carries both runs.

Both grounded narrations are thin in the same way: the model takes facts 1 to 3
in order and jumps to the shot, so the run the goal is famous for is the part it
skips. Nothing refuses a narration for being dull, and nothing should; it is a
model limit and it is worth knowing before the pass rate is measured.

### Phase 4, task 4a

**The pass rate and the coverage are measured now, and the second one is the
bad news.** `scripts/narration_eval.py` narrates every goal three times and
writes `docs/narration_eval.md`. It takes `--goals` (a match id for every goal
in it, or `match:minute:second` for one) and `--runs`, so a change can be tried
on one goal before twenty-seven; `--json` saves the records after every
narration and `--from-json` rebuilds the report from them, which is what keeps
a long run from being lost to a typo in the report code.

Ollama only. There is no watsonx path in the script and no flag that adds one,
because a loop of twenty-seven generations is the shape of accident that spends
money on a paid endpoint; Task 4b writes that comparison and states its call
count first.

The full run, `granite4:micro`, 27 narrations in 854s:

| | |
| --- | --: |
| grounded on the first attempt | 22 of 27 |
| fell back to the template | 1 |
| mean tokens per narration | 1,941 |
| mean wall clock per narration | 32s on CPU |

**Grounding holds up and completeness does not.** Coverage is the share of the
key beats of a passage that a narration cited: the shot, every dribble past an
opponent, and the foul for a penalty. Five of the nine goals have the shot as
their only key beat and read 100% for anything that passed at all, so the
report averages coverage over the five that can move and shows the other four
on their own.

Across those five goals the model wrote fourteen narrations and all fourteen
cited the shot and no other key beat. Not one dribble past a defender, and not
one of the three penalty fouls. Every grounded narration cites the shot
because the ending rule requires it, so those fourteen reached nothing the rule
did not force out of them. The mean, 45%, is kinder than that and moves with
how many beats a goal has rather than with what the model found, which is why
the report prints the count beside it.

**Coverage is split by what wrote the narration.** A template fallback reaches
every key beat by construction, so a column that mixed it with the model's own
narrations would report the fallback's completeness as the model's. First
attempt, after a retry and template are three columns.

**The fallback was thin too, and that was a bug rather than a limit.** It
scored 2 of 5 on the 54:18 goal: grounded in every word and missing three of
the four defenders Maradona went past. It collapsed the run of four `Dribble`
events into one sentence, then trimmed the run-up from the front to fit a
five-sentence budget. A model writing a thin narration is a model limit; code
assembling one out of the facts can see every beat and has no excuse.

So `key_beats` moved into `app/narration_prompt.py`, where the fallback and the
measure read one list rather than two that drift apart. The fallback gives
every key beat a sentence before any other fact is considered, and
`TEMPLATE_MAX_SENTENCES` became a target that a key beat outranks. A dribble
beat is said with its `Dribbled Past` record, which names the player who was
beaten; a foul beat prefers `Foul Won` and falls back to `Foul Committed`,
which is all the 117:05 penalty records. The 54:18 fallback went from

> Minute 54. José Luis Cuciuffo passed. Héctor Adolfo Enrique passed. Diego
> Armando Maradona dribbled. Diego Armando Maradona shot and scored for
> Argentina.

to

> Minute 54. Peter Beardsley was dribbled past. Terry Butcher was dribbled
> past. Terry Fenwick was dribbled past. Peter Shilton was dribbled past. Diego
> Armando Maradona shot and scored for Argentina.

and it now scores 100% on all nine goals:
`tests/test_narration_prompt.py::TestTemplateNarration::test_it_cites_every_key_beat_of_the_passage`
and
`tests/test_narration_eval.py::TestCoverage::test_the_fallback_scores_full_coverage_on_every_goal`.

**The measure is tested against the narration it exists for.** A live first
attempt that passes the check and skips every dribble is pinned with its real
citations in
`tests/test_narration_eval.py::TestCoverage::test_the_thin_narration_covers_only_the_shot`,
which asserts 1 of 5, and a companion test asserts the same narration is
grounded. If coverage ever scores that narration well, the number is measuring
nothing.

Two definition calls are worth knowing. A dribble past an opponent is one beat
recorded twice, a `Dribble` on the attacker and a `Dribbled Past` on the
defender, so citing either covers it; a beat exists only where there is a
`Dribbled Past`, since that is what makes it past an opponent. And the penalty
foul is every foul record in the buildup merged into one beat: keying it on
`Foul Won` alone would have left the 117:05 penalty, which has only the
`Foul Committed` side, reporting that nothing was missing.

Tokens are Ollama's own `prompt_eval_count` and `eval_count`, read through a
transport wrapper rather than estimated from the text. `Transport` is the seam
`app/narration_provider.py` already has for tests, so measuring cost needed no
change to `app/`.

### Phase 4, task 4c

**The beats are named in the prompt now, and the model reaches them.** Task 4a
measured the gap: across the five goals where coverage can move, all fourteen
narrations `granite4:micro` wrote cited the shot and no other key beat, while
passing the grounding check every time. The facts were all in the prompt and
the model took the first few in order and jumped to the goal.

`beats_block` in `app/narration_prompt.py` prints the key beats with the fact
number to cite for each, and asks for one sentence on each before the last
line. It uses the same record the fallback does: the `Dribbled Past` for a
dribble, which names the player who was beaten, and the `Foul Won` for a
penalty foul where there is one. The requested sentence count rises to fit,
because a prompt that asked for four sentences and then named five beats would
have the model drop one instruction to obey the other.

The check is unchanged. Coverage is still reported and not enforced, and a
narration that reaches every beat and miscites one of them is refused as
before.

**Only five goals were rerun, and that is sound rather than merely cheap.**
The block is empty when the shot is the only key beat, so the prompt for those
four goals is byte-identical to 4a's. Checked rather than asserted: the new
`build_prompt` was run against the one at `ca26451` for all nine goals, and
five differed and four did not. The property is pinned by
`tests/test_narration_prompt.py::TestBeatsBlock::test_it_is_empty_when_the_shot_is_the_only_key_beat`.

The five goals, three runs each:

| | Task 4a | Task 4c |
| --- | --: | --: |
| grounded on the first attempt | 12 of 15 | 10 of 15 |
| coverage of the model's narrations | 42% | 95% |
| cited the shot and no other key beat | 14 of 14 | 1 of 14 |

The 54:18 goal went from 1 of 3 grounded at 20% coverage to 3 of 3 at 100%. It
is the first model narration in this repo to name all four defenders.

**The pass rate fell, and the report shows it beside the coverage.** Twelve of
fifteen to ten of fifteen. All of the loss is the 22:24 penalty, 2 of 3 to 0 of
3: a hundred facts, a prompt of around nine thousand tokens, and the goal where
naming the beats asks the most of a 3B model. The other four held or improved.
Asking for more sentences is asking for more chances to cite the wrong fact, so
a change that bought coverage with grounding would be a bad trade dressed as a
good one, and the two numbers sit in one table per goal so it cannot hide.

**Both runs are committed and the report is regenerated from them**, in
`docs/narration_runs/`. `--compare` renders the before and after, so the
comparison in `docs/narration_eval.md` is program output rather than numbers
copied by hand, and the command that produces it is quoted in the document and
runs as written.

What this does not settle is whether a larger model needs the block at all.
Task 4b should run the watsonx candidates with it, since it is in the prompt
now, and a candidate that covers the beats without being told is worth knowing
about.

### Phase 4, task 5

**The orchestrator contract is declared and its tests fail. Bob builds it
next.** `app/orchestrator_contract.py` holds the shapes, the wording table and
six functions, every one of which raises. `tests/test_orchestrator.py` was
handed over with forty-four tests: 38 failed with `NotImplementedError: the
orchestrator is not built yet` and 6 passed. `docs/bob_brief.md` carries the brief as Task 4.

**What the orchestrator is for.** The narration says only what the play data
proves, and that rule leaves it unable to greet anyone, unable to know which
side the listener is on, and stopped dead on the goal. So everything addressed
to the fan happens in one line before the narration, and that line is this
module's whole output. The app's placeholder, "Here's the buildup.", is the
neutral case of it.

| Input | What it carries |
| ----- | --------------- |
| `Event` | kickoff, both teams, the sport |
| `ScoringMoment` | which side scored, the clock, the score after it, regulation length |
| `Listener` | allegiance, and an optional name that stays on the phone |

| Output | What it is |
| ------ | ---------- |
| `greeting` | "today" or "tonight" |
| `header` | the line as shown, prefix and tail already joined |
| `persona` | the default persona id for this listener |

**The rules the tests encode.** "tonight" at or after `EVENING_CUTOFF`, which
is 17:00 and configuration rather than a rule. The phase as a share of
regulation time, early being the first third and late the final quarter, with
a boundary belonging to the later phase. The score state after the moment, for
the listener's side. The header from a fixed table by allegiance, outcome and
phase. "There's still time" never late. The Mate for a fan, the Storyteller
for a neutral listener.

**The phase is where the sport agnosticism lives, so it has a test that cannot
be satisfied by football.** `TestAnotherSport` is a sixty minute game in a
sport that does not exist. Twenty minutes in is late in a ninety minute game
and early in that one. If a 90 is ever written into the phase rule, those
tests fail and no test about the two demo matches does.

**Three details worth knowing before reading the tests.**

Conceding is not the same as being behind. Argentina conceded at 80:37 in 1986
and were still 2 to 1 up, and the header for that is chosen on the outcome
while the score state is a separate answer. Both are tested on that moment.

A neutral listener has no score state and no outcome, and both functions raise
`ValueError` rather than returning a third value. Inventing "level" for
somebody with no side would put a wrong word in a header.

The late conceded cell is empty, so the header is the tail alone. A test
asserts no header runs two spaces together, because an empty prefix joined
carelessly is exactly how that happens.

**The wording is Shawn's to finish.** `HEADER_PREFIXES` in the contract held
the starting wording and `docs/VOICE.md` carried the table with it marked as
unbuilt. The brief told Bob to read prefixes out of the table rather than
writing any into the code, so changing a word stayed a one line edit.

That table is gone: task 2 after 6d replaced it with `HEADER_WORDING`, keyed
by transition, and the follow-up after Bob task 5 removed it from the contract
once nothing read it. The one line edit is to `HEADER_WORDING` now.

**The header is not narration and must never be labelled.** It is built from
the kickoff time, the score and the listener's own answer, none of which is
event data, so "Verified from play data" has nothing to say about it. It is
also the one line in the app spoken to the fan, which is the thing the ending
rule keeps out of narration: the header goes before, and nothing goes after.

**The suite is red on purpose until Bob runs.** `pytest -q` reports
`38 failed, 256 passed`, `docs/HARNESS.md` and `docs/bob_brief.md` both say so
and both are checked against live output by `scripts/check_docs.py`. A failure
outside `tests/test_orchestrator.py` means something is actually wrong.

**Stop here.** Shawn runs Bob against the Task 4 brief. Bob also fixes the
latent period gap in `buildup` in the same session, since that is his module:
the set-piece reach back a possession has nothing stopping it crossing a
period boundary, and no goal in either demo match triggers it today.

### Phase 4, Bob task 4

**The orchestrator is built, by IBM Bob, in `1c4063a`.** `app/orchestrator.py`
implements the six functions declared in `app/orchestrator_contract.py` and
`PreludeOrchestrator`, whose `opening` returns the greeting word, the header
and the default persona together. The contract was not edited.

**Claude Code's follow-up changed where the tests import from.** The tests
written in Task 5 imported the six functions from the contract, which only raises, so they
could not pass unless the contract changed. Bob was forbidden to edit it, and
instead overwrote the contract's functions from `app/orchestrator.py` at
import time, adding an import to `tests/conftest.py` so the overwrite ran
before any test. The tests were the fault, so the fix went there:
`tests/test_orchestrator.py` now imports the functions from
`app/orchestrator.py` and the shapes and wording from the contract, the
overwrite block and the conftest import are gone, and the contract's
functions raise again on their own. Three tests were added in
`tests/test_orchestrator.py::TestTheOpening`, because none of the
handed-over tests called `opening`, which is what the app will call.

**The period gap was not where the brief said.** The brief placed it in the
set-piece reach back a possession, but that reach already filtered by the
goal's period. The unguarded path was the goal's own possession, and
possession 99 of the 1986 match is one that spans half time. Bob added the
period filter there, with
`tests/test_event_feed.py::TestBuildup::test_goal_possession_does_not_cross_period_boundary`,
a synthetic feed that fails without the fix. No goal in either demo match
reaches it, so no narration output changes.

**The suite is all green.** At `f7d8c97`, `pytest -q` reported `298 passed`, and the four
gates pass.

**The late scored header changed after Bob's session.** It read "Your side
again.", which was false for England's only goal in 1986, at 80:37, since
nothing the header is built from records an earlier goal. It became "Late one
for your side.", and a test in `TestTheHeader` covered that goal.

That test is gone: task 2 after 6d replaced the prefix table, and the rule it
held is now
`tests/test_orchestrator.py::TestTheHeader::test_no_header_claims_a_goal_before_this_one`,
which holds all nine goals to it rather than the one.

At `11d0f8f`, `pytest -q` reported `299 passed`.

### Phase 4, task 6a

**The persona config is committed and nothing reads the styles yet.**
`app/personas.py` holds the three personas and `tests/test_personas.py` holds
them to their shape, in 27 tests now and 22 at this commit. No prompt passes a
style to a model at this commit: that is task 6b, and the style field is gone
again after "after task 6d" below.

| Persona | Id | Register | Offered to |
| ------- | -- | -------- | ---------- |
| The Caller | `caller` | play-by-play pace, one action a line | everyone |
| The Storyteller | `storyteller` | documentary calm, measured and plain | everyone |
| The Mate | `mate` | partisan, a supporter in the next seat | fans only |

**The ids were already declared and are not spelled twice.** `CALLER`,
`STORYTELLER` and `MATE` are in `app/orchestrator_contract.py`, because Task 5
had the orchestrator picking a default persona before this config existed.
`app/personas.py` imports them, so a typo is an import failure rather than a
persona nothing can select, and
`tests/test_personas.py::TestTheThreePersonas::test_the_ids_are_the_ones_the_contract_declares`
asserts the set.

**A persona is a register and changes nothing about what may be said.**
`app/grounding.py` reads a narration against the facts it cited whoever asked
for it. A persona that could loosen the check would make "Verified from play
data" mean something different depending on who was listening.

**The two kinds of copy are checked differently, which is the one design
decision in the file.** The Profile line is read by a fan, so the rules
`CLAUDE.md` puts on app output apply to it and
`tests/test_personas.py::TestProfileCopy` scans it. The style text is said to
a model, where naming a banned word is sometimes the only way to forbid one,
which is what rule 7 of the prompt already does; scanning the styles for those
words would refuse the instruction that keeps them out of the narration. Both
are held to the no-em-dash rule.

**The voices were `None` and marked unconfirmed at this commit.** Phase 5
picked them by ear later; a plausible voice id written down here would have
been a guess with the look of a decision, so `voice` and `voice_confirmed`
together said "not chosen". Phase 5 task 1 step 2 set all three, and the test
that refuses a confirmed null voice survived the change:
`tests/test_personas.py::TestTheVoices::test_a_null_voice_is_never_confirmed`.

**One cross-check earns its place.** `default_persona` in
`app/orchestrator.py` returns an id and reads nothing in this config, so a
default that was fans only would hand a neutral listener a persona the Profile
screen then refuses to show them. That disagreement would not raise anywhere,
so
`tests/test_personas.py::TestFansOnly::test_the_default_for_a_neutral_listener_is_one_they_may_choose`
is what catches it.

**One thing was left where it is and is worth saying.** `EVENING_CUTOFF` in
`app/orchestrator_contract.py` carries a comment saying Task 6's config file is
where it belongs. Moving it would change an import in `app/orchestrator.py`,
which is Bob's module, so it stayed in the contract. It is a one line move
whenever that module is open.

`pytest -q` reports `320 passed`, and the four gates pass.

### Phase 4, task 6b

**The persona's style is in the prompt, and the Mate may say "we".**
`build_prompt` takes a persona and a side, `check` takes the same two, and
`narrate` passes both through. `persona=None` is the prompt and the check as
they stood before personas existed, which is what the measured runs in
`docs/narration_eval.md` were made with.

**A persona changes the register and one rule.** Every other rule was the
same text in all three voices, which was asserted rather than asserted about:
a test took the RULES block of each prompt, removed the person rule, and
required what was left to be identical. It went with the per-persona style
text in the task below, along with the class it was in, so it is described
here rather than cited.

| Voice | "we", "our", "us" | "you", "your" |
| ----- | ----------------- | ------------- |
| no persona | refused | refused |
| the Caller | refused | refused |
| the Storyteller | refused | refused |
| the Mate, with a side | allowed over that side's facts | refused |
| the Mate, with no side | the request itself raises | refused |

**One cited fact, not every cited fact.** A partisan sentence needs one cited
fact recorded against the listener's side. That is the shape a name claim
already has, and requiring every cited fact to be theirs would refuse
"[10, 11] We dribbled past Peter Beardsley", which cites the two records of one
dribble and is true for an Argentina listener.

**The pair of tests that makes it concrete is one sentence cited two ways.**
"[11] Our captain dribbled past a defender." is grounded for an Argentina
listener, because fact 11 is Maradona's `Dribble`; citing fact 10 instead,
Beardsley's `Dribbled Past`, is refused, because that record is England's.
Nothing in the words tells them apart, and the team on the cited record is
what does.

**A Mate request from a neutral listener raises in both places.**
`NoSideForAPartisanVoice` comes out of `build_prompt` and out of `check`.
Falling back to a neutral register would return narration in a voice nobody
asked for, and picking a side would tell a listener they support a team they
did not choose.

**Two implementation notes worth keeping.** `FIRST_PERSON` holds patterns
rather than words, because an apostrophe is a word boundary and `we` is
what catches "we're", which the name loop reads as one word it strips nothing
from. And "our" and "ours" joined `NOT_A_NAME`, so a partisan "Our" is
reported once as the first person rather than twice, the second time as a
player nobody has heard of.

**A live check on `granite4:micro`, one run each over the 1986 54:18 goal,**
before any measurement: the Caller was grounded on its first attempt, the Mate
on its second, and the Storyteller fell back to the template after three. One
run each is not a rate, which is what task 6c is for. Worth noting from it:
the Mate's grounded narration used no "we" at all. The voice is allowed the
first person; nothing makes a model take it.

**`persona=None` is still the default everywhere.** No screen and no script
passes a persona yet, so nothing in the app's behaviour changed with this
commit.

`pytest -q` reports `341 passed`, and the four gates pass.

### Phase 4, task 6c

**The personas were measured and they came back nearly the same.**
`scripts/narration_eval.py` grew a `--personas` flag and a persona section,
and 36 narrations ran on `granite4:micro`: three goals, four voices each (the
Mate twice, once per side), three runs apiece, 2001 seconds in all. The
records are `docs/narration_runs/6c_granite4_micro.json` and the report is the
Task 6c section of `docs/narration_eval.md`.

**The exit condition is met.** Every persona produced model-written,
grounded narration on the 1986 54:18 goal and on the 2022 79:24 penalty. The
22:24 penalty is reported whatever it came out as, and what it came out as is
below.

| Voice | First attempt | After a retry | Fell back | Coverage | Words per sentence |
| ----- | ------------: | ------------: | --------: | -------: | -----------------: |
| caller | 1/9 | 3/9 | 6 | 100% | 5.5 |
| storyteller | 5/9 | 7/9 | 2 | 70% | 5.0 |
| mate (Argentina) | 2/9 | 6/9 | 3 | 89% | 5.4 |
| mate (England) | 2/3 | 3/3 | 0 | 87% | 5.3 |
| mate (France) | 0/6 | 3/6 | 3 | 100% | 4.9 |

**A template fallback is counted as a failure,** which is the measurement
decision behind every number above. The fallback is assembled by code out of
the facts in one plain register, so it is neither the model's narration nor
the voice that was asked for.

**Three findings, each a number rather than an impression.**

*The registers did not reach the model.* Words per sentence came out between
4.9 and 5.5 for every voice, the Caller included, whose style asks for short
lines. The sample narrations in the report read alike for the same reason.
This is a statement about a three billion parameter model and about nothing
else; whether a larger one separates them is Task 4b's question.

*The Mate never took the first person.* None of its 18 narrations used "we",
"our" or "us". The rule built in task 6b is tested and correct and has so far
had nothing to rule on, because the model did not reach for the word.

*The style block cost first-attempt grounding.* On 54:18, Task 4c measured 3
of 3 first attempts grounded with no persona; with a persona the same goal is
3 of 12. Retries absorb most of it, 10 of 12 after one, which is why both
rates are printed.

**The Caller failed every run on the 22:24 penalty,** 0 of 3 model-written,
three fallbacks. That goal has a hundred facts and the longest prompt in the
data, and Task 4c already measured it as the one goal the beats block cost
every first attempt. A persona on top of that block is what this row is. The
Storyteller went 3 of 3 on the same goal, so it is not the goal alone.

**What this does not say.** Nothing here is a model choice, and nothing here
says a persona is a bad idea. It says that on the development model the three
styles are not separable by the one measure available, and that is the thing
to retest when a candidate model is picked.

`pytest -q` reports `363 passed`, and the four gates pass.

### Phase 4, task 4b

**`openai/gpt-oss-120b` leads on grounding, and it is not close.** 87
narrations, 155 generation calls, 303,382 tokens reported, 269 seconds, run
once from `scripts/narration_compare.py`. The records are
`docs/narration_runs/4b_watsonx.json` and the report is the Task 4b section of
`docs/narration_eval.md`.

| | `ibm/granite-4-h-small` | `openai/gpt-oss-120b` |
| --- | ---: | ---: |
| narrations | 54 | 33 |
| model wrote it | 31 | 33 |
| grounded on the first attempt | 16 | 33 |
| fell back to the template | 23 | 0 |
| generation calls per narration | 2.26 | 1.00 |
| tokens per narration | 4,095 | 2,493 |
| seconds of generation per narration | 2.7 | 3.3 |

**It is cheaper per narration as well as better,** which is the result worth
reading twice. It costs more per call, 2,493 tokens against 1,812, and it
never makes a second call: Granite needed 122 calls for 54 narrations and
still fell back 23 times. The only column Granite wins is latency, by six
tenths of a second a narration.

**The endpoint had to change, and that is a finding rather than a detail.**
Neither candidate refused `/ml/v1/text/generation`, and both were unusable on
it: it applies no chat template, so Granite answered with the tail of the
prompt ("Nothing else follows. READY") in front of its narration and
`openai/gpt-oss-120b` returned its reasoning as the answer. Both were run on
`/ml/v1/text/chat` instead. A pass rate measured across two endpoints would
compare those as much as the models, so it is one endpoint for both.

**`openai/gpt-oss-120b` is run at `reasoning_effort: low`,** which is the one
setting the two do not share. At the default it spent 1,496 completion tokens
thinking before one narration, against Granite's 60, and a fan waits through
that on every attempt and every retry. At low effort it spends 312 and still
grounded every narration it wrote. Everything else is pinned identically, and
the decoding is pinned at all because watsonx is greedy by default and three
runs of a greedy model are one run reported three times.

**The personas are still not distinguishable, on either paid model.** This is
the question Task 6c left open and the answer did not change. Words per
sentence spread 2.0 across the voices on `openai/gpt-oss-120b` against 0.6 on
the development model, and the Caller, the Storyteller and the Mate wrote the
same five sentences for the 54:18 goal with different punctuation. The styles
are being read as rules and obeyed, not as a voice.

**The Mate did reach for the first person on the larger model**, 9 of its 12
narrations against none on either smaller one, and what it wrote is "Our Peter
Beardsley was dribbled past at 54:08." The check accepts it because every
cited fact is the listener's side, so the rule from task 6b is working. The
prose is not, and nothing here refuses a narration for being stilted.

**The beats block earns its place on Granite too.** On the five multi-beat
goals, with the block 7 of 15 first attempts grounded at 95% coverage; without
it 3 of 15 at 93%. On `granite4:micro` the block cost grounding and bought
coverage. On this model it buys both, so the Task 4c trade is a small-model
trade and not a general one.

**What this does not settle.** One run of each arm, 2 runs on the persona arm
rather than 3, and three goals of the nine. It is enough to rank the two
candidates on grounding, which is what it was for, and not enough to put an
interval on any figure in it.

**What it cost against the budget.** 339,788 metered of the 500,000 hard stop,
which never fired. The estimate before the run was 453,362 at the rate the
development model had shown; the models retried far less than that, which is
the whole reason it came in under.

`pytest -q` reports `393 passed`, and the four gates pass.

### Phase 4, task 6d, step 1: the model is switched

**Shawn picked `openai/gpt-oss-120b` on the Task 4b results.**
`ACTIVE_CANDIDATE` in `app/narration_config.py` names it, and
`tests/test_narration_provider.py::TestTheShippedSettings::test_the_active_candidate_is_gpt_oss`
records the choice while the tests around it hold the thing that matters:
whatever is active, the settings it needs are what gets sent.

**The settings travel with the candidate rather than with the call site.**
`Candidate` gained `chat` and `reasoning_effort`, and `WatsonxProvider` reads
them. Task 4b found that a model id is not enough to reach a model: on
`/ml/v1/text/generation` neither candidate refused and both were unusable,
because that endpoint applies no chat template. A switch that moved the id and
left the endpoint behind would have shipped a model answering with the tail of
its own prompt, and nothing in the suite would have noticed.

| Candidate | Endpoint | Reasoning effort |
| --------- | -------- | ---------------- |
| `ibm/granite-4-h-small` | chat | not applicable |
| `openai/gpt-oss-120b` | chat | low |

An explicit argument still wins, which is what `scripts/narration_compare.py`
and the generation-schema tests use. A model id that is not one of
`CANDIDATES` inherits nothing, so a one-off model cannot pick up another
model's endpoint by accident.

**Nine tests were changed rather than added to.** The ones that assert the
documented `/ml/v1/text/generation` request and response shapes now pass
`chat=False`, because both candidates ship on chat and those tests are about
the generation schema. The schema itself is unchanged and
`tests/golden/watsonx_text_generation.json` still says it came from IBM's
published documentation rather than from a recording.

`pytest -q` reports `402 passed`, and the four gates pass.

### Phase 4, task 6d, steps 2 and 3: the worked examples changed almost nothing

**Each persona was given a worked example of its register, and the voices
still did not separate.** `app/personas.py` gained an `example` beside its
`style`: a short narration in that voice, cited the way a real one has to be,
printed in the prompt under "THE REGISTER, ON A PASSAGE FROM ANOTHER MATCH".
16 narrations on `openai/gpt-oss-120b`, two goals by four voices by two runs,
16 generation calls, 33,071 tokens reported, 37,040 metered against a 60,000
limit, in 61 seconds.

| | Described | Shown |
| --- | ---: | ---: |
| grounded on the first attempt | 16 of 16 | 16 of 16 |
| narrowest voice, words per sentence | 5.9 | 5.6 |
| widest voice | 8.0 | 7.5 |
| spread across the voices | 2.1 | 1.9 |
| the Mate's narrations using the first person | 5 of 8 | 6 of 8 |

**The spread narrowed rather than widened.** On the 54:18 goal the Caller,
the Storyteller and the Mate for an Argentina listener wrote the same five
sentences, differing in whether a clock is introduced by a comma or by "at".
Showing the register did not work where describing it had not, and that is
now two different ways of asking with the same answer.

**The Mate moved, and not the way the example was written for.** The example
says "We recovered it through Quillan". What came back for an England
listener is "We were dribbled past, Peter Beardsley.", five times over. That
is the apposition the example was written to replace, inverted: the name
trails the clause instead of interrupting it. It is grounded, because every
cited fact is England's.

**Nothing was paid for in grounding.** Every one of the 16 was grounded on
the first attempt, as every one was before, so the examples are inert rather
than harmful. They are
committed because the measurement is the point and reverting them would leave
the report describing code that is not there.

**The examples are held to the rules they teach.** Each one runs through the
real `app/grounding.py` against the invented passage it narrates, which
caught the first draft: the Caller's example read "Quillan won it back",
which the check reads as a claim about a `Foul Won` event over a fact
recording a recovery. An example that breaks a rule is the prompt teaching a
model to fail the check.

**What this leaves for Shawn.** Three ways of getting three voices out of one
model have now been measured and none worked: a described register on a small
model, a described register on a capable one, and a shown register on a
capable one. The question is no longer "how do we make the personas
distinguishable" but "do three personas earn their place in the app". That is
a product decision, and Task 7 waits on it.

`pytest -q` reports `417 passed`, and the four gates pass.

### Phase 4, after task 6d: one narration style, and the personas become voices

**Shawn's decision, on the three measured runs: the personas are separated by
sound and not by text.** Tasks 6c, 4b and 6d asked three models for three
registers three ways and got one register back each time, so the per-persona
style text and the worked examples are out of the prompt and out of the
config. The narration text is one text now: `NARRATION_STYLE` in
`app/narration_prompt.py`, which is the Storyteller's style text, printed in
every prompt under "THE STYLE".

**`build_prompt` takes no persona and no side.** It took both from task 6b to
task 6d. An argument that changed nothing would read as a register still
reaching the model, so the signature says what is true and
`tests/test_narration_prompt.py::TestTheOneNarrationStyle::test_the_prompt_takes_no_persona_and_no_side`
holds it there. `narrate` still takes both and passes them to the check alone.

**The Mate's "we" is out of the prompt and still guarded in the check.** The
prompt now refuses the first person in the one voice it has, the Mate
included. `check` in `app/grounding.py` is unchanged: it admits "we", "our"
and "us" from a partisan persona in a sentence citing a fact recorded against
that side, and refuses them everywhere else. Nothing asks a model for the
word any more, so that rule is a guard against a model that writes it anyway.
`NoSideForAPartisanVoice` moved to `app/grounding.py`, which is now its only
raiser.

**What a persona carries instead.** `style` and `example` came off `Persona`
and five Phase 5 fields went on, every one of them `None`: `voice`, `rate`,
`pitch`, `sentence_break` and `goal_break`, with `voice_confirmed` and
`prosody_confirmed` false. The two breaks are milliseconds so the one before
the goal can be read against the one between sentences. The `profile` lines
describe a voice rather than a way of writing: "Quick play-by-play, keeping up
with the move.", "Calm documentary, unhurried and even.", "Warm, from the next
seat."

**The measured negative result is kept.** The Task 6c, 4b and 6d sections of
`docs/narration_eval.md` are unchanged in their numbers and each one now
carries the same label: the code they measured is gone, and the runs are at
`8f784cf`, `abf5702` and `128833a`. `scripts/narration_eval.py` writes that
label, because the report is generated and a hand-edit would be overwritten by
the next run. The report was regenerated from the saved records with
`--from-json`, so no model was called to produce it.

**One live check on `granite4:micro`, the 1986 54:18 goal, 3 runs.** The
single-style prompt grounds. Two of the three narrations were written by the
model and accepted by `app/grounding.py`, one on its first attempt and one on
its second; the third failed three attempts and fell back to the template.
Coverage was 5 of 5 key beats in all three, and the run took 235 seconds on
CPU.

```
.\.venv-prelude\Scripts\python.exe -I scripts\narration_eval.py \
    --goals 3750191:54:18 --runs 3 --out <outside the repo> --json <outside the repo>

[1/3] first attempt refused, model, coverage 5/5, 3429 tokens, 127.8s
[2/3] first attempt refused, template, coverage 5/5, 4947 tokens, 44.8s
[3/3] first attempt grounded, model, coverage 5/5, 1846 tokens, 62.1s
first attempt grounded 1/3
mean coverage          100%
```

The report and the records were written outside the repo, because this is a
check that the prompt still works and not a measurement:
`docs/narration_eval.md` holds the runs that are measurements, and
overwriting it with three narrations of one goal would lose them.

**Three runs is not a rate and this one is not offered as one.** For context
rather than as a comparison: on this goal and this model, Task 4c measured 3
of 3 first attempts grounded with no style block in the prompt, Task 6c
measured 3 of 12 with a persona's style block, and the shipped model grounded
16 of 16 first attempts with one in Task 6d. A style block costing a small
model its first attempt is a finding Task 6c already reported, and no watsonx
call was made for this task.

`pytest -q` reports `408 passed`, and the four gates pass.

### Phase 4, task 2 after 6d: the game-focused header, contract and failing tests

**The header now says what the goal did to the score, and nothing is built
yet.** This task is a handover: the shapes, the wording and the tests, with the
two functions declared and raising, for IBM Bob to implement as Task 5. The
suite is deliberately red, which is the first time in this repo it has been.

**`ScoringMoment` carries the score before the moment as well as the score
after it.** `score_before_a` and `score_before_b` are passed by the caller and
never derived: subtracting one from the scoring side would read football into a
shape meant to outlive it, since a score can move by any number of points.
`__post_init__` refuses a pair that one side scoring cannot explain, which is
the only code in the contract: the scoring side's score has to have risen and
the other side's has to be the number it was. That catches a before and an
after swapped and a before copied from another moment, where they are made.

**A transition is read out of those two scores and out of nothing else.** Five
of them, from the scoring side's point of view, and they are exhaustive over a
score that rose for one side only: `TAKE_LEAD`, `OVERTAKE`, `EXTEND`,
`CLOSE_GAP` and `DRAW_LEVEL`. No transition depends on anything earlier in the
match, because nothing it is given records one. `HEADER_WORDING` is keyed by
transition, `SCORE_LINE` is the score, `HEADER_TAIL` is the sentence every
header ends on, and `docs/VOICE.md` carries all three.

**`header` lost its listener argument.** It takes the event and the moment, and
one moment gives one line to a fan of either side and to a listener with none.
Allegiance picks the persona, through `default_persona`, and nothing else.

**The old table was still in the contract and still what ran.**
`HEADER_PREFIXES` and `FAN_TAIL` stayed because `header` in
`app/orchestrator.py` read them, and that module is Bob's. The Task 5 brief
told him not to remove them either: the contract is the handover, and a
contract edited in the session that implements against it stopped being one.
Claude Code took them out in the follow-up after his session, along with
`NEUTRAL_TAIL`.

**`tests/test_orchestrator.py` is 72 tests now, up from 48.** Every goal in
both demo matches is read
out of the feed, with the score before and after counted from the goals
themselves and reconciled against the match index, which is a separate file.
Only the nine header lines are written down. `TestAnotherSport` gained a score
that moves three at a time, which is how `OVERTAKE` is reachable at all: a goal
is worth one, so a side that was behind is level or still behind afterwards, and
neither demo match contains that transition. A `built()` helper looks each
unimplemented function up by name at call time, so an absent `transition` is one
failing test naming it and the brief, rather than an ImportError that collects
nothing.

The header tests handed over with Bob's task 4 are gone, along with the contract
tests about `HEADER_PREFIXES`. Two header tables, both tested, would have left
it unclear which one the app is meant to say.

**The 26 failures are the header and nothing else.** They are
`TestTheTransition` (6), `TestTheHeader` (10), `TestTheOpening` (3) and
`TestAnotherSport` (7). The three in `TestTheOpening` call `opening` and differ
on the header attribute alone: the greeting and the persona match.

```
.\.venv-prelude\Scripts\python.exe -m pytest -q

26 failed, 406 passed

.\.venv-prelude\Scripts\python.exe -m pytest tests/test_orchestrator.py -q

26 failed, 46 passed
```

**`scripts/check_docs.py` accounts for the red.** `docs/HARNESS.md`,
`README.md` and `docs/bob_brief.md` carry the split rather than a passing
total, the quoted pytest result in the brief is checked against live output, and
`bob_sessions/phase4_task5_header.md` is on `DELIBERATELY_ABSENT` because the
Task 5 brief names the export before the session has been run.

### Phase 4, Bob task 5: the game-focused header

**The header is built, by IBM Bob, in `7f1b21e`.** `transition` and `header`
are in `app/orchestrator.py` and `PreludeOrchestrator.opening` says the new
line. The suite went green with that commit: the 26 red tests were the header
and nothing else, exactly as task 2 after 6d had set them up.

```
.\.venv-prelude\Scripts\python.exe -m pytest -q

432 passed

.\.venv-prelude\Scripts\python.exe -m pytest tests/test_orchestrator.py -q

72 passed
```

**Bob reported that nothing reads `HEADER_PREFIXES` or `FAN_TAIL`**, which the
brief asked him to check and not to act on. He left both in the contract.

**Bob found two tests built with the wrong scoring side**, in
`TestAnotherSport`: `test_three_points_from_far_behind_closes_the_gap` and
`test_three_points_can_draw_it_level`. Both called the moment helper with the
default `side=TEAM_A` for a scenario that only works with `side=TEAM_B`, so a
side that was meant to be behind was in fact ahead, and both expected a
transition the data could not produce. **The defect was in the tests Claude
Code wrote, not in Bob's implementation.** He stopped and reported it rather
than editing around it, which is what the stop condition asks for. Shawn
approved the fix in the session, only `side=TEAM_B` was added to the two
calls, and no expected value changed.

### Phase 4, the follow-up after Bob task 5: the old header comes out

**Claude Code's task, not Bob's.** `HEADER_PREFIXES`, `FAN_TAIL` and
`NEUTRAL_TAIL` are out of `app/orchestrator_contract.py`, with the comments
that explained why they were still there. `grep` over `app/`, `scripts/` and
`tests/` returns nothing for any of the three. `docs/VOICE.md`,
`docs/HARNESS.md`, `README.md`, `docs/bob_brief.md` and the records above were
updated in the same commit, and every count and quoted pytest result in them
comes from the output above.

`bob_sessions/phase4_task5_header.md` came off `DELIBERATELY_ABSENT` in
`scripts/check_docs.py`, which empties that list. The export was scanned
against the list in `bob_sessions/README.md` before it was committed: no
variable name from `.env.example`, no `.env` mention, no bearer token, no
key-shaped string and no URL of any kind. Nothing was scrubbed.

**Three functions are left with no caller, and all three stay.** `phase`,
`score_state` and `outcome` are implemented in `app/orchestrator.py` and
declared in `app/orchestrator_contract.py`. The old header was the only thing
that called any of them; nothing in `app/` or `scripts/` calls one now, and
only `tests/test_orchestrator.py` does, directly, which is why the suite does
not notice.

They are **candidates for a later Bob cleanup task**, not for this one: they
are in Bob's module, and removing them means removing their tests and their
declarations together. Where they are, at this commit:

| Function | `app/orchestrator.py` | `app/orchestrator_contract.py` |
| -------- | --------------------: | -----------------------------: |
| `phase` | 54 | 271 |
| `score_state` | 71 | 282 |
| `outcome` | 90 | 291 |

`phase` is the one with a use beyond the header if anything wants it: it is
the sport-agnostic read of how far into a game a moment is. Task 7 shows the
header on the moment card and may want none of them.

### Phase 4, task 3c

**Four documents, each statement carrying its file and its test.**

| Document | What it covers |
| -------- | -------------- |
| `docs/HARNESS.md` | the environment, the data, the eight entry points, the test harness and its two guards |
| `docs/VERIFICATION.md` | the five claim surfaces and the checker for each, with one test per claim kind |
| `docs/GOVERNANCE.md` | each rule in `CLAUDE.md`, what enforces it, and where the weak layer is blind |
| `docs/IBM_STACK.md` | Bob's module and its session exports, the watsonx provider, both candidate model ids, and TTS and Orchestrate under Planned |

**The citations are checked, which is the point of writing them.**
`check_cited_tests` in `scripts/check_docs.py` resolves every test a doc names
against a live `pytest --collect-only` run, in all three forms pytest addresses
one plus a bare class or test name. It found nothing stale on its first run, so
it was tested the other way: three bad citations were added to `docs/HARNESS.md`
and the gate reported all three, one per form.

The gate now reads 13 docs, and on this commit it resolves 132 citations of a
test alongside 208 path references. The number of count claims it checks is not
quotable here, because this paragraph would be one of them: the first draft of
it put a figure in front of the word "test" twice, and `check_test_count` read
both as claims about the suite and failed. That is the older check working on
the newer document, not a false alarm, and it is why the sentence is phrased
this way.

**What the new checks share with the old ones.** The four documents went into
`DOCS`, so they get the path check and the no-em-dash check that every doc
already had. `TEST_TARGET_CITE` became `TEST_NODE_CITE` and now matches a full
node id as well as a file and a class, so a count claim beside a single cited
test is scoped to that test rather than read as a claim about the suite.
`collected_targets` became `collected`, which keeps its one collection run
because three checks now read it.

**Nothing tests `scripts/check_docs.py` itself,** as with the other two gates:
its evidence is the counts it prints and its exit code. `docs/VERIFICATION.md`
says so in the same words, under what is not verified.

**`README.md` gained a documents table** so the four are findable, and it states
the one property that makes them evidence rather than description.

### Phase 4, task 2c

**The credentials moved out of the repo.** They now live at `~/.prelude/.env`
by default, which is `C:\Users\shawn\.prelude\.env` on this machine, or
wherever `PRELUDE_ENV_FILE` points. `app/credentials.py` is what finds and
reads them. `.env.example` stays in the repo: it lists the variable names,
holds no values, and that is what makes it safe to read and safe to commit.

**Why a hook was the wrong fix, and this is the right one.** The obvious answer
to the Phase 4 leak was a `PreToolUse` hook on `Bash` that blocks commands
mentioning `.env`. It has a blind spot exactly where the leak happened. The
command that leaked was a recursive `grep -r` over the whole folder: it never
named `.env`, it swept the file up by searching everything, and a hook reading
the command text would have waved it through. It would also have needed a
carve-out for `.env.example`, which sessions are meant to read. Moving the file
out of the working directory closes the path itself, for every tool and every
command, with no pattern to maintain.

**A path inside the repo is refused, not read.** Pointing `PRELUDE_ENV_FILE`
back into the working directory would give up the only property the move buys,
so `load` and `describe` both raise `CredentialsInsideRepo` instead.

**Nothing prints a value.** `describe` reports the path and the variable names a
file defines, and no values, which is what the missing-credential report uses.
It answers the question a missing credential actually raises, which is "which
file did it read?", without putting a key in a terminal or a transcript.

**The process environment wins over the file.** A variable exported in a shell
is a deliberate override for one run, and a file on disk quietly beating it
would be surprising.

**No test reads the real file.** The 29 tests in `tests/test_credentials.py`
each write a fake into pytest's temporary directory and pass that path in, and
an autouse fixture in `tests/conftest.py` points `PRELUDE_ENV_FILE` at an
absent path for the whole suite. That guard is not decoration: the
missing-credential report asks `describe` which file it looked in, and the
default is the real one, so without it the suite would have opened it. Names
only, so nothing would have leaked, but opening it at all is what the rule
forbids.

**The second layer stays.** The `.env` entry in `.gitignore`, the `.env` line
in `.bobignore`, and the `Read(./.env)` deny rule in `.claude/settings.json`
are kept in case a file is ever created at the repo root by habit. None of them
is the live location, and each says so where it sits.

**Shawn has to move the file himself.** Nothing here will do it: that would mean
opening it. At the time of this commit the default path did not exist, which
`app/credentials.py` reported as "no credentials file at
C:\Users\shawn\.prelude\.env".
