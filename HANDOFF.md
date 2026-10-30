# HANDOFF

State of the repo at the end of Phase 2. Every number below came from a command
that ran; see `docs/data_check.md` and `docs/DESIGN.md` for the generated and
derived reports.

## What was built

### Phase 1

**Scaffold** (`d11f686`): `app/`, `scripts/`, `tests/`, `docs/`, and
`data/raw/`. `data/raw/` is gitignored; raw StatsBomb data is never committed.

**`scripts/fetch_statsbomb.py`** (`17795e9`): downloads from
`github.com/hudl/open-data` into `data/raw/`:

| File | Size |
| ---- | ---: |
| `competitions.json` | 34,887 bytes |
| `matches/43/54.json` (1986 World Cup) | 5,392 bytes |
| `events/3750191.json` (Argentina vs England) | 2,364,101 bytes |
| `matches/43/106.json` (2022 World Cup) | 119,132 bytes |
| `events/3869685.json` (2022 final) | 3,757,121 bytes |

The 2022 season id (`106`) and the final's match id (`3869685`, Argentina vs
France, 2022-12-18) are resolved at runtime: season by `season_name == "2022"`
in `competitions.json`, match by `competition_stage.name == "Final"`, failing
hard unless exactly one match matches. Nothing is hardcoded from memory.

**`scripts/data_check.py`** (`bdb83e7`): reads `events/3750191.json`, lists
goals and shots per team, and generates `docs/data_check.md`.

**Docs** (`ae582d2`, `f59e135`): `CLAUDE.md`, `README.md` skeleton, this file.

### Phase 2

**Housekeeping** (`c52358c`): `data_check.py` writes with `newline="\n"`, so
the generated report stays LF and no longer trips git's CRLF normalization
warning. `fetch_statsbomb.py` creates `data/raw/` explicitly at startup, which
was verified by deleting the directory and re-running. The voice test leftovers
moved into the already-ignored `voice_test/`. 20 em dashes removed from the
docs and the no-em-dash rule recorded in `CLAUDE.md`.

**Screens** (`ee7ba82`): four screens into `app/web/`, 750 lines in total.
Sizes as committed at `ee7ba82`; later copy fixes changed three of them.

| Screen | Size |
| ------ | ---: |
| `prelude_01_picker.html` | 17,815 bytes |
| `prelude_02_live_seated.html` | 14,554 bytes |
| `prelude_03_moment_card.html` | 17,522 bytes |
| `prelude_04_moments.html` | 24,548 bytes |

Copy-only fixes: the buildup headline and share title replace the 60-second
framing, the narration quote ends at "and finishes.", the 60S and 45S BUILDUP
meta values and the three player timers are gone (spans left in place and
empty, for Phase 5 to fill from real fixtures), and the nicknamed accessibility
labels are now descriptive. The reversed Hudl StatsBomb logo sits beside both
text credits, copied unrenamed and byte-identical from the supplied set.

**`scripts/scan_copy.py`** (`ee7ba82`): gates the banned strings across the
screens and exits non-zero on any hit.

**`docs/DESIGN.md`** (`1b56a62`): the design system as the screens define it,
derived from the inline `tailwind.config` and the markup that uses it, with a
file and line citation on every value. 291 lines.

### Phase 3

**Bob built the EventFeed module**, in two sessions, against `docs/bob_brief.md`.
The exports and the task-summary screenshots are in `bob_sessions/`, and
`bob_sessions/README.md` lists them.

| Task | Commit | Bobcoins |
| ---- | ------ | -------: |
| Build `StatsBombEventFeed` | `3ce6bca` | 0.463 |
| End event windows at the goal shot | `343c712` | 0.508 |

**`app/statsbomb_event_feed.py`** (`3ce6bca`): `StatsBombEventFeed`, satisfying
the `EventFeed` protocol in `app/event_feed.py`. Standard library only. It reads
`data/raw/events/<match_id>.json`, returns Goal-outcome shots from periods 1 to
4 as moments, and returns the run-up to a moment as untouched source records.
The contract was not changed, so `Moment` still carries no period field and the
shootout exclusion stays a rule the module applies.

**The window fix** (`343c712`): `event_window` filtered by clock time alone, so
where StatsBomb records the goalkeeper's event in the same second as the shot,
the window ran one event past the goal. It affected 6 of the 9 goals across the
two matches. The fix also excludes any event whose `index` is above the goal
shot's, and the second session tightened
`test_window_ends_at_the_moment` so the last event in a window has to be the
goal shot itself. That is the one test change Bob made; the other 13 are as
written in Phase 2.

**Penalties come back as a window holding only the kick.** Three of the nine
goals are penalties, and each one is alone in its own possession, with the foul
that won it 71 to 93 seconds earlier in the possession before. A 30 second
window around an open-play goal holds 22 to 36 events; around each of the three
penalties it holds 1. This is correct under the contract, which does not cross a
period boundary or pad a window, but it means **Phase 4 cannot narrate a set
piece from the window alone: it needs the prior possession.** Run
`defining_moments` and `event_window` over both matches to see it.

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
`tests/test_narration_provider.py` is 50 tests, and `tests/conftest.py`
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

### Phase 5: the Watson Text to Speech facts

Recorded here because Task 3 built no audio code and these are not in the
repo. They came from Shawn, not from the credentials file, which nothing here
opens.

| What | Value |
| ---- | ----- |
| Service | IBM Watson Text to Speech |
| Instance | the Dallas instance in the team's IBM Cloud account |
| `TTS_URL` | that instance's service URL |
| `TTS_VOICE` | an IBM voice name |
| Working default | `en-GB_GeorgeExpressive` |
| Alternative | `en-GB_GeorgeNatural` |

**The final voice pick is Shawn's, by ear, later.** Do not settle it from a
spec sheet. The two files in the gitignored `voice_test/` are an earlier
audition of the same pair.

### Phase 5, task 1, step 1: the delivery probe

**The plan this task started from would not have worked, and reading the docs
is what caught it.** It set each persona's rate and pitch with `<prosody>`
tags. IBM's SSML reference says "The `<prosody>` element is not supported for
Natural voices", and all three candidate voices are Natural voices. The same
page says the service silently ignores unsupported SSML, so the tags would
have been accepted, the audio would have come back, and every persona would
have sounded the same.

`scripts/tts_probe.py` measured what does work. Six arms a voice, 18 calls,
642 submitted characters against a 3,000 budget, and the audio is in
`C:\Users\shawn\prelude_voice\probe` for Shawn to compare by ear.

| Control | Heidi | Emma | Ethan |
| ------- | ----- | ---- | ----- |
| `rate_percentage`, both ways | works | works | works |
| `pitch_percentage`, upward | works | works | works |
| `pitch_percentage`, downward | ignored | ignored | ignored |
| `<break time="600ms"/>` | works | ignored | ignored |
| `<prosody>` rate or pitch | ignored | ignored | ignored |

`docs/VOICE.md` carries the durations and the pitches. Three findings behind
that table shaped everything after it:

**"Ignored" was measured, not inferred.** Those responses are byte for byte
identical to the plain one, same SHA-256. A control that does nothing and a
control too subtle to hear are indistinguishable by any other measure, which
is why the probe hashes the audio.

**The break works on one voice of three,** and on that one a 600 ms break
added 1.36s. IBM labels `<break>` beta for Natural voices with timing that may
vary, and that is what varying looks like. Pauses are a Caller-only control.

**Pitch moves up and not down.** +20 works on all three voices and -20 is
ignored on all three, measured twice in two separate runs. It is not that
negatives are refused: an earlier arm at -50 halved Heidi's pitch exactly,
222.2 Hz to 111.1 Hz, the -12.00 semitones IBM documents. Where between -50
and -20 it stops being honoured is not known here, and nothing depends on
knowing.

**Two measurement notes, both corrected before anything was written down.**
The WAV header's length field is a streaming placeholder, `0xFFFFFFFF` for
both the RIFF size and the data chunk, so `wave.getnframes()` reported
89478.49 seconds for every file on every voice and every delta came out zero.
The duration now comes from the bytes that arrived. And duration cannot see a
pitch change at all, so the probe estimates f0 by autocorrelation; it agrees
with the service's own arithmetic, 3.16 semitones predicted for a 20 percent
rise against 3.16, 2.67 and 3.16 measured.

`--from-audio` re-measures the files already on disk and sends nothing, which
is how both corrections were made without paying for the audio twice.

### Phase 5, task 1: what was built on top of the probe

**The voices are recorded and the delivery is not.** `app/personas.py` carries
one voice each with `voice_confirmed` true, which says Shawn chose them rather
than that this repo listened to them. The four delivery numbers left that file
for `app/delivery.py`, keyed by persona and situation: the probe settled that a
delivery is per request and that the same voice does not deliver a goal for
the listener's side and one against it the same way, and a single rate on a
persona could not say that. Every value in all eight rows was a placeholder
at that point; task 2 filled them in.

**The rules around the empty table are the work.** Filling it in is an edit to
one file and a run of the suite, because the bounds are already enforced: no
lowered pitch, since the service ignores one; no pause on a voice whose breaks
do nothing; IBM's own bounds on the rate; and the Mate never brighter or
quicker when the other side scored, written as a comparison between its own
two rows so it survives any pair of numbers picked by ear.

**The pronunciation table reaches the speech request and nothing else.** The
guard is structural, because neither failure announces itself: a header
carrying markup still reads correctly to anything that strips tags, and a
narration marked up before the grounding check comes back refused for an
ungrounded name, which sends a reader to the wrong file.

**`<phoneme>` took two arms to settle and the first was worthless.** Asking
for `liːd` returned byte-identical audio, which reads exactly like the
`<prosody>` result and means nothing of the kind: an element asking a voice
for what it already does cannot be told from one thrown away. Asking for
`lɛd`, the metal, changed the audio on all three voices, so the element is
honoured.

**The entry is needed, and a wrong conclusion about it was corrected in task
2.** This file said the identical `liːd` audio proved the voices already say
"lead" correctly, so the entry cost 44 characters and changed nothing audible.
That was a conclusion about one sentence dressed up as a conclusion about a
word. The probe spoke "Argentina take the lead.", and both hero headers say
"Argentina **extend** the lead." Shawn listened to that one: "led" without the
entry, "leed" with it. So the entry is doing real work on the shipped path,
and nothing was spent re-proving it, because a listener hearing the difference
is the evidence this question takes.

Two mistakes in one measurement, and both are worth not repeating: asking a
control for what the voice already does, and measuring one sentence to settle
a word. A pronunciation is a property of a word in a context.

**The suite replays a real exchange and makes no call.**
`tests/golden/tts_synthesize.json` cost 83 submitted characters to record. It
holds the request and the first 128 bytes of the response, with the full length
and SHA-256 of the rest, and it says so in its own provenance block: the
backend returns the bytes it was handed without examining them, so that is
what a replay has to assert.

**Nothing secret can reach a fixture.** `SpeechRequest` carries the path, the
query and the body and not the host, because `TTS_URL` holds an instance id,
and its `Authorization` header reads redacted because the real one is built
inside `send` and lives for one call. That is what made the recorded request
safe to commit.

**The hero samples are eight files in `C:\Users\shawn\prelude_voice\samples`.**
The first run was six calls for eight files, 1,794 submitted characters
against a budget of 2,500: with the delivery table empty the Mate's two sides
built the identical request, so two files were the same audio under two names,
and the script said which rather than paying twice and hiding it. Task 2
regenerated the four Mate files once the table was filled in, four calls and
1,196 submitted characters. The Caller and Storyteller files are still from
the first run and carry no delivery. `docs/VOICE.md` lists all eight with
their lengths.

### Phase 5, task 3: "minute", and looking words up instead of hearing them

**All three voices read "Minute 54." as "my-NEWT".** The app means the unit of
time and only ever means it: the word comes from `template_narration`, which
opens a narration on the clock, so it is the first sentence of most of what a
fan hears. `minute` to `ˈmɪnɪt` is the second entry. No synthesis was spent on
it, since October's allowance is near its limit and the element is already
proven by the `lɛd` arm; Shawn confirms it by ear after November 1.

**The voices were not misreading it.** The CMU Pronouncing Dictionary lists
`M AY0 N UW1 T` beside `M IH1 N AH0 T` for that spelling. Both entries so far
are heteronyms, both were caught by a person listening after the audio was
paid for, and both were predictable from a dictionary before anybody listened.

**So the vocabulary is now looked up in advance.**
`scripts/check_vocabulary.py` collects every word the app can speak, from the
header wording, the event verbs, the narration template, the team names in
`app/web/matches.json` and the recorded narrations in `tests/golden/`, and
reports any spelling the dictionary lists more than one pronunciation for. 54
words on this commit, 19 flagged.
`tests/test_vocabulary.py::TestEveryFlaggedWordHasBeenReviewed::test_no_flagged_word_is_unreviewed`
fails on a flagged word that is neither in `PRONUNCIATIONS` nor on
`CHECKED_NO_ENTRY_NEEDED`, so new vocabulary cannot reach a voice unreviewed.
That was checked by removing "the" from the reviewed list and watching it go
red.

**It found one thing worth finding.** "close" is a heteronym, and the header
says "close the gap" on one transition, where it is the verb. It is the third
entry and the first that came from the dictionary rather than from a listener,
so nobody has heard it: Shawn confirms it with the other two after the reset.
Sixteen of the nineteen need nothing and carry their reasons in
`app/pronunciation.py`; they are full against reduced forms of function words
and unstressed vowels in verbs. One word, "miscontrolled", is not in the
dictionary at all and is reported as unchecked rather than flagged.

**The dictionary is a dev dependency and is never fetched.** `cmudict` ships
its data in the package, which is what lets the suite run it with the network
blocked.

**A claim in three documents was wrong and is corrected.** They said a
narration marked up before the grounding check would be refused for an
ungrounded name. It is not: the plain and the marked-up 1986 narration both
come back grounded on the same 35 claims, because the check reads names,
actions, clocks and numbers against cited facts and "phoneme", "alphabet" and
"ipa" are none of those. So that mistake would be accepted, labelled "Verified
from play data" and read out with the markup in it, with nothing raising. The
structural test that reads source is the only guard against it, which is now
what the documents say. **Task 4 changed that:** the check refuses markup
outright and the structural test is the second layer.

**One housekeeping note.** `uv add` writes to `.venv`, not to the
`.venv-prelude` that `CLAUDE.md` names, and it created a stray one. The
dependency was installed with `UV_PROJECT_ENVIRONMENT=.venv-prelude uv sync`
and the stray directory was removed. Worth remembering for the next
dependency.

**What is owed.** The Caller's rate ceiling, which is words per minute off
real audio and is `None` until something measures it: the Caller's rate being
set at +10 does not settle how high anybody may set it. Regenerating the
Caller and Storyteller samples, once Shawn has heard the Mate and knows
whether the numbers are close. And a decision on where between -50 and -20
`pitch_percentage` stops being honoured, if anything ever needs a lowered
pitch. And Shawn's ear on the two unheard pronunciation entries after
November 1, which is "minute" and "close"; this said all three and was
corrected in task 4. "lead" has been heard with its entry, in Shawn's own
test and in the hero samples, which carry it.

### Phase 5, task 4: the grounding check refuses markup

**The hole task 3 measured is closed.** `BANNED_PATTERNS` in
`app/grounding.py` refuses any narration containing `<` or `>`, labelled
"markup", beside the em dash rule. Narration here is plain prose: nothing the
prompt or the template writes holds either character, so there is no good
narration to lose by refusing both.

**It is the characters and not the element.** Matching `<phoneme` would catch
the one mistake anybody has made and nothing else, and a half-written tag is
not a smaller problem than a whole one.
`tests/test_grounding.py::TestNotGrounded::test_markup` and
`::test_either_bracket_on_its_own` hold that.

**The measurement that used to say the opposite now says this.**
`tests/test_pronunciation.py::TestTheClockInARealNarration` ran the real 1986
narration through `for_speech` and asserted both forms came back grounded on
the same 35 claims. It now asserts the marked-up form is refused with
"markup" and nothing else, and that the plain narration still passes on its
35. The structural test that reads source is kept and is now described as the
second layer: the check catches marked-up narration arriving at it, and
`TestNothingElseAppliesIt` catches a module that could write markup into a
header, which no check ever sees.

**Four documents said the source test was the only guard** and now say what
the check does: `docs/VOICE.md`, `README.md`, `docs/VERIFICATION.md` (a
`banned` row for markup) and the `app/pronunciation.py` docstring. Two stale
counts went with them: the README called `lead` the table's one entry, which
task 3 made three, and `docs/VOICE.md` called it "the first and so far only".

**The pronunciation record is corrected.** Shawn heard "lead" with its entry
in his own test and in the hero samples, so it is settled; "minute" and
"close" are the two nobody has heard, and they wait for November 1. Three
places said or implied all three were waiting.

`pytest -q` reports `660 passed` and the four gates pass.

### Phase 5, task 5: the hero recordings, built and refused

**The script and the words are finished; there is no audio.** Watson Text to
Speech answered `HTTP 403 Forbidden` to the first call of the run on
2026-10-30, so nothing was written, `hero.audio` is still `{}`, and steps 3
and 4 of the task (the Chromium check and Shawn's listening pass) cannot
happen yet. The body it sent back:

```
{"code":403,"error":"Forbidden",
 "more_info":"https://cloud.ibm.com/docs/watson?topic=watson-forbidden-error",
 "trace":"c8d0be4c-f414-49c1-85be-cc866ffbb8ce"}
```

**The 403 is not the format and not the length.** One five character request
was sent twice, once asking for WAV and once for MP3, and both came back 403
(traces `91c1e3a4-8494-4529-a3cd-38de6a27c518` and
`628c2cb9-316b-486e-a45c-11ee22a43347`). So the account refuses every
synthesis request, which rules out the MP3 Accept header this task added and
rules out the size of the run. What it does not establish is the reason: the
body carries none, nothing in this repo can read the usage counter, and the
credentials file is intact by name. That is Shawn's to look at in IBM Cloud,
and it is the next first action above.

**What IBM bills is now known, and it is none of the numbers printed before.**
Shawn checked IBM's documentation: SSML counts toward the character count and
whitespace does not. So a request costs its submitted length less its spaces,
which is `billed_characters` on `SpeechRequest` in `app/tts.py`, and it sits
between the two figures this repo had been printing. Every budget from here is
set on it. The three counts for the run, from `--plan`:

| Count | Characters | What it is |
| ----- | ---------: | ---------- |
| submitted | 2,070 | the text as sent, markup and spaces counted |
| billed | 1,818 | the price: markup counted, whitespace not |
| spoken | 1,530 | the words a listener hears |

The brief's ceiling was 2,000. On the submitted count the run was 70 over and
`--budget` refused it; on the billed count it is 182 under, which is why it
was sent. Five documents and docstrings that said IBM does not publish which
count it charges for now say what it charges for.

**Three recordings per match, and every one of them speaks the template.** No
model ran. The header is the orchestrator's, with no listener name in it,
through `openings` in `scripts/write_headers.py`; the narration is
`template_narration` in `app/narration_prompt.py`, the fallback assembled out
of the numbered facts, through `narration_for` in `scripts/tts_samples.py`.
The same words as the eight hero samples, in MP3 rather than WAV because
these are committed and served.

The 1986 text, 363 submitted and 318 billed, is the header

> Argentina extend the lead. Argentina 2, England 0. Here's how it happened.

and the narration

> Minute 54. Peter Beardsley was dribbled past. Terry Butcher was dribbled
> past. Terry Fenwick was dribbled past. Peter Shilton was dribbled past.
> Diego Armando Maradona shot and scored for Argentina.

The 2022 text, 327 submitted and 288 billed, is the header

> Argentina extend the lead. Argentina 2, France 0. Here's how it happened.

and the narration

> Minute 35. Lionel Andrés Messi Cuccittini passed. Julián Álvarez passed.
> Alexis Mac Allister passed. Ángel Fabián Di María Hernández shot and scored
> for Argentina.

Both carry the pronunciation markup on "lead" and on "minute", which is the
point of the listening pass: "Minute 54" and "Minute 35" are the first thing
each recording says after the header, and nobody has yet heard the `minute`
entry.

**The six files, for Shawn to listen to when they exist.** None of these is on
disk yet. Each is `app/web/assets/audio/<match_id>_<key>.mp3`, and the key is
the `hero.voice_for` value the browser looks up, so the name says which fan
hears it.

| File | Voice | Listener | Listen for |
| ---- | ----- | -------- | ---------- |
| `3750191_mate_scored.mp3` | Ethan, +10 rate, +10 pitch | with Argentina | "Minute 54" |
| `3750191_mate_conceded.mp3` | Ethan, -10 rate, 0 pitch | with England | "Minute 54", and that it is not cheerful |
| `3750191_storyteller_neutral.mp3` | Emma, 0 rate | no side | "Minute 54" |
| `3869685_mate_scored.mp3` | Ethan, +10 rate, +10 pitch | with Argentina | "Minute 35" |
| `3869685_mate_conceded.mp3` | Ethan, -10 rate, 0 pitch | with France | "Minute 35", and that it is not cheerful |
| `3869685_storyteller_neutral.mp3` | Emma, 0 rate | no side | "Minute 35" |

**The map is written from the files on disk, not from the plan.** A monthly
allowance can refuse a run part way through, so `scripts/tts_hero.py` writes
each file as its response arrives and `--map` then fills `hero.audio` with
whatever is actually there. A partial run therefore leaves a map pointing only
at real files, which is what
`tests/test_narration_player.py::TestTheAudioMap`
holds it to, once per match, and the listeners with no recording keep a disabled button rather
than a broken one.

**One hour lost to a refusal that looked like a silent crash, and it was
neither.** The first `--confirm` exited 1 with the last line on screen being
`sending 6 calls`, and the second, captured to a file, looked the same from
the tail. The error handler had worked both times: stderr is unbuffered and
redirected stdout is block-buffered, so the refusal was sitting at the *head*
of the captured file, above output printed before it. Read the whole file, or
redirect the two streams separately. A guess that it was an encoding fault in
the handler was wrong, and the comment it put in `scripts/tts_hero.py` has
been corrected; `sys.stderr` is reconfigured for UTF-8 there anyway, as a
guard on a body this one did not need.

**What is owed, and it is step 1 of the task over again.** Once the service
answers: run `--confirm`, commit the six files, commit `hero.audio`, drive all
three listeners on both matches in Chromium to see the timer and the waveform
move, and hand Shawn the table above. Nothing else in the task is outstanding.

`pytest -q` reports `680 passed` and all five gates pass.

### Phase 5, task 6: the narrations are the model's, and they are frozen

**Both goals were grounded on the first attempt, so the run cost 2 calls of
the 6 it was allowed.** `scripts/freeze_narrations.py --plan` printed the
count first: at most six generations, two goals at three attempts each, plus
one IAM exchange. `--confirm` on 2026-10-30 needed one attempt per goal,
`openai/gpt-oss-120b` through the chat endpoint at `reasoning_effort` low and
`max_new_tokens` 2000. No retry, no fallback, one IAM exchange. The 1986
narration passed on 33 claims and the 2022 one on 40.

That matches what Task 4b measured rather than being luck: 33 of 33 narrations
grounded on the first attempt is why this candidate is active.

**What is frozen, in `app/web/narrations.json`.** 1986:

> Peter Beardsley was dribbled past at 54:08. Terry Butcher was dribbled past
> at 54:13. Terry Fenwick was dribbled past at 54:15. Peter Shilton was
> dribbled past at 54:18. Diego Armando Maradona shot with his left foot from
> open play at 54:18.

2022:

> Nahuel Molina Lucero passed at 35:12. Alexis Mac Allister received the ball
> at 35:14. Ángel Fabián Di María Hernández received the ball at 35:22. Ángel
> Fabián Di María Hernández shot at 35:22.

Beside each: the tagged text the check passed, the facts it cited with the
`event_id` each was read from, which sentence cited which, and the verdict.

**The words are terser than the template's and carry more than it did.** The
model dropped "Minute 54." and put a clock on every sentence instead, and it
reached for `shot.body_part` and `play_pattern` on the 1986 goal: "with his
left foot from open play" is in the facts and the template never said it. The
2022 narration is four sentences where the buildup offers thirteen facts, and
it does not name Messi or Álvarez, who are in the card's quote. That is the
model's editing rather than a hole: a narration cites what it uses, and the
check reads what it cites.

**Neither narration says the goal went in,** and both are grounded anyway. The
check's ending rule is that the last sentence cites the goal's own shot fact,
which both do. The facts are built from one record each and a `Shot` record is
a shot; the goal is in the header above the narration, which says the score.

**The hero recordings now speak these words, and the price moved.**
`scripts/tts_hero.py` reads `app/web/narrations.json` instead of calling
`template_narration`, so what a judge hears and what a judge reads are one
text. From `--plan`:

| Count | Was | Now | What it is |
| ----- | --: | --: | ---------- |
| submitted | 2,070 | 2,268 | the text as sent, markup and spaces counted |
| billed | 1,818 | 1,959 | the price: markup counted, whitespace not |
| spoken | 1,530 | 1,746 | the words a listener hears |

**The run clears the 2,000 budget by 41 characters.** That is thin enough to
say out loud: one more pronunciation entry on a word either narration says
would push it over, and `--budget` would refuse the run. Raising it is a
decision, not a fix, so it is left at 2,000.

**Spoken is now below billed, where it used to be above it.** Nothing changed
in the counting. The frozen narrations carry more markup than the template
did, because the 2022 one says "Di" twice and each costs a `<phoneme>`
element, and markup is billed while the whitespace it displaces is not.

**The vocabulary sweep now reads the frozen narrations,** because those words
reach a voice and a model writes from a wider vocabulary than the template
does. It found four words nobody had reviewed and one of them is a real
heteronym.

**`di` is the fourth entry in the pronunciation table.** The dictionary lists
`D IY1` beside `D AY1`, and the second is the English "die" rather than an
accent on a Spanish name. The 2022 recording says it twice and the 2022 moment
card shows it, so it is `diː`. It is the second entry found by the dictionary
rather than by a listener, after `close`, and the first found on a word the
app speaks only because a model chose to write it: the template wrote the full
recorded name in one breath and never said "Di" on its own.

The other three went on `CHECKED_NO_ENTRY_NEEDED` with their reasons: `his`
and `with` are function words with full and reduced forms, and `allister` is
one name under the cot-caught vowel the voices merge.

**Two things nobody has heard, and they are not the two that were owed.**
`minute` is no longer in either hero recording: the model wrote clocks instead
of "Minute 54", so the entry is still unheard but the hero recordings are no
longer what would settle it. What they will settle instead is `di`, and a
question no entry covers: **the narrations now read clock values aloud**,
"at 54:08" and "at 35:22", and nothing here knows how an IBM Natural voice
reads a colon between two numbers. It is not vocabulary, since a digit is not
a word and no dictionary entry governs it, so no gate can flag it. It is the
first thing to listen for after November 1.

**The moment card shows the narration under the header** with the grounding
label beside it, and the quote block is kept: it does not conflict. Both
quotes name the same players in the same order as the facts their narration
cites, and the 2022 quote names two more.

**The card's one label moved rather than being duplicated.** It sat at the
foot of the card beside the quote. Two copies of the same promise on one card
reads as a defect rather than as a stronger guarantee, so the label is beside
the narration, which is the only text on the screen a test re-checks.
`NARRATION_FIELDS` in `scripts/scan_copy.py` gained `hero_narration`, which
the file itself says to do when Phase 5 adds a narration element.

**`scan_copy.py` caught two things worth it having caught.** It refuses the
grounding label in a copy file, because a data file carries no markup that
could place the label over anything, and both the `label` field in
`narrations.json` and a comment in `match-content.js` were hits. The data file
now records `"labelled": true`, the permission rather than the words, and the
label is spelled in `app/narration.py` and in the markup and nowhere else.

**Checked in Edge at 390px over a local server**, all three URLs reaching
`data-match-rendered`: the default and `?match=3750191` show the 1986
narration, `?match=3869685` shows the 2022 one, one label each, after the
narration and inside its card, no horizontal scroll.

**Not run, and still owed: the recordings.** The Text to Speech instance is
disabled above its Lite cap until November 1, so `scripts/tts_hero.py
--confirm` was not sent. Everything in front of it is ready and the price is
1,959 billed characters.

`pytest -q` reports `714 passed` and all five gates pass.

**One thing was already red before this task started.** `check_docs.py` exited
1 on `d0837ac`: that commit added `bob_sessions/phase5_task12_narrators.md`
and left it on `DELIBERATELY_ABSENT` in `scripts/check_docs.py`, so the gate
reported it as existing while listed as absent. The list is empty again
(`d1757b3`). The suite was `694 passed` and the other four gates were green.

## Data-check findings

Match `3750191`, Argentina 2-1 England, quarter-final, 1986-06-22. 2,748 events.

**Goals (3):**

| Player | Team | Minute | Second | Period | `shot.body_part.name` |
| ------ | ---- | -----: | -----: | -----: | --------------------- |
| Diego Armando Maradona | Argentina | 50 | 27 | 2 | `Other` |
| Diego Armando Maradona | Argentina | 54 | 18 | 2 | `Left Foot` |
| Gary Lineker | England | 80 | 37 | 2 | `Head` |

StatsBomb's `minute` floors the match clock, so `50:27` is the 51st minute as a
broadcast would caption it. The three goals reconcile with the `2-1` scoreline
in the match index, which is an independent file.

**Shots: 27 total. Argentina 15, England 12.**

**The 13-of-15 claim does not hold.** Both halves are wrong: Argentina took 15
shots, not 13, and the match total is 27, not 15. Argentina's share is 15/27
(55.6%). The likely origin of the error is that 15 is Argentina's real count,
read as the match total.

This matters downstream: any narration line that leans on shot dominance has to
use 15-of-27, and a line built on "13 of 15" could not carry
"Verified from play data".

## Screen scan results

`scripts/scan_copy.py` checks the four screens, `index.html` and
`app/web/matches.json` for basketball terms, verdict nicknames, "official", the
60-second framing, invented hardware, and em dashes. It also checks where the
grounding label sits, which is a placement rule rather than a banned string;
see below.

**Baseline, 4 hits:**

| File | Line | Category | String |
| ---- | ---: | -------- | ------ |
| `prelude_03_moment_card.html` | 26 | 60-second framing | `60 seconds` |
| `prelude_03_moment_card.html` | 165 | 60-second framing | `60-Second` |
| `prelude_04_moments.html` | 76 | verdict nickname | `Goal of the Century` |
| `prelude_04_moments.html` | 151 | verdict nickname | `Hand of God` |

**Current, 0 hits**, exit code 0. Screens 01 and 02 were clean at baseline: no
basketball terms, no "official", no UWB, haptic or dB, no "Controversy"
anywhere in the set. A separate census of every non-ASCII character found no em
or en dashes, only middle dots, one bullet, one curly apostrophe, and the quote
guillemets.

### The grounding label

`CLAUDE.md` allows "Verified from play data" only over narration whose claims
trace back to the event data. The label was on two screens. On the moment card
it sits beside the narration quote, which is the placement the rule describes.
On Live it sat on the standby pipeline card, above rows reporting whether the
step-away trigger and the narration were switched on. Those rows are app state,
not a claim read from the feed, so the label promised grounding for something
the data never said. **It has been removed from Live** and now sits only beside
the narration quote: "Verified from play data" (`03`).

A regex sweep cannot catch that, because the words were right and only the
position was wrong. `scripts/scan_copy.py` now parses each screen into a tree
and fails if the label does not share a card with a narration element, meaning
one carrying a `data-field` listed in `NARRATION_FIELDS`, currently
`hero_quote`. The walk stops at `html`, `body` and `main`, so a label anywhere
else on a screen that happens to hold narration does not pass. The label in
`app/web/matches.json` is a hit on sight, since copy data carries no markup that
could place it over anything.

Both directions were tested. Putting the label back on the standby card gives
exit 1 and `prelude_02_live_seated.html:89 [ungrounded label]`, reported as
sitting over "STANDBY PIPELINE"; adding it to a `matches.json` caption also
gives exit 1. With both reverted the scan is back to exit 0.

If Phase 5 adds another narration element, add its `data-field` to
`NARRATION_FIELDS` or a correct placement will be reported as a violation.

### Card bodies checked against the data

Two card bodies were tested against `shot.body_part.name`:

- **50:27 Maradona** records `Other`, with `technique: Normal`, `type: Open
  Play`, `xg: 0.379`, location `[110.8, 40.1]`. Nothing in the feed records an
  aerial duel, so "Maradona rises with Shilton and the ball is in" (`removed`)
  was not supported and was rewritten. The surrounding events do support a replacement:
  Peter Reid has both a `Clearance` and an `Error` at 50:26, then Maradona has
  `Ball Recovery`, `Carry` and `Shot` at 50:27. The body now reads "Maradona
  recovers Reid's error and scores from nine yards." (`04`) Nine yards is
  `120 - 110.8` on StatsBomb's 120-yard pitch. A trailing "the body part is
  recorded as Other" was cut in review as a data note rather than card copy.
- **80:37 Lineker** records `Head` at minute 80, so "England's late header sets
  up a tense finish" (`removed`) was supported on both counts and was left
  alone at the time. It came off the screen later, not because it was wrong
  but because 80:37 falls after the session clock, which sits at the 55th
  minute.

### Hero copy checked against possession 117

The solo goal line appeared on two screens and the narration quote on one. All
three were re-derived from `events/3750191.json` before editing (`10eb5a5`).

Possession 117 is the 54:18 goal. It holds four `Dribble` events, every one
with outcome `Complete`, each paired with a `Dribbled Past` event naming the
defender:

| Clock | Dribble location | Dribbled Past |
| ----- | ---------------- | ------------- |
| 54:08 | `[54.4, 56.4]` | Peter Beardsley |
| 54:13 | `[87.1, 68.6]` | Terry Butcher |
| 54:15 | `[97.1, 55.1]` | Terry Fenwick |
| 54:18 | `[112.8, 49.4]` | Peter Shilton |

Maradona's first touch of the move is a `Ball Receipt*` at `x = 55.2`. Halfway
is 60 on a 120-yard pitch, so the run starts inside his own half. The shot is at
`x = 113.4`, giving a span of 58.2 yards.

Three claims did not survive that:

- **"past five England players" (`removed`) was one too many.** Four are
  recorded as dribbled past. The likely fifth is Peter Reid, who has a
  `Pressure` event at 54:08 but no `Dribbled Past`, so the feed does not record
  him as beaten.
- **"60-yard" was a rounded figure.** The run spans 58.2 yards. The copy now
  says "from his own half", which is what `x = 55.2` supports.
- **"turns away from two, still going" (`removed`) has nothing behind it** in
  the feed and was cut.

The hero line on both screens now reads "Maradona's solo run from his own half,
past four England players" (`03`, `04`), and the quote names all four in
feed order: "«...Maradona, inside his own half, past Beardsley, past Butcher,
past Fenwick, rounds Shilton, and finishes.»" (`03`)

### Design tokens worth carrying forward

From `docs/DESIGN.md`, all verified against the markup:

- 29 of 47 colour tokens are declared but never referenced. The whole tertiary
  ramp and the whole error ramp are unused, so the screens define no error state.
- No responsive design exists: zero `sm:`, `md:`, `lg:`, `xl:` or `2xl:`
  utilities, and `screen-edge-tablet` is defined but never applied.
- Focus is defined only on the picker's text inputs. Every button has no focus
  style, and the toggle sets `focus:outline-none` with no replacement.

## Deviations

### Phase 1

- **`.gitkeep` files.** Git cannot track empty directories, so `app/`,
  `scripts/`, `tests/`, and `docs/` each got a `.gitkeep`. `data/raw/`
  deliberately did not, since it is ignored and a placeholder there would be
  ignored too. A fresh clone has no `data/raw/`; `fetch_statsbomb.py` creates it.
- **`competitions.json` was also downloaded.** Not in the task list, but
  resolving the 2022 season id without it would have meant hardcoding the id.
- **`.gitignore` carried a pre-existing uncommitted line.** `voice_test/` was
  already modified in the working tree before Phase 1 and rode along in
  `d11f686`, with its missing trailing newline fixed.
- **The CRLF normalization warning on `docs/data_check.md`** is resolved in
  `c52358c` and no longer occurs.

### Phase 2

- **The em dash removal covered already-committed docs.** The constraint arrived
  in Phase 2 and says "any doc", so the 20 existing em dashes in `CLAUDE.md`,
  `README.md` and `HANDOFF.md` were treated as violations and fixed, along with
  the prose `--` in the scripts and the generated report. This went beyond the
  four listed housekeeping items.
- **`scripts/scan_copy.py` was not requested.** The exit condition was a scan
  result, and a one-off grep is not evidence anyone else can reproduce, so the
  scan is a committed script that exits non-zero on a hit.
- **The screens were rendered during review, in Edge rather than Chrome.**
  Chrome is not installed on this machine; Edge is the same Blink engine, driven
  headless with `--screenshot`. Both credit rows were confirmed by eye: the
  reversed logo reads correctly as orange and white on the dark surface, beside
  "Powered by StatsBomb play-by-play data" on the picker and "Data: StatsBomb"
  on Moments. That render is what surfaced the credit truncation.
- **The moment-card timer was cleared in review** (`c7934d6`). The display and
  the 60-second cap in the script are both gone, and `#timerReadout` stays in
  place and empty for Phase 5. The moment card's play button was renamed from
  the generic `Play Narration` to `Play buildup narration` in `df6ca25`, so all
  four play buttons now say what they play.
- **A reported 390 px overflow was a measurement artifact, not a defect**
  (no code change). The first review screenshots used Edge headless with
  `--window-size=390`, which does not drive the layout viewport in this build:
  the page laid out at 492 CSS px and the screenshot captured a 390 px crop of
  it, so unclipped elements appeared clipped. Re-measured inside a 390 px
  iframe, every screen reports
  `clientWidth=390 scrollWidth=390 overflow=0px count=0`, and screenshots at a
  true 390 px viewport show the header pill, both primary buttons and the
  `PROFILE` nav label all intact on all four screens. The screens were never
  broken; the earlier handoff entry claiming they were has been removed.
- **`truncate` was dropped from the picker credit** (`c7934d6`). Rendering
  showed the logo squeezing the attribution to "play-by-play da...", which is
  not an intact credit. The text now wraps to two lines and reads in full. This
  changed an existing class rather than only copy.
- **Three claims in `DESIGN.md` were wrong on the first pass** and were
  corrected before commit by verification rather than shipped: the Material
  Symbol count, an omission in the unused spacing list, and a claim that
  `focus:outline-none` was the only focus utility. That last error also
  surfaced two components that had been missed entirely, the text input and the
  toggle switch, both now documented.
- **The four screens arrived mid-session as untracked files** that this session
  did not author. They were left untracked until the task that called for them.

## Settled decisions: the session model

These are decided, not open. Changing any of them changes what the app claims.

### The app is always live

No screen says "demo", "historical", "archive" or "replay". The app presents a
match in progress, and `scripts/scan_copy.py` keeps those words out of the
screens and `matches.json`.

### Two stages, then a single event

**Stage 1 is a list of today's events.** Both matches appear as pre-match
cards: teams, stadium, kickoff time and 0-0. Nothing from after kickoff is on
it, so no clock, no GPS badge and no date. Kickoff times are read from the
match index, 19:00 for 1986 and 17:00 for 2022, and `check_match_copy.py`
verifies them and the 0-0 against it.

**Stage 2 is one event for the session.** Confirming a card, or scanning a
ticket, fixes the match for the rest of the session; Live, the moment card and
Moments then show only that match. The match travels in the query string, for
example `?match=3869685`, and with none in the URL the default is 1986. Scan
ticket opens the scanner rather than the list, because a scanned ticket names
its own event. A
small "Change event" link on Live goes back to the list.

**"At venue, GPS" belongs to Live.** It appears only after selection, never on
the list. Both matches are at the venue with a seat; the seat is the fan's own
ticket, not a claim about the match, which is why it carries no data
obligation.

### One session clock

Each match has a `session_clock` sitting at its hero moment: the 55th minute
goal for 1986, Di Maria's for 2022. It is the single "now" for the session, and
no screen shows anything after it.

### Live has two states

| | Before heading out | After the moment |
| --- | --- | --- |
| 1986 | 2H 52', ARG 1-0 ENG (was 48', 0-0; Bob's Task 8) | 2H 55', ARG 2-0 ENG |
| 2022 | 1H 35', ARG 1-0 FRA | 1H 36', ARG 2-0 FRA |
| Prompt | READY FOR BUILDUP, HEADING OUT | BUILDUP READY, OPEN THE BUILDUP |

Heading out is what moves the clock: it marks the moment reached and opens the
moment card. Returning to Live keeps the advanced clock and score, and the
step-away prompt has become a way back into the buildup. The state lives in
`sessionStorage` keyed by match, so it survives navigation without riding in
the URL; blocked storage degrades to the pre-moment state rather than throwing.

Both scores are recomputed from the events rather than trusted: the after score
counts goals at or before the clock, the before score counts goals strictly
earlier.

### Moments stops at the clock

Moments lists only what has happened by the session clock, chronologically,
with the count following the list and the subtitle "Tonight so far".

| Match | Shown | Left off |
| ----- | ----- | -------- |
| 1986 | 2H 51', 2H 55' | Lineker's 81' |
| 2022 | 1H 23', 1H 36' | 2H 80', 2H 81', ET 108', ET 118' |

Chronological order is deliberate. Leading with the hero would rank one goal
above the others, and that is a verdict the app does not get to make.
`check_match_copy.py` fails if any entry falls after the clock.

### The repo is private, the site is not

`github.com/sh4wnbk/prelude` is private. GitHub Pages is still enabled and the
site is still public: `https://sh4wnbk.github.io/prelude/` serves 200 to an
unauthenticated request, and the Pages config reports `public: true`.

Two consequences worth knowing. Pages from a private repo is a paid-plan
feature, so losing that plan would take the site down without any commit
causing it. And the source is no longer browsable alongside the demo, so the
live URL is the only thing a reader can reach: anything the README promises as
evidence has to be runnable from a clone, not a GitHub link.

## Demo tickets

**The seats are settled.** 1986 is Sec 108, Row 14, Seat 8. 2022 is Sec 215,
Row 9, Seat 6. The 1986 seat was settled earlier; the 2022 seat had never been
set and was chosen when the ticket codes were generated, so it is the one value
here that no earlier decision produced.

These are demo fixture data, not play data. The seat is the fan's own ticket
rather than a claim about the match, which is why it carries no grounding
obligation; the same already applied to the section and row, neither of which
comes from `data/raw/`. This does not add a fourth input.

`app/web/matches.json` now carries `section`, `row` and `seat` per match as
separate fields, alongside the `ticket` line that Live renders. Live shows the
seat: "Sec 108 · Row 14 · Seat 8" (`02`). The "Ticket: " prefix came
off when a 414pt phone showed it wrapping to two lines: the icon beside it
already says what the line is.

**`scripts/make_tickets.py`** writes one QR code per match to
`app/web/assets/tickets/`, named for the match id. The payload is a URL,
`<site>/?ticket=<match_id>:<section>:<row>:<seat>`:

| File | Payload | Size |
| ---- | ------- | ---: |
| `app/web/assets/tickets/3750191.png` | `https://sh4wnbk.github.io/prelude/?ticket=3750191:108:14:8` | 444 bytes |
| `app/web/assets/tickets/3869685.png` | `https://sh4wnbk.github.io/prelude/?ticket=3869685:215:9:6` | 452 bytes |

**A URL, because a phone's own camera app only offers to open what it
recognises.** The codes used to carry a bare `prelude:...` string, which an
iPhone read back as text with nothing to do: "No usable data found". That made
the codes work only from inside Prelude's own scanner, pointed at another
screen, which is not what the README was promising. A https link opens the app
at that ticket from any camera app, with nothing to install and nothing to type.

`index.html` parses `?ticket=` and hands the seat to the ticket screen, which is
the screen that knows `app/web/matches.json` and so is the one that can say
whether the seat is a ticket this app holds. A link naming a seat we do not hold
is ignored rather than displayed, and `documentElement` carries
`data-ticket-link`, `accepted` or `rejected`, which is how a test can tell.

**The scanner reads both forms.** A code carrying the URL and a code carrying
the old `prelude:` string reduce to the same four fields before the same check
runs, so a code printed earlier keeps working.

The payload is built from the structured fields rather than parsed back out of
the display line, so the code and the copy cannot drift. The script refuses to
write anything if they disagree, or if any part of the payload is missing from
the data, and both refusals were tested.

Writing an image proves nothing about what it holds, so each PNG is read back
with a real decoder (`zxing-cpp`) and compared byte for byte; a code that does
not round trip exits non-zero. Both decode exactly. Generation uses `segno`, now
a project dependency; the decoder and `pillow` are dev dependencies.

**The scanner reads these codes**, and the next section records how. The
payload format is a contract between `scripts/make_tickets.py` and
`app/web/prelude_05_scan.html`, and both read the seat fields from
`app/web/matches.json`, so neither can drift from the other.

## Ticket scanning

`app/web/prelude_05_scan.html` reads the QR code on a demo ticket and opens the
ticket details for that match. Scan ticket on the list opens the scanner, and
the code decides the match, so the card selected on the list no longer rides
along with the button. Built from the Stitch scan mockup's layout and
viewfinder.

**Two readers, one handler.** `BarcodeDetector` where the browser has it, and
jsQR pinned at `1.4.0` from jsDelivr with an integrity hash where it does not,
because iPhone Safari has no `BarcodeDetector`. A detector that fails part way
through falls back to jsQR for the rest of the session rather than failing every
frame. `documentElement` carries `data-reader`, which is how a test can tell
which one ran.

**A code is a ticket only when the whole payload matches** one in
`app/web/matches.json`: match id, section, row and seat. Those two tickets are
the only ones this app knows about, so anything else is not a ticket it can
open. An unrecognized code shows "Ticket not recognized" and the scanner keeps
running, because the next frame may hold a code it does know.

**Reading a code does not start the match.** The seat travels to the ticket
screen, and Enter match there is what clears that match's `sessionStorage` key
and leaves the other match's alone. Backing out of the ticket screen therefore
changes nothing.

**With no camera to use**, the viewfinder is replaced by a plain message and the
manual entry button stays. That covers permission denied, no camera found, and a
camera that will not start, each with its own message. Manual entry takes the
same ticket code and refuses anything else the same way.

**The shell states the camera grant, and does not depend on it.**
`index.html` holds every screen in an iframe, and that iframe now carries
`allow="camera"`. It is not what makes the scanner work there: Permissions
Policy defaults the camera to `self`, so a same-origin frame inherits it. That
was measured rather than assumed, by serving the shell with the attribute
stripped out and scanning a ticket anyway, which worked. The attribute stays
because it says the grant out loud, and because it is what a cross-origin shell
would need.

**Stripped from the mockup**, as the task required: the FPS, FOV, zoom and ISO
readouts, the parity and locking-on lines, auto-detect active, the torch button,
the format chips including Apple Wallet, and the StatsBomb verifies footer. Three
more came out for the same reason the list exists. The stylised QR target inside
the viewfinder was a drawing of what a camera would show, and the viewfinder now
shows a camera. The "view scan instructions" link went nowhere. The optical HUD
and active verification wording described machinery that is not there: the screen
reads a code, and the status pill now reports what the camera is actually doing.

**Manual entry on the picker is built.** The free-text matchup and venue input
is gone. The match comes from a select built from `app/web/matches.json`, the
stadium fills in from the chosen match rather than being typed, and the section,
row and seat are the only things a fan enters. Continue stays disabled until a
match is picked and all three fields hold something that is not whitespace, and
it opens the ticket details screen, the same one a scan opens.

**A seat entered by hand is that fan's own ticket**, so it overrides the one in
`matches.json` for that match for the rest of the session. It lives in
`sessionStorage` as JSON under `prelude.ticket.<match_id>`, next to
`prelude.moment.<match_id>`, and `match-content.js` prefers it when it renders
the Live ticket line. A seat typed for one match does not appear on the other,
and a new session falls back to the seat in `matches.json`.

**There is one manual entry, and both screens mount it.** This was an open
question and it is now settled: the scanner used to ask for a ticket code, which
meant typing `prelude:3750191:108:14:8`, a string printed nowhere a fan can
read. Asking for it was a worse failure than no fallback at all, because it
looked like a way in. Both screens now show the same form, built once in
`app/web/manual-entry.js` and put on a screen with `Prelude.mountManualEntry`.
The ticket code field is gone.

The form is script rather than markup precisely so there is one copy of it.
`docs/DESIGN.md` cites it as `js`, and `scripts/check_docs.py` treats that as a
source it can verify anchors in, the way it does a screen. `scripts/scan_copy.py`
reads the scripts as well now, because copy is screen copy wherever it is
written.

What the camera path and the form path check is still different, and that is the
point rather than an inconsistency. A scanned code must match a ticket this app
knows, because a code either decodes to one or it does not. A typed seat is
accepted as given, because where someone is sitting is theirs to state and
carries no data obligation. The copy
above Scan ticket now reads "Reads the QR code on your ticket and opens that
match." (`01`). The old line promised to set a venue and a section from a
ticket, which was never true of the button and is still not what it does: it
opens the scanner, and the code names the match.

## Ticket details

`app/web/prelude_06_ticket.html` is where both ways in arrive, and the only
place the match is actually entered. Built from the Stitch ticket mockup. The
match comes from `app/web/matches.json`; the seat comes from whatever put it in
`sessionStorage`, the scanner or manual entry. Opened with no stored seat, a
reload after the session ended or a bookmark, it falls back to the seat
`matches.json` holds for that match, which is the inline copy already in the
markup.

**Enter match** clears that match's step-away key and opens Live at its
pre-moment state, with the ticket's seat on it. **Scan different ticket** goes
back to the scanner. **Edit details** appears only for a ticket entered by hand,
and returns to the list with the manual panel open and the seat still in it, so
correcting one field is not a retype. The pill says how the ticket arrived,
"Ticket scanned" or "Entered by hand", which is the only thing it claims.

**Three rows, each describing something real**: at venue with GPS, naming the
stadium; play data connected, which is the picker's own status string; and
"Tap Heading out when you leave your seat.", which is an instruction rather than
a claim about machinery.

**Removed from the mockup**, as the task required: the year and the date
everywhere, the telemetry lock line, "Step-away tracking armed", and the
Stitch-hosted stadium image. The pass ID went with them, because `#AZT-86-108`
carries the year and nothing issues pass IDs, so a year-free version would be an
invented identifier. Four more came out for the same reason the rule exists.
"Lower bowl", "aisle adj" and "reserved" are claims about a seat that no data
makes. The gate and concourse strip invents a way into a stadium. The torch
button has nothing to toggle on a screen with no camera, and was already struck
from the scanner. The vibrate call on the primary button was invented hardware
feedback. "Ticket verified, match locked" became the arrival pill, since nothing
is verified about a seat someone typed.

## Published

The site is deployed from `main` by `.github/workflows/pages.yml`, which stamps
the commit into every `__V__` placeholder and uploads `app/web/` only.

**The camera needs the live site, not a file.** `getUserMedia` is refused
outside a secure context, so the scanner works on
`https://sh4wnbk.github.io/prelude/` and on `localhost`, and not from a screen
opened off the filesystem. The README carries both ticket QR codes so a phone
can scan one off the page.

**Verified on the live site at `a836eb7`**, entering through `index.html` the
way a visitor does, in a browser emulating a phone: both matches scan to their
own ticket and open Live with the scanned seat, and both reach the same place
through manual entry with a typed seat. The reader reported itself as jsQR,
which is the path an iPhone takes. What that run cannot prove is a real iOS
Safari camera prompt on a physical handset.

**A phone may refuse to autoplay the camera** even once it is granted. That is a
separate failure from having no camera, so the scanner keeps them apart: a
refused `play()` shows a Tap to start the camera button rather than the no
camera message, and scanning begins on that tap.

## Readable type, and the reader can zoom

Reported from an iPhone XR: the smallest text read as fine print, and nothing
the reader could do got round it. Both halves are fixed.

**The label scale moved from 9/11/13 to 13/14/16.** 12/13/15 was the first
attempt and came back as still tight on the XR, so these sizes are the second
reading rather than the first. `label-sm` carried 66 of the
uses across the screens and `manual-entry.js`, so it is the one that mattered,
but all three moved together: the order of the scale and the gaps in it are
unchanged, and leaving `label-lg` at 13px would have put `label-md` level with
it. It is one edit repeated identically in six screens, because the
`<script id="tailwind-config">` block is one block and the design system rests
on it staying byte-identical. It still is, now sha256 `44927b9a0feedea2`,
3210 chars.

**`user-scalable=no` and `maximum-scale=1.0` are gone** from all six screens and
from `index.html`, which is the page a phone loads first. Both had to go: either
one alone still blocks pinch to zoom on iOS.

**The manual entry fields are 16px**, the one literal type size in the system.
iOS zooms the page when a field under 16px takes focus, and it could not do that
while zooming was blocked. Unblocking zoom brings that behaviour back, so the
fields sit at the threshold where it never fires. Without this the fix would
have traded fine print for a page that lurches every time a seat is typed.

**One thing the bigger type broke, and it is fixed.** The narration label on
Moments, "AI AUDIO NARRATION · PLAY DATA SYNC", is in a span that truncates, and
at 12px it no longer fitted on one line, so it rendered as
"AI AUDIO NARRATION · PLAY DATA…". The truncation is gone from those two spans
and the line wraps instead, which shows all of it. Nothing else lost content:
the verified marker, the Live ticket line and the seat tiles all still read in
full.

Measured on every screen at 390px and at 414px, the XR's width: document
scrollWidth equal to clientWidth, `window.scrollTo(9999, 0)` leaving scrollX at
0, no unclipped element past the body box, and no leaf element whose own text is
wider than its box. The behaviour suites were re-run unchanged.

**What the measurements cannot settle.** Nothing overflows and the computed
sizes are 13, 14, 16 and 16px, but whether that reads comfortably in the hand is
not something a desktop browser at 414px can answer. It took two readings on a
real XR to get here, which is the useful part of the record: the first fix
measured completely clean and was still wrong.

At these sizes several lines that used to sit on one now wrap: the two status
pills on Live, its ticket line, and the status line on the event cards. Nothing
is hidden or clipped, and that was checked rather than assumed, by looking for
any leaf element whose own text is wider than its box. Wrapping is the cost of
the larger type and it was taken deliberately.

## Stadium backdrop on desktop

Above the 501px breakpoint the page sits on `app/web/assets/stadium-bg.jpg`,
blurred and dimmed, so a desktop window reads as a phone held at a match rather
than a phone on a flat field. At 500px and narrower nothing applies: the screens
are pixel for pixel what they were, which was checked by comparing screenshots
with and without the rules rather than by eye.

**The frame is drawn in two places and both needed it.** `phone-frame.css`
serves a screen opened on its own; `app/web/index.html` carries its own copy and
does not link the stylesheet, and the site root serves `index.html`. A backdrop
written only in the stylesheet would have been invisible to everyone visiting
the demo.

**What nearly went wrong.** With the rules in place, the computed styles were
all correct, the image was `cover` and centred, the blur was 8px, the overlay
was 70%, and the page still rendered flat black. Measuring the rendered pixels
rather than the stylesheet showed the backdrop sitting at a luminance of exactly
19, which is `#101319`: the shell's `body` fills the viewport and the base layer
paints it that colour, so it covered the backdrop on `html`. The fix is one
line, `background-color: transparent` on `body` above the breakpoint. The trap
worth remembering is that an opacity sweep looked like the obvious remedy and
would have made the page lighter without ever revealing the photograph.

The image is a match night seen from behind one goal: four floodlight towers, a
full crowd, players on the pitch. Mean luminance 49.5 of 255, with 44% of its
pixels below 32 and 1% above 192, which is the lights. It replaced a darker and
emptier stadium that needed a 70% dim to sit behind the phone; this one carries
the crowd and the lights that make it read as a match, and takes 50%.

The phone stays the brightest thing on screen, but only peak brightness shows
it: 227 for its amber button against 131 for the brightest floodlight, at every
width. Do not use the mean. The two are close enough at 1920 and 2560 that the
answer flips with the crop: measured over the phone's screen area the phone led
45.6 to 45.2, and measured over the whole handset including its bezel it trailed
41.6 to 42.3. Both numbers are real and neither means anything, which is the
point. The phone is a dark panel with bright accents on a blurred page, so what
makes it read is peak contrast and sharpness, not average light.

It is 122KB: 1920px wide, JPEG quality 75, the same treatment the previous
backdrop got. A photograph that is blurred 8px and dimmed to half can take far
more compression than it looks like it should, and phones never pay for it at
all: the media query means they do not request it, measured as zero requests at
390px against one at 1920px.

## Verifying the app in a browser

Phase 2 verified the screens by rendering them. A click through needs more than
that, and none of what follows is derivable from the screens or from the rest of
this file, so it is recorded rather than worked out again.

### Serve it, do not open the files

`match-content.js` fetches `app/web/matches.json`, so a screen opened straight
off the filesystem fails that fetch and falls back to the inline 1986 copy. The
fallback is deliberate and quiet, which means a filesystem run looks like a
working app while confirming almost nothing. Serve the directory instead, from
`app/web/`:

    ..\..\.venv-prelude\Scripts\python.exe -I -m http.server 8099 --bind 127.0.0.1

The `?v=__V__` placeholder stays literal when the app is served this way, since
CI substitutes it only on deploy. The server ignores query strings, so every
asset still resolves.

**`data-match-rendered` on `documentElement` is the signal** that a screen
rendered from `matches.json` rather than falling back to the inline copy. Wait
for it before reading any value, or an assertion can quietly pass against the
1986 markup while claiming to check 2022.

**The step-away state is `sessionStorage` under `prelude.moment.<match_id>`,
set to `"1"`.** Seeding or clearing that key is how a session carrying old state
is reproduced. It is per tab, so it has to be set on the origin and then
navigated within the same tab.

### Driving it

No browser automation is installed. `.venv-prelude` holds the test runner and
its dependencies only, and putting a driver there would add browser packages to
the venv that runs the gates. Chrome is still absent on this machine. Edge is at
`C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`.

Playwright drives that Edge with `channel="msedge"` and needs no browser
download, so a scratch venv outside the repo is enough. It sets the layout
viewport through the DevTools protocol, which is the thing `--window-size`
failed to do in the Phase 2 review.

### Two measurements that look like defects and are not

Both produced a false failure before being run down, and both will recur:

- **Decorative glows read as horizontal overflow.** Each card carries an
  absolutely positioned blur placed outside its own box, and the card clips it
  with `overflow-x: hidden`. `getBoundingClientRect()` reports the unclipped
  geometry, so a naive sweep flags it every time. The claim that matters is
  whether the document scrolls at all: at 390 px and at 900 px the screens
  report `scrollWidth` equal to `clientWidth`, and `window.scrollTo(9999, 0)`
  leaves `scrollX` at 0.
- **The framed body measures 422 px, not 390.** Above the 501 px breakpoint
  `phone-frame.css` sets `box-sizing: content-box` with a 16 px bezel, so the
  border box is 390 plus 32 while the screen area is exactly 390. Read
  `body.clientWidth`, not the bounding rect.

Two further non-defects: the browser requests `/favicon.ico` on its own and
gets a 404, which nothing in the app references; and the Moments filter row
clips its last chip at 390 px because that row is `overflow-x: auto` and
scrolls.

### Driving the scanner

A camera cannot be clicked, so the scan screen is verified by giving Chromium a
fake capture device whose frames are a clip of a ticket code. A QR image becomes
a `.y4m` clip, and Edge is launched with `--use-fake-device-for-media-stream`
and `--use-file-for-fake-video-capture`, which is a ticket held up to the lens
as far as the page can tell.

Two things this machine cannot show you. Edge on Windows ships no usable
`BarcodeDetector`, so the real browser always takes the jsQR path here: that
branch is covered by substituting a stub detector, one that works and one that
fails, which exercises the integration rather than a native decoder. And a
denied camera is simulated by making `getUserMedia` reject with the error name
the browser would use, since a headless run cannot refuse a permission prompt by
hand.

### Test values are literals, not derived from each other

A run once reported that manual entry was given Section 332 and the ticket
showed 3320, and the same row for the other match read 118 going in and 1180
coming out. Nothing in the app was wrong. The harness built that row's section
by appending a character to the section used in the row above it, so it really
did type 3320, and the check really did pass.

The defect was in what the report let a reader conclude. Two numbers that
disagree on their face, printed side by side and marked as passing, are
indistinguishable from the form corrupting what it is given, and nothing in the
line said which it was. Derived test data costs more than it saves.

Every seat a check types is now a literal written next to the check, the paths
that should agree use the same literal, and the assertion covers the whole way
through: what the inputs hold when Continue is pressed, what ticket details
renders, and what Live renders. The seat is carried as a string from the input
to `sessionStorage` to the screen, with no parsing or arithmetic anywhere on
that path, which is why it cannot gain a digit.

Measured for both matches, with the same input through all three ways in:

| Input | Picker form | Scanner form | Ticket link |
| ----- | ----------- | ------------ | ----------- |
| 1986, Sec 108 Row 14 Seat 8 | 108/14/8 | 108/14/8 | 108/14/8 |
| 2022, Sec 215 Row 9 Seat 6 | 215/9/6 | 215/9/6 | 215/9/6 |

A typed seat of 332/7/21 for 1986 and 118/2/9 for 2022 comes through both forms
unchanged and produces the same Live ticket line either way. A link carries only
a seat this app holds, so the shared input the three paths can all take is the
seat on the ticket itself.

### What the click through confirmed

Both matches were driven end to end in Edge, in a session with no saved state
and again in one carrying saved state for both matches. The event list, the Live
states before and after Heading out, Moments stopping at the session clock,
Change event, and Heading out returning after a switch all behave as the settled
decisions above describe, at 390 px and at 900 px. The per-match reset holds in
both directions, and picking one match leaves the other match's key untouched.

## Plan

Tasks 3d through Phase 7, as agreed with Shawn, copied here so a fresh session
has the whole arc rather than one task at a time.

**Everything in this section is planned work except where a task is marked
done.** Tasks 3d, 4a, 4b, 4c, 5, 6a, 6b and 6c are built, and so are Bob's task
4 and task 5 and the follow-up after it; nothing below them exists. Paths a doc
names before they are written go on `DELIBERATELY_ABSENT` in
`scripts/check_docs.py`, so the docs gate fails if one appears and this section
was not updated with it. That list is empty now:
`bob_sessions/phase4_task5_header.md` came off it when Bob's session was run
and the export was committed.

Shawn is asked whether to continue at the end of each task, after the exit
commands have run, because an adjustment may be wanted before the next one
starts.

### Task 3d: past tense, no closer, end on the goal (done, `aff2dfd`)

Update `docs/VOICE.md`: the buildup is told in the past tense, as playback of
what already happened. No closer: the narration ends on its sentence about the
goal, because the stadium takes over and the app gets out of the way. The
opening line is "Here's the buildup." for now (the orchestrator replaces it in
Task 5).

Write the numbered facts in the past tense ("Terry Butcher (England) was
dribbled past, 54:13") and require past-tense narration in the prompt.

Update the grounding check's action words to past-tense forms (dribbled, shot,
scored, pressed, recovered, won a foul). Keep "won a foul" allowed and outcome
claims like "won the match" banned, and test both.

The final sentence must cite the goal's shot fact, with nothing after it. Test
that a narration ending elsewhere is refused.

Add tests: a true past-tense sentence passes; the Beardsley, Reid and Butcher
line still fails in the past tense; a present-tense buildup sentence is flagged.

Exit when: all tests and gates pass, a live run on `granite4:micro` over the
1986 54:18 goal produces past-tense narration that passes, and the work is
pushed.

### Task 4a: comparison script (Ollama only) (done)

Write a script that narrates all 9 goals, 3 runs each, and records per
narration: the first-attempt grounding pass rate, coverage (the share of key
facts cited: the shot, every dribble past an opponent, and the foul for a
penalty), tokens and time.

Build and debug it on `granite4:micro` only. No watsonx calls.

Write the results to `docs/narration_eval.md`, marked clearly as
development-model results.

Exit when: the script runs end to end on Ollama, the report shows pass rate and
coverage per goal, and the work is pushed.

### Task 4c: ask for the key beats (done)

Added after Task 4a measured the gap it is about. Mark the key beats in the
prompt (the list already lives in `app/narration_prompt.py`) and tell the model
each one needs its own sentence before the goal sentence.

Leave the grounding check unchanged. Coverage is still reported, not enforced.

Rerun only the five multi-beat goals, 3 runs each, and add the results to
`docs/narration_eval.md` next to the 4a numbers, so the before and after can be
compared.

Exit when: the comparison is in the report, the pass rate is shown beside
coverage (so a gain in one that costs the other would be visible), tests and
gates pass, and the work is pushed.

### Task 5: orchestrator contract and failing tests (done)

Write `app/orchestrator_contract.py` (contract only, no logic), declaring the
orchestrator's inputs: the event (kickoff time, teams, sport), the moment
(which side scored, game clock, score after it, regulation length), and the
listener (allegiance: team A, team B or neutral). Outputs: the greeting word
("today" or "tonight"), the header line, and the default persona.

The rules to encode in tests:

- "tonight" when kickoff is at or after a cutoff set in config (start at
  17:00), otherwise "today";
- game phase as a share of regulation time (early is the first third, late is
  the final quarter), so it works for any sport;
- score state after the moment (ahead, level or behind, for the listener's
  side);
- the header comes from a fixed table by allegiance, scored or conceded, and
  phase (Shawn's final wording goes in `docs/VOICE.md`; start with: scored =
  "Great start." / "Good news." / "Your side again.", conceded = "Still early."
  / "There's still time." / no prefix, neutral = no prefix, each followed by
  "Here's how it happened." or, for neutral, "Here's the buildup.");
- "There's still time" only appears when the phase isn't late;
- default persona: fans get the Mate, neutral listeners get the Storyteller.

Write the failing tests in `tests/test_orchestrator.py`, covering both demo
matches plus one made-up non-football case (to prove it is sport-agnostic). Add
a "Task 4: the orchestrator" section to `docs/bob_brief.md`.

Exit when: the new tests fail only because the orchestrator isn't implemented,
everything else passes, and the work is pushed. Stop; Shawn runs Bob.

**Bob, task 4 (done, `1c4063a`):** implemented the orchestrator and fixed the
period gap in `buildup`. See "Phase 4, Bob task 4" under What was built.

### Task 6: personas

Three tasks, committed one at a time, because the config, the prompt change
and the measured run fail in different ways and a single commit would not say
which.

#### Task 6a: the persona config (done)

Three personas in a committed config file, each with an id matching the
contract, a name, a one-line description for the Profile screen, a writing
style for the prompt, a fans-only flag and an IBM voice to be confirmed: the
Caller (classic play-by-play energy), the Storyteller (calm documentary
narrator), and the Mate (partisan, like a friend in your row; offered only to
fans). Inspired by styles, never named after real broadcasters. Tests for the
config's shape. See "Phase 4, task 6a" under What was built.

#### Task 6b: the style into the prompt, and the Mate's partisanship (done)

Feed the persona's style text into `build_prompt`. The grounding check and the
banned list apply unchanged to every persona.

For the Mate only, pass the listener's side into the prompt and admit "we",
"our" and "us" in the grounding check, refusing any sentence using them whose
cited facts are not about the listener's team. "You" and "your" stay banned
for every persona.

Exit when: tests and all four gates pass, the docs are updated, and the work
is pushed.

#### Task 6c: the comparison on Ollama (done)

Extend `scripts/narration_eval.py` to run each persona, the Mate once with
each side as the listener's team. Run it on `granite4:micro` over the 1986
54:18 goal and the 2022 79:24 and 22:24 penalties, three runs each. Only
model-written narration counts as a pass; a template fallback is a failure.

Exit when: every persona passes on 54:18 and 79:24, the 22:24 numbers are
reported whatever they are, the report shows the first-attempt and
after-retry pass rates with coverage per persona and per goal, and the work is
pushed.

### Task 1 after 6d: one narration style, the personas separated by sound (done)

Shawn's decision on the three measured runs. The per-persona style text and
the worked examples come out of the prompt and out of `app/personas.py`; the
narration text is one style for every persona, which is the Storyteller's. The
Mate's "we" comes out of the prompt and the rule stays in `app/grounding.py`
as a guard. `Persona` carries what Phase 5 needs instead: a voice, a rate, a
pitch and two sentence breaks, all unconfirmed. The 6c, 4b and 6d results stay
in `docs/narration_eval.md`, labelled as runs of code since removed.

Exit when: tests and all four gates pass, and the work is pushed. See "Phase
4, after task 6d" under What was built.

### Task 2 after 6d: the game-focused header, contract and failing tests (done)

For Bob's task 5. `ScoringMoment` gains the score before the moment,
explicitly rather than by subtracting one, because a score can move by any
number of points. A transition is classified from the scoring side's view out
of the before and the after alone (take the lead, overtake, extend, close the
gap, draw level), with no transition depending on earlier history. A wording
table keyed by that transition replaces the outcome-by-phase prefixes, the
header is the same line for every listener, and allegiance picks the persona
instead of changing the header.

Exit when: the new tests fail only because Bob has not built them, everything
else passes, the docs gate accounts for the red tests, and the work is pushed.
See "Phase 4, task 2 after 6d" under What was built.

### Bob task 5: the game-focused header (done, `7f1b21e`)

Bob implemented `transition` and `header` in `app/orchestrator.py` and pointed
`PreludeOrchestrator.opening` at the new `header`. See "Phase 4, Bob task 5"
under What was built.

### The follow-up after Bob task 5: the old header comes out (done)

`HEADER_PREFIXES`, `FAN_TAIL` and `NEUTRAL_TAIL` are out of
`app/orchestrator_contract.py`, and `bob_sessions/phase4_task5_header.md` is
off `DELIBERATELY_ABSENT`. See "Phase 4, the follow-up after Bob task 5" under
What was built.

### Task 7: the card, the name and the Profile screen

Build the "Who are you with tonight?" card (or "today?", from the orchestrator)
from the existing design tokens in `docs/DESIGN.md`. It shows the two teams plus
"Just here for the game", and an optional "What should we call you?" field. It
appears after the fan confirms an event or enters through a ticket.

**The header is the game-focused line and it is the same for every listener.**
The answer to "Who are you with" picks the persona, through `default_persona`,
and it does not change a word of the header. That is settled and built: see the
header section in `docs/VOICE.md`.

Store the answers on the phone only. The name is never sent to a model or a
server, and it is added to the header on the phone, after the narration has
been generated.

Turn on the Profile tab: the three persona cards with their descriptions, the
current pick, and a way to change allegiance and name.

Show the orchestrator's header at the top of the moment card.

Exit when: the full flow works on both matches in a real browser, at 390px and
on desktop, all gates pass, and the work is deployed and pushed.

### Task 4b: the paid comparison (watsonx, once) (done)

Before running, state how many watsonx calls it will make: 2 models by 3
personas by the chosen goals by runs. Keep it to the hero moments if the count
is high.

**Run one candidate without the beats block as well, on the five multi-beat
goals only, so the extra calls stay small.** Task 4c added the block because
`granite4:micro` would not reach the beats without it, and that is a statement
about a 3B model rather than about every model. A candidate that covers the
beats unprompted does not need the block, and the block costs sentences and
therefore costs grounding: on the 22:24 penalty it cost `granite4:micro` every
first attempt. `build_prompt` takes `Facts`, so the no-block arm is a prompt
built with the block suppressed and nothing else changed, and
`scripts/narration_eval.py --compare` already renders a before and after.

Run it, add the results to `docs/narration_eval.md`, and save sample narrations
for Shawn to read.

Exit when: the report compares both models by pass rate, coverage, cost and
speed, per persona; this file records which leads; and Shawn picks the model.

### Phase 5: voice and audio

**This is where the personas are, now that the narration text is one text.**
Each persona becomes an IBM voice plus SSML prosody: a rate, a pitch, and the
breaks between sentences. The five fields are on `Persona` in
`app/personas.py`, all `None`, with `voice_confirmed` and `prosody_confirmed`
false beside them.

The rules Shawn settled for them, before any of it is built:

- **Comprehension comes first.** The narration is names, actions and clocks,
  and a listener who misses one has missed the thing the app is for.
- **The Caller's energy is emphasis and pitch**, with a rate only modestly
  above the Storyteller's and a ceiling on it. The Storyteller's rate is what
  the other two are set against.
- **Breaks let each beat land**, with a slightly longer break before the goal
  sentence.
- **The rates are set by ear**, by Shawn, in this phase. Words per minute is
  then measured from the real audio rather than assumed, and the measured
  ceiling goes into config.

- Shawn: audition the voices (the PowerShell command from earlier) and assign
  one IBM voice per persona, then set each one's rate, pitch and the two
  breaks by ear. Test how the voice says the film character's name.
- Claude Code: build the IBM Text to Speech backend against IBM's published API
  (credentials from the file outside the repo), taking the voice and the
  prosody from `app/personas.py` and emitting the breaks as SSML.
- Claude Code: measure words per minute from the generated audio, report it,
  and put the ceiling in config once Shawn has agreed it.
- Claude Code: add audio playback to the moment card (play, waveform, "Verified
  from play data" shown only for narration that passed).
- Claude Code: save audio for the hero moments only (1986 54:18 and the 2022 Di
  Maria goal, by 3 personas, about 3,600 characters), staying inside the 10,000
  free characters a month, and say the character count before generating.

### Phase 6: hosting and Orchestrate

- Claude Code: a small hosted backend (Render, as planned) holding the IBM keys,
  with rate limiting, so judges get live, varied narration; the saved audio is
  the fallback if it is down.
- Bob: write the OpenAPI tool spec for the narration endpoint (the YAML the lab
  guide's exercise uses).
- Shawn: recreate the prelude agent in Orchestrate and import the spec as its
  tool. Optionally host the orchestrator's routing there.
- Claude Code: check the spec against the live endpoint, add a keepalive so a
  judge never hits a cold start, and finish `docs/IBM_STACK.md`.

### Phase 7: film and submission

- Shawn: record the real app for the split screen (her on the left, the moment
  card playing her named header and narration on the right, then the right half
  drops away into the sunlight shot). Use the app's real audio.
- Claude Code: fill the README's empty sections and the
  judging-criteria-to-evidence table, each row backed by something runnable.
- Shawn: finish the deck and the video. Claude Code: a final recon from a fresh
  session (all gates, both matches, a real-phone check).
- Shawn: export Bobalytics from User scope, weekends included, over the full
  lab period, once at the end of the build. Claude Code scans it and commits it
  to `bob_sessions/`.
- Shawn: make the repo public, check `bob_sessions/` is complete, and submit.

## Next first action (Bob task 13, then the recordings on November 1)

**Bob task 13 in `docs/bob_brief.md` renames the persona id from `mate` to
`buddy`**, Shawn's call on 2026-10-30, made before the hero recordings exist
because their filenames are built from the id. Live code, data and tests
change; the past does not: `scripts/narration_eval.py`, `docs/narration_eval.md`,
this file's history and `bob_sessions/` keep "Mate" for the runs made under that
name. The docs that describe the current state are the follow-up's.
`pytest -q` reports `4 failed, 714 passed`. Every failure is in
`tests/test_buddy_rename.py`, whose last test lists each live line still to
rename.

**The rename comes first, and the recordings after it.** `scripts/tts_hero.py`
names each file `<match_id>_<key>.mp3` from `hero.voice_for`, so the six
recordings are `mate_scored` and `mate_conceded` today and `buddy_scored` and
`buddy_conceded` once Task 13 lands. Recording before the rename would mean
paying for the audio twice or renaming files the map is written from, and the
Lite allowance is monthly.

**Claude Code Task 6 is done and the words are settled.** The narrations are
the model's, frozen in `app/web/narrations.json`, shown on the moment card and
read by `scripts/tts_hero.py`. See "Phase 5, task 6" above for the run, both
texts and the new price. The rename does not touch them: a narration is one
text for every voice, and the id appears nowhere in it.

**Then one command, and it cannot run before November 1.** The Text to Speech
instance is disabled above its Lite cap until the month turns:

```
.\.venv-prelude\Scripts\python.exe -I scripts	ts_hero.py --confirm
```

It costs 1,959 billed characters against a `--budget` of 2,000. Then commit
the six MP3s and the `hero.audio` map, drive all three listeners on both
matches to see the timer and the waveform move, and hand Shawn the file table
in "Phase 5, task 5", with its keys renamed.

**What to listen for has changed.** `minute` is no longer in either recording,
because the model wrote clocks rather than "Minute 54". The two new things are
`di` in "Di María", which has an entry nobody has heard, and the clock values
themselves: the narrations say "at 54:08" and "at 35:22", and nothing here
knows how a Natural voice reads a colon between two numbers. No gate can flag
that, because a digit is not a word.

### Before Task 13

**Bob task 12 is built and checked.** `35c91b6` made the four changes in the
brief. In Chromium, Profile marked The Buddy for an England fan and The
Storyteller for a neutral listener, showed the coming-soon note on tapping The
Caller, and showed Change as an outline under the amber current card. Its
export is committed in `d0837ac`.

### Before Task 12

**The 403 is explained: the Text to Speech instance is disabled above its Lite
cap.** Shawn read it in IBM Cloud on 2026-10-30: "Inactive. Instance disabled
with reason_code IBMCLOUD_SERVICE_INSTANCE_ABOVE_CAP", plan Lite. It comes back
with the new month.

**Decisions on 2026-10-30, Shawn's.** What judges hear is recorded, never live:
the Text to Speech cap is 10,000 characters a month on a shared instance, and
live voice would let judges exhaust it. The recordings will speak a narration
written once by gpt-oss-120b and frozen after passing the grounding check, not
the template (Phase 5, Task 6, to be run by Claude Code). In production the
narration and voice move onto the phone (an on-device model and the phone's
own speech, with the same grounding check and fallback), which is vision, not
built. A "fresh telling" button that rewrites the narration on screen is a
stretch idea, with the bird's-eye view.

**Bob task 12 in `docs/bob_brief.md` puts "Your narrator" on Profile.** The
three narrators are shown with the one the fan's answer picked marked, tapping
another says it is coming soon, the partisan persona is shown as "The Buddy"
(its id stays `mate`), and Change becomes an outline so it does not compete
with the amber current card. A dry run of the brief passed every test then
collected and, in Chromium, marked The Buddy for an England fan and The
Storyteller for a neutral one and showed the note on tapping The Caller; it
was reverted.

While it was briefed, every failure was in `tests/test_narrators.py`.

### The hero recordings, once the service answers

**The six recordings are not generated: Watson Text to Speech answered HTTP
403 to every request on 2026-10-30.** Everything around them is built, the
words and the price are known, and `hero.audio` in `app/web/matches.json` is
still `{}`, so the moment card's play button stays disabled for all three
listeners. See "Phase 5, task 5" below for the run, the evidence and what is
owed.

**Shawn: check the Text to Speech instance in IBM Cloud.** Nothing in this
repo can read the usage counter, and the 403 body carries no reason, so
whether this is the Lite plan's monthly characters, a disabled key or a
deleted instance is a question for the console. The credentials file is
intact: `app/credentials.py` reports `C:\Users\shawn\.prelude\.env defines
TTS_API_KEY, TTS_URL, TTS_VOICE, WATSONX_API_KEY, WATSONX_PROJECT_ID,
WATSONX_URL`, by name and no value. Once it answers, the whole of task 5 is
one command:

```
.\.venv-prelude\Scripts\python.exe -I scripts\tts_hero.py --confirm
```

**Bob task 11 is built, checked and fixed.** `35708cd` built the player to the
brief, but in Chromium with a silent test file under one key the play button
stayed disabled for every listener: the player read `Prelude.whenMatches`'s
argument as the list of matches when it is the document. The follow-up reads
`doc.matches`, returns on a failed fetch, and adds a test that fails on the
original. Rechecked: the Argentina fan's key played, paused, advanced the
timer and waveform and replayed; the two keys with no file stayed disabled.
`pytest -q` reports `675 passed` and all five gates pass. Nothing more can be
heard until the recordings exist, after the November 1 TTS reset.

### Bob task 11, as it was briefed

**Bob task 11 in `docs/bob_brief.md` wires the moment card's player to real
audio.** Which recording a fan hears is decided in Python by
`scripts/write_headers.py`, from `default_persona` and `situation`, and
written as `hero.voice_for`; the browser looks its answer up in `hero.audio`,
which stays empty until the hero recordings are generated after the
November 1 TTS reset, so until then the play button is disabled. A dry run of
the brief passed every test then collected and, in Chromium with a silent test file under
one key, played and paused, advanced the timer and the waveform, replayed, and
left the button disabled for the two keys with no file; it was reverted.

The dry run also found that a player loaded in the `<head>` sees no buttons, so the brief
requires the `DOMContentLoaded` start that `match-content.js` uses.

`pytest -q` reports `13 failed, 661 passed`. Every failure is in
`tests/test_narration_player.py`.

### Before Task 11: Task 7 is done

**Bob task 10 is built and checked, and with it the Task 7 work.** `4ef3aa0`
built the Profile screen to the brief. Driven in Chromium it showed "Shawn |
Argentina", Change reopened the card on Live with Argentina pressed and the
name filled, the new answer held without reopening on reload, and Profile then
showed "Olivia | Just here for the game". Two corrections: `asked()` matched
"ask" anywhere in the query, and now reads `ask=1` as a parameter; and the
screen carried its own Tailwind config instead of the shared one, with a dark
`primary-container`, so its amber looked disabled on Shawn's phone. The shared
head is restored and a test now holds every screen to one config. `pytest -q`
reports `501 passed` and all four gates pass. Change was then given the
Heading out treatment, `text-on-primary` with `shadow-lg
shadow-primary-container/20`, Shawn's pick for consistency with the app's main
actions over an outline. The Task 7 plan's persona cards
on Profile move to Phase 5, once there are voices to pick.

### Bob task 10, as it was briefed

**Shawn found the answer could not be changed.** It lasts the tab's session and
a refresh keeps it, so a fan who typed a name was stuck with it. Bob task 10 in
`docs/bob_brief.md` adds a Profile screen with the name, the side for the
match and a Change button that reopens the card on Live, and makes the person
icon and the Profile tab lead to it. The persona cards wait for Phase 5, when
there are voices to choose. A dry run of the brief, driven in Chromium, showed
"Shawn | Argentina", reopened the card with Argentina pressed and the name
filled, saved the new answer without reopening on reload, and showed "Olivia |
Just here for the game"; it was reverted. `pytest -q` reports
`24 failed, 476 passed`, all of them `tests/test_profile.py`. Bob's task 9
export is committed.

### Bob task 9, its follow-up

**Bob task 9 is built, checked and corrected.** `c6fc1ad` built the card to
the brief, and in headless Chromium at 390 wide it asked "Who are you with
tonight?" on both matches, kept Continue disabled until a choice, stored the
answer and the trimmed name in `sessionStorage`, did not reappear on reload,
and gave "...Here's how it happened, Olivia." on the moment card. The same
run caught one bug: a name holding `$&` came out mangled, because it was passed
to `replace()` as the replacement. The follow-up fixed it and added a test that
fails on Bob's version, and swapped four classes the app did not already use
for its own tokens. `pytest -q` reports `476 passed` and all four gates pass.
Once the Tailwind and font hosts were allowed for this workspace, a styled run
at 390 wide showed two problems with the choices, both fixed: the selected
choice set light text on amber and was hard to read, and the unselected choices
had the card's own background, so they read as plain text rather than buttons.
Selected now uses `text-on-primary-container`, as Continue does, and unselected
sits on `bg-surface-container-highest`. Two older wraps on the Live screen are
cosmetic and not changed: "AT VENUE · GPS" breaks inside its pill, and the seat
line leaves "6" alone on its second line for 2022.

### Bob task 9, as it was briefed

**Bob task 9 in `docs/bob_brief.md` is briefed.** The card asks, once per match
on the Live screen, who the fan is with and what to call them; both answers stay
in `sessionStorage`. The name goes on the header's last sentence ("...Here's
how it happened, Olivia."), Shawn's call on 2026-10-29. The Live badge stops
wrapping, the one cosmetic finding from the visual check at `c0568a8`, which
otherwise passed on both matches, locally and live, at 390 and 1280 wide.
`pytest -q` reports `15 failed, 460 passed`, all of them
`tests/test_listener_card.py`. After Bob: a browser check of the card's
behaviour, then the Profile tab.

### Before Task 9

**Bob task 8 is built and checked.** `30116a2` changed exactly the five values
in the brief. `pytest -q` reports `459 passed`, all four gates pass, and
`scripts/check_match_copy.py` now holds every match to one missed goal. Its
export is committed and was scanned for key-shaped strings, with none found.

### Bob task 8, as it was briefed

**Shawn found that the 1986 step-away missed two goals.** The fan left at 48'
at 0 to 0 and came back at 55' to 2 to 0, with goals at 50:27 and 54:18 in the
window and one buildup on the card. 2022 was already one goal. His decision on
2026-10-29: the 1986 fan leaves at 52' at 1 to 0. `scripts/check_match_copy.py`
now refuses any window that holds more or fewer than one goal, so the rule
outlives this fix, and it fails on 1986 until Bob's Task 8 in
`docs/bob_brief.md` landed, with 6 failures in `tests/test_live_before.py`
while it was briefed.

A moment card that tells several missed goals in order is a planned feature,
not built: real fans can miss more than one, and that card would play each
buildup with its own header.

### Before Task 8: Bob task 7

**Bob task 7 is built and checked.** `8215108` touched only
`app/web/matches.json` and the moment card, made the six changes in the brief
and reran `scripts/write_headers.py` (`--check` passes). `pytest -q` reports
`452 passed` and all four gates pass. Its export was committed in `76e0d15`
and scanned for key-shaped strings, with none found.

**Checked in headless Chromium on both matches, at 390 by 844 and 1280 by
800, after the commit.** The rendered header is each match's line ending
"Here's how it happened.", the share button carries "Maradona's solo goal as
it happened." and "Di María's counter goal as it happened.", "STEPPED AWAY"
appears nowhere on the card, and the Live screen shows "Ready when you are."
after Heading out and the settled helper before it. That run had no network,
so the Tailwind and font CDNs did not load and the layout was not judged:
the look still needs a real-phone check on the live site.

**Next:** Shawn checks the moment card on his phone, then the "Who are you
with" card and the name get briefed for Bob.

### Bob task 7, as it was briefed

**Bob task 6 is built and checked.** `aab7093` added
`scripts/write_headers.py`, which runs the orchestrator over the data and
writes `hero.opening` into `app/web/matches.json`, and the moment card's
heading now shows it. Its diff touched only the three files the brief allowed
plus the script's output, the script holds no header text of its own, and
`--check` passed. Its session export was committed in `95341d1` and scanned
for key-shaped strings, with none found.

**Task 7 is split into Bob tasks, and the second is briefed.** Bob builds in
tight sessions; this chat writes each brief with failing tests and checks his
commit; Claude Code does the real-browser check and the larger doc updates. Bob
task 7 in `docs/bob_brief.md` is the copy Shawn settled on 2026-10-29: the
"YOU STEPPED AWAY" label removed, "Ready when you are." after Heading out,
"Listen on Prelude." as the share title, "...as it happened." share texts, and
the header ending "Here's how it happened." The tail is already changed in
`app/orchestrator_contract.py` and the tests, so Bob reruns the script. After
it: the "Who are you with" card and the name, then the Profile tab.

**The suite was red on purpose while it was briefed**, with 13 failures, all
of them Bob's Task 7.

**Fixed while briefing it:** the kickoff comments in
`tests/test_orchestrator.py` called 16:00 and 18:00 the real kickoffs. They now
say the times are chosen for the rule, and that the match index records 19:00
and 17:00. The stale `_note` in `app/web/matches.json` is item 6 of Bob's
task.

**Still owed to Claude Code:** commit Bob's task 7 export once Shawn has
saved it, take it off `DELIBERATELY_ABSENT`, and check the moment card and
the Live screen in a real browser on both matches at 390px and on desktop. The three things to hold on to through all of Task 7:

- **The header does not change by listener.** One moment gives one line to a
  fan of either side and to a listener with none. The "Who are you with"
  answer picks the persona through `default_persona`, and nothing else.
- **The name is added on the phone**, after the narration has been generated,
  and it is never sent to a model or a server.
- **No screen shows a header yet.** Task 7 is what puts it on the moment card,
  so `scripts/scan_copy.py` and `scripts/check_match_copy.py` both start
  caring about the header's copy at that point.

Three functions in `app/orchestrator.py` have no caller: `phase`,
`score_state` and `outcome`. They stay, and "Phase 4, the follow-up after Bob
task 5" under What was built says where they are and why removing them is a
later Bob task. Check whether Task 7 wants any of them before that is raised.

### Settled after task 6d

Three decisions, all Shawn's, all taken on the measured runs rather than on
an argument about prompts.

**The personas are separated by sound, not by text.** Three attempts at three
registers gave one register back each time: 0.6 words per sentence of spread
on `granite4:micro` with the register described, 2.1 on
`openai/gpt-oss-120b` described, 1.9 shown as a worked example. The narration
text is one style for every persona now, and each persona becomes an IBM voice
plus SSML prosody in Phase 5: rate, pitch, and breaks between sentences.

**Comprehension comes first.** The Caller's energy comes from emphasis and
pitch, with a rate only modestly above the Storyteller's and a ceiling on it.
Sentence breaks let each beat land, with a slightly longer break before the
goal sentence. Shawn sets the rates by ear in Phase 5, words per minute is
measured from the real audio, and the measured ceiling goes into config. The
Phase 5 entry in the Plan carries this.

**The header becomes game-focused.** It states what the goal did to the score,
not how the fan should feel. Allegiance no longer changes the header: it picks
the persona. Task 2 above is that change, and `docs/VOICE.md` carries the
wording.

### Settled earlier (Task 4b and Task 6)

**Task 4b is run and Task 6 is finished. Both decisions are Shawn's, and
Task 7 waits on them.**

**The model.** `openai/gpt-oss-120b` grounded 33 of 33 narrations on the first
attempt with no fallback, against `ibm/granite-4-h-small` at 16 of 54 with 23
fallbacks, and it costs fewer tokens per narration because it does not retry.
It is six tenths of a second slower a narration. `ACTIVE_CANDIDATE` in
`app/narration_config.py` is still Granite, and switching it is the one line
that file was written for. Nothing in the repo assumes either way.

**Two things to know before switching it.** The comparison ran on the chat
endpoint, so whatever ships has to pass `chat=True`, and
`openai/gpt-oss-120b` needs `reasoning_effort: low` or it spends about 1,500
tokens thinking before every narration.

**The personas.** The question Task 6c left open is answered and the answer is
no: on both paid models the three voices write the same narration. The Mate
reaches for the first person on the larger model, 9 of 12, and writes "Our
Peter Beardsley was dribbled past." The three options from Task 6c still
stand, with better evidence under them now: leave the personas as they are,
rewrite the styles and remeasure the same way, or ship fewer of them. A fourth
is open now that a model follows instructions this exactly: give each persona
its own worked example in the prompt rather than a description of a register,
since what reached this model was the rules and not the prose.

### Settled by Task 4b and Task 6 (the old next action)

**Task 6 is finished and Task 7 is next, after Shawn has read the Task 6c
numbers.** The three personas are built, wired into the prompt and the check,
and measured. What the measurement says is that on `granite4:micro` the three
voices are not separable: words per sentence is 4.9 to 5.5 across all of them,
and the Mate never once used the first person it is the only voice allowed.

**That is a decision for Shawn rather than a bug to fix.** Three options, and
nothing in the repo assumes one of them:

1. Leave it. The personas are a Phase 5 and Task 7 feature and the model that
   ships them is chosen in Task 4b, which is where this should be retested.
2. Make the styles harder for a small model to ignore, and remeasure the same
   three goals the same way so the before and after are comparable.
3. Drop to two personas, or to one, if the voices cannot be told apart on the
   model that ships.

**Task 4b now has a third arm worth running**, since the persona prompt is
the one that costs first-attempt grounding: one candidate with a persona and
one without, on the same goals, so the cost is measured on a model that might
not pay it.

**Bob's task 4 export is committed.** It was scanned first, as
`bob_sessions/README.md` requires, and nothing was scrubbed: no variable name
from `.env.example`, no token, no key-shaped string and no URL carrying a
query string.

Task 4b, the paid watsonx comparison, can run at any point and has one extra
arm recorded in the Plan: one candidate without the beats block, on the five
multi-beat goals only.

**Read `docs/narration_eval.md` first.** It is the measured state of the
narration, and it now holds two runs. Task 4a found grounding healthy on the
development model (22 of 27 first attempts) and completeness absent: all
fourteen model narrations on the goals where coverage can move cited the shot
and nothing else. Task 4c named the beats in the prompt and took coverage on
those goals from 42% to 95%, at a cost of two first attempts out of fifteen,
all of them on the 22:24 penalty. Any further prompt change should be measured
the same way rather than argued about.

The pass rate is worth re-measuring after any prompt change: `--goals` and
`--runs` make a one-goal check cheap, and the full twenty-seven takes about
fourteen minutes on CPU.

What is in place:

| What | Where |
| ---- | ----- |
| The contract | `app/event_feed.py`, shapes and protocol |
| The implementation | `app/statsbomb_event_feed.py`, class `StatsBombEventFeed` |
| The tests | `tests/test_event_feed.py`, 28 tests, all passing |
| The buildup tests | the 14 in `tests/test_event_feed.py::TestBuildup` |
| The brief it was built to | `docs/bob_brief.md` |

Run the suite with `.\.venv-prelude\Scripts\python.exe -m pytest`.

Settled while writing the narration copy:

- **Set-piece buildup needs the prior possession. Settled and built.**
  `buildup` is on `EventFeed` in `app/event_feed.py` and implemented in
  `app/statsbomb_event_feed.py`; `docs/bob_brief.md` carries the brief it was
  built to as Task 3. `event_window` was left alone, as its truncation rule is
  deliberate. Narration calls `buildup` for a set piece rather than widening
  the window.
- **"Verified from play data" is the whole point of the raw-record rule.** Every
  line that carries the label has to trace to an event in the window it was
  written from. A line that cannot be pointed at does not get the label, and
  there is no softened variant of the phrase.

The EventFeed and moment-detection module stays reserved for IBM Bob. It is
built, but `CLAUDE.md` still governs it: further work on moment detection is
Bob's, and Phase 4 should call the module rather than reach around it.

**Session exports go in `bob_sessions/`,** one per task, committed rather than
ignored, and scrubbed of credentials before each commit. See
`bob_sessions/README.md` and `.bobignore`.

**Before starting:** run `scripts/fetch_statsbomb.py`, since `data/raw/` is
gitignored and absent from a fresh clone.

### Settled during the Phase 2 review

- **2022 defining moments are periods 1 to 4 only.** A shootout has no buildup
  to narrate, so excluding it is the right default.
- **`Moment` carries no period field.** Accepted as it stands. Bob can add one
  later, with the tests, if the module needs it.

## Phase 5 backlog

Items found during Phase 2 that belong with the wiring, not before it:

- **Keyboard focus states.** `docs/DESIGN.md` records that focus is defined only
  on the picker's text inputs. Every button in the system has no focus style,
  and the toggle at `prelude_04_moments.html:263` sets `focus:outline-none` with
  no replacement, so it has no visible keyboard focus. This is a real
  accessibility gap and a cheap win on the design and usability axis.
- **The empty placeholders.** The Moments meta badges, the three Moments player
  timers, and the moment card's `#timerReadout` are all present and empty,
  waiting for real values from the fixture.
