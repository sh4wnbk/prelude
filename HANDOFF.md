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
done.** Tasks 3d, 4a, 4b, 4c, 5, 6a, 6b, 6c, 6d, 7, 8 and 9 are built, and so
are Bob's tasks through task 13; the pick is made, the six are written and in
the repo, and what is left is two decisions about how a place is read, the
freeze, the disclosure and the recordings, and then Phases 6 and 7. Paths a doc
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

### Task 9: the narration framework, as the standard and then as a check (done)

**9a, `198f368`.** The framework into `docs/VOICE.md`, replacing one style for
every persona, and `tests/test_reference_narrations.py` with the eight
reference narrations in it as failing tests. They failed only on the citation
regime, which is what 9b replaced.

**9b, `8e9a79c` and `d3f1ba0`.** Step 1 put the recorded fields a goal call
says out loud on `Beat` in `app/narration_prompt.py`: the play pattern, the
pressure, the pass recipient and length, the assist, the first-time flag, the
body part, the two locations as `Spot` and the millisecond timestamp, with the
field positions and the duration computed by code. Step 2 added
`app/narration_grammar.py`, which reads a narration that cites nothing, and
gave `app/grounding.py` two readings picked off the narration's own shape.

**9c, `e76ea63` and what follows it.** `app/goal_call_prompt.py` holds a style
per narrator and situation, shown through an invented match with invented
players, and `scripts/narrator_candidates.py` generates three candidates for
each of the six recorded slots. `scripts/tts_hero.py --budget` went to 3,500,
because six narrations replace two spoken three ways each. The run and its
numbers are in "Next first action" above.

### Task 9d: the play tightened, the reaction added, and the run at a high effort (done)

**The candidates were plain, near copies of each other, and some of them said
things the records contradict.** Shawn read the eighteen of Task 9c aloud and
found three kinds of mistake that nothing could catch: Álvarez "carried it
back to MacAllister" and "slipped it back" over a pass of 38 yards up the
pitch, "drove forward" over carries of under a yard, and "smashed it home"
over a shot record that says nothing about force.

**9d step 1, `70e05a2`.** Four rules in the goal-call reading. "Forward" and
"back" are a claim about the change in x on a pass or a carry, with
`DIRECTION_YARDS` at 2.0: nothing in either hero passage moves the ball
between 0.8 yards and 9.0, so the threshold sits in that gap. "Drove", "ran",
"burst" and the words like them need a recorded carry of `RUN_YARDS`, 10.0:
Maradona's three long carries are 34.9, 16.8 and 16.7 yards and every other
carry in either passage is 1.1 or less. A carry never delivers the ball to
another player, so a chain whose only verb is a carry is refused. And force
words are refused outright, while the neutral finishes stay sayable:
"struck", "fired" and "slotted" joined `ACTION_CLAIMS` as `Shot` claims.
Re-read through the Task 9c candidates, eleven of the eighteen now fail.

**9d step 2, `d607588`.** The reaction layer. Shawn settled on 2026-10-31
that a narration has two layers: the play, grounded strictly, and the
reaction, which is the narrator feeling the moment and claims nothing about
the data. A reaction is at most `REACTION_WORDS` words, holds no digit, names
no player, team or pronoun, and makes no claim about a recorded field; it
stands once, at the goal, after the finish has landed. Everything else still
applies to it, so a verdict about history, a force word, "you" or a cheer
from a voice that does not cheer is refused in a reaction exactly as in the
play. "!" has two places now rather than one, the finish and the reaction
after it. The eight references hold no reaction and all eight still pass.

**9d step 3, `9a1bca1`.** Both layers into `docs/VOICE.md`, and "The label,
and the two layers under it" into `README.md`: the label claims that every
event happened as told, and the reaction tells no event. Each of the four
worked examples in `app/goal_call_prompt.py` is a full telling with one
reaction, and the rules are thirteen. Rule 13 asks for tellings that differ
in structure rather than in wording, and `build_goal_call_prompt` takes
`avoid`, the candidates already kept for that slot, because three independent
calls cannot differ on purpose unless each one is told what the others said.

**9d step 4 is five commits, because the run found five things.** Reasoning
effort, the length cap and the timeout are per-run settings now
(`57f8940`), and the plan states the token estimate beside the call count.

The run then taught the rest:

| What happened | What it cost | What fixed it |
| ------------- | -----------: | ------------- |
| at effort high the model answered with reasoning and no narration | 4,718 | `--max-new-tokens`, measured at 16,000 (`5575853`) |
| rule 12 asked for "about 230 characters" and it counted letters | 2 probes | rule 12 asks for words and says not to count (`5575853`) |
| rule 3 did not say where the reaction goes, so both efforts wrote it first | 2 probes | rule 3 says it is the last thing written (`5575853`) |
| one answer with no content ended the whole run | nothing yet | `AnsweredWithoutContent` is a failed attempt (`21c9795`) |
| a call that never came back ended the run after one slot | about 72,000 | `--timeout`, and a lost call costs one candidate (`871115d`) |
| "we won it back through Molina", twice more | 2 attempts | the records say no recovery is there (`e28fbd8`) |

**What high effort costs, measured.** One goal-call prompt of 2,746 prompt
tokens, the same prompt each time: at effort low the model answers in 295
completion tokens, and at high it answers in 14,141 and returns nothing at
all under a cap of 8,000. So high is about fifty times low on this prompt.
The figures are in `app/narration_provider.py` beside
`COMPARISON_MAX_NEW_TOKENS`, and `WatsonxProvider` counts what watsonx says
it billed (`0aca40e`) so the next estimate can be checked against a bill
rather than against another estimate.

**9d step 4, the near copies, `f8d3ba1`.** `play_shape` in
`scripts/narrator_candidates.py` reads a candidate with the goal-call grammar
and keeps the kinds of move each sentence of the play makes. It reads kinds
and not words, so two tellings differing only in a synonym are one shape and
the second is dropped, and the reaction is left out of the shape. Shawn's
four references for each hero goal come out as four shapes, so it is not
over-eager. Applied to the eighteen this run produced it flags two.

### Task 15: the six written by the team, and the two the check still refuses (steps 1 to 3 done, stopped at step 3)

The record is above. Listed here so the plan reads in order: a half said with
a possessive resolved from the listener's side, a telling required to open on
a name, the six hero narrations the team wrote put in the repo and read
against the records, and a stop: two of the six are refused for a place, so
the freeze, the disclosure and the recordings were not done. Steps 4, 5 and 6
are still owed and are the three things under "Next first action".

### Task 14: the fallback back in the repo, the side rule, and places required (done, the run kept one)

The record is above. Listed here so the plan reads in order: the six fallback
narrations written verbatim into `scripts/fallback_narrations.py` and
re-checked into `docs/narration_runs/`, a side said only where the ball is
clear of the middle, a candidate refused for places in the run and not in the
check, the review file copied aside with a timestamp before anything was
sent, and a run of all six slots that kept one candidate of the fourteen it
reached.

### Task 13: the move placed on the pitch (done, the six fallback candidates lost)

The record is above. Listed here so the plan reads in order: a zone
vocabulary of eight bands up the pitch and three across it, the beats
carrying a place where the move starts, turns and ends, a wrong place
refused, rule 17 asking every narrator for two or three of them, and a run
of all six slots that kept eight of eighteen and overwrote the six
candidates it was told to keep as the fallback.

### Task 12: the hyphen, the Storyteller's full sentences and the two-slot rerun (done)

The record is above. Listed here so the plan reads in order: a hyphen reading
as the space it stands in for, so "first-time" and "left-foot" are checked
rather than read as prose; the Storyteller told to write no pass as "X to Y";
and one rerun of the two 2022 slots that had something to gain from both.

### Task 11, the second list: the pressure rule, the beats as phrases, two rules and the near copies (done)

The record is above. Listed here so the plan reads in order: "under pressure"
attributed to the player on the ball with "from X" checked against X's own
pressure, every beat rendered as a phrase instead of a line with its fields
labelled, rules 15 and 16 about the long ball and the first-time finish, a
near-copy filter on the words as well as on the shape, and one rerun of the
three 2022 slots.

### Task 11: the three check and prompt fixes, and the rerun (done)

The record is above, under "Task 11". Listed here so the plan reads in order:
`is_a_reaction` against the match's own names, attribution read off the
subject of the sentence rather than off the ball, the yard figures out of the
beats with the consecutive dribbles grouped, and one rerun of the six slots
with no retries.

### Task 10: a token cap, curated beats and rule 14 (done, the run short of eighteen)

**The diagnosis, from Shawn on 2026-10-31: the candidates echo the fact
list.** Every one of the eighteen said "received, carried and passed",
because the prompt handed over every recorded event of the passage. Eight of
the twenty-four 1986 records are a `Ball Receipt*` and seven more are a carry
of under a yard. Nothing in `app/grounding.py` was wrong about any of it: a
receipt is a real record and a touch on the spot is a real record, and
neither is a beat. High effort cost about 817,000 tokens and bought nothing,
and the fix was never the model: it is curating what the model is given,
which is Prelude's job whatever narrates.

**Step 1, `11b357d`: a run is capped in tokens and refuses to start without
one.** `WatsonxProvider` takes `token_cap` and raises `TokenCapReached`
before a call whose worst case would pass it: the tally it already reads off
watsonx's `usage` object, plus the prompt at `CHARACTERS_A_TOKEN`, plus the
whole of `max_new_tokens`, because a reasoning model writes its reasoning
into that budget. Before the call rather than after it, since a call already
sent is already billed. `scripts/narrator_candidates.py` takes
`--max-total-tokens`, there is no default, and `--confirm` refuses without
one. When the cap is reached the run keeps every candidate already written:
the slot it stopped in with what it had, the goal with the slots it had, and
the review file saying it is short of what it asked for.

**Step 2, `62c7d6b`: `app/story_beats.py`, and the records block is gone.**
The prompt now shows the beats a goal call tells: the recovery, each pass
(who it reached, "forward" or "back" off the change in x, "long" at
`LONG_PASS_YARDS`, the assist, the box), each carry of `RUN_YARDS` or more
(its distance in whole yards and whether it ended in the box), each dribble
past an opponent as one beat for the two records naming both players, the
pressure on the player with the ball, and the finish with the body part and
the first-time flag. Receipts go because the pass beat already names who the
ball reached; a carry under `RUN_YARDS` goes because a touch on the spot is
not a turn in the story.

`StoryBeat` carries no minute, no second and no timestamp, and
`NO_CLOCK_FIELDS` is read off the dataclass by a test, so a clock added to it
fails a test rather than reaching a prompt. The goal's minute is in the
report header and the model never sees it. `play_pattern` and the own half
are said once above the list rather than on every line, which was two facts
printed twenty-four times.

**The beat lists, from `scripts/story_beats_report.py`:**

| Goal | Records | Beats | What they are |
| ---- | ------: | ----: | ------------- |
| 1986 54:18 | 24 | 14 | 1 recovery, 2 passes, 3 pressure, 4 dribbles past, 3 runs, the finish |
| 2022 35:22 | 13 | 6 | 5 passes, the finish |

The 1986 list in order: Cuciuffo recovered; Cuciuffo to Enrique, forward;
Enrique to Maradona, the assist, forward; Beardsley pressed; past Beardsley;
a run of 35 yards forward; Reid pressed; past Butcher; 17 yards forward; past
Fenwick; 17 yards forward, ending in the box; Butcher pressed; past Shilton;
the shot, from inside the box, with his left foot. The 2022 list: Molina to
MacAllister, MacAllister to Messi, Messi to Álvarez, Álvarez to MacAllister
long, MacAllister to Di María the assist into the box, and the shot first
time with his left foot.

**Butcher's third pressure is matched on feed order and not on the clock.**
It is recorded at 54:17 against the carry at 54:15 it overlapped, because the
clock fields floor and a pressure lasts longer than the touch that began
under it. Matching on the second dropped it; `_pressed_the_carrier` looks at
the possession team's nearest record in feed order instead, and all three
pressures are kept. Reid's only record in the passage is a pressure, so
without them "Beardsley and Reid closed him down" cannot be written at all.

**The check is unchanged and still reads every record.** The curation can
only narrow what a narration may say: a line about a ball receipt would still
pass the check and will not be written, because the model was never shown
one. The block no longer says "nothing happened that is not here", which a
curated list makes untrue; it says the narration may not reach outside the
list, which is true.

**Step 3, `c938a87` and `185563e`: rule 14.** "Use the word 'who' at most
once in the narration. Join the play with other connections: a comma chain,
'and', 'on to', or a new clause." Added as rule 14 rather than inserted, so
the numbers rules 11, 12 and 13 are referred to by elsewhere do not move. The
cadence rules are untouched: rule 12 still asks for one or two sentences of
play with the clauses joined, nothing bans a long sentence and nothing asks
for a full stop after each pass. Nothing in `app/grounding.py` answers to it
because it is cadence and not a claim, so `said_who` counts the word, the
review table has a "who" column, and a candidate saying it more than once is
flagged in bold and kept.

**The run, and the cap stopped it at ten of eighteen.** Six slots, three
candidates each, `openai/gpt-oss-120b` at `reasoning_effort` low,
`--max-total-tokens 80000`. The candidates are in
`C:\Users\shawn\prelude-review\narrator_candidates_2026-11-05.md`, with the
same data beside it as JSON.

| What | Figure |
| ---- | -----: |
| billed by watsonx, off the `usage` object | 76,542 |
| of it prompt | 62,766 |
| of it completion | 13,776 |
| the cap | 80,000 |
| unspent | 3,458 |
| the plan's expected figure | 78,622 |
| calls sent | 26 |
| candidates kept | 10 of 18 |
| slots reached | 5 of 6 |

**Where it stopped.** In the 2022 `buddy_scored` slot, on candidate 2: 76,542
billed and the next call's worst case 80,731. So 2022 `buddy_scored` has
nothing and 2022 `storyteller_neutral` was never generated. Everything
written before that point is in the files.

**The prompt is the expensive half, and the retries are why the run ran out.**
62,766 of the 76,542 is prompt, over 26 calls, which is about 2,414 a call.
Nine of the 26 were failed attempts. Eighteen calls at that rate is about
43,000 and the cap would not have been reached; the nine retries spent the
difference.

**Eight of the nine failures are one failure.** The model wrote the reaction
as a second sentence opening on a capitalised adjective, "Incredible!",
"Pure magic!", "Unbelievable!", and the check refused all three the same way:
`is_a_reaction` wants a sentence that names nobody, and a capitalised word
that is not in `NOT_A_NAME` reads as a name. "What a finish!" passes because
"What" is in that set. The same attempts were also refused for the
exclamation mark and for ending the play and then carrying on. This is the
check working as specified on an edge the prompt does not warn about, and it
cost nine calls of twenty-six. Whether the fix belongs in `NOT_A_NAME`, in
`is_a_reaction` or in rule 3 is the next thing to decide, and nothing was
changed here.

**The distances are being read out loud, and that is new.** Every 1986
candidate spells the yards: "carried forward thirty-five yards, evaded Reid,
beat Butcher, ran forward seventeen yards, beat Fenwick, ran forward
seventeen yards into the box". It is grounded, because the beats carry the
distance and the grammar holds a yards claim against the record, and the two
seventeens read as a stumble rather than as a build. The three
`storyteller_neutral` candidates say "ran forward" with no figure and are the
better cadence for it. Whether a beat should carry the distance at all, or
say "a run" and nothing more, is Shawn's call after reading them aloud.

**Rule 14 held on all ten.** Seven say "who" once and three say it not at
all, against eighteen of eighteen hanging the move off it on 2026-10-31.

**Every candidate fits the budget.** `scripts/tts_hero.py --budget` is 3,500
for the six recordings, so 583 a recording, and the ten run 297 to 369
billed. The 1986 candidates are 343 to 369 and the 2022 ones 297 to 339.

### Task 11: the three check and prompt fixes Shawn read off the run (done)

**Shawn read the ten candidates of 2026-11-05 aloud and none was ready to
record.** The curation had done its job: the "received" echo was gone and the
event order was right in every 1986 candidate. What was left was one hole in
the check and three things the pipeline was doing to the output.

**The hole, and it matters more than the cap.** Buddy for Argentina candidate
1 said "We won it back through Cuciuffo, who passed to Enrique and set up
Maradona". The records put `goal_assist` on Enrique. The check passed it on
twenty-one claims.

`support` was never the problem: a `chain` grounds only against a record
whose `pass.player` is the actor and whose `pass.recipient` is the target, and
"set up" only against the pass carrying `goal_assist`. The problem was which
actor reached it. `Reader` advanced `tracked` to the recipient after a chain,
and the next chain marker in the same clause took `tracked` as its source, so
the ball moving on to Enrique made Enrique the subject of "set up" although
"and" joins a second verb to the same subject.

**Fix 2, `f6cb030`: `_chain_source` answers in three steps.** A name or
pronoun in the marker's own clause; failing that the subject a chain in that
clause already established; failing that the player with the ball. A bare
marker is exempt because it carries no verb of its own, so "Molina to
MacAllister on to Messi" is the ball continuing, which rule 14 offers as a
join. All eight references still pass, including "played it to Enrique who
found Maradona", where the pronoun moves the subject on and the second chain
really is Enrique's.

**Fix 1, `bdecc28`: a reaction names nobody by the match's names, not by
capitals.** The reader emits an unknown name for any capitalised word it
cannot resolve, `is_a_reaction` refused a sentence holding one, and "What a
finish!" passed only because "What" is in `NOT_A_NAME`. So every neutral
candidate of that run ended "What a moment", "What a finish" or "What a
strike", every England one on a stapled-on "Ah, no.", eight of the nine
retries went on the refusal and the 2022 `buddy_scored` slot lost all three
attempts to it. `name`, `team` and `ambiguous_name` resolve against this match
and still make a sentence play; `unknown_name` points at no record and no
longer rules a reaction out.

One capital is still not allowed through. "Pure Pelé, that!" names a
footballer who is not in this match, which is both an invention and the
verdict about history `CLAUDE.md` forbids, so an unresolved capital is read as
a reaction only where it is the sentence's own first word. A proper noun
introduced mid-sentence keeps the sentence in the play.

**Two of the three words the model reached for stay refused anyway**, as the
editorial epithets they are: "incredible", "unbelievable" and "stunning" are
in `BANNED_PATTERNS`. What the fix widens is the rest, and the rerun used it:
"Pure magic." was written and accepted as a reaction.

**Fix 3, `ed20c8f`: no yard figures, and consecutive dribbles grouped.** The
beats carried a carry's distance in whole yards and every 1986 candidate read
it out. `yards` is `long_carry` now, a flag, and the beat says "a long carry";
the beat list is bulleted rather than numbered for the same reason, so the
block holds no digit at all. And consecutive dribbles past one player are one
beat naming the defenders in order, with the carries between them absorbed,
because a list of beats is read out as a list of beats. A pressure between
them keeps its own beat and the group sits where it ends, so a pressure inside
its span is said before it. A carry that ended in the box ends the group,
which is why Shilton is beaten in a beat of his own.

**The 1986 beat list, from `scripts/story_beats_report.py`: 24 records to 10
beats, from 14.**

```
- Cuciuffo recovered the ball
- Cuciuffo passed to Enrique, forward
- Enrique passed to Maradona, the assist, forward
- Beardsley pressed the player on the ball
- Reid pressed the player on the ball
- Maradona dribbled past Beardsley, Butcher and Fenwick, carrying the ball
  forward between them, under pressure
- Maradona carried the ball, a long carry, forward, ending in the box, under
  pressure
- Butcher pressed the player on the ball
- Maradona dribbled past Shilton, under pressure
- Maradona shot, from inside the box, with his left foot
```

The 2022 list is unchanged at six: it holds no dribble and no carry over ten
yards.

**Fix 4, the rerun: all six slots, one attempt a candidate, and it cost two
thirds of what the retried run did.** `--max-retries` is a flag now, and 0 is
one attempt with no regeneration.

| | 2026-11-05, three attempts | the rerun, one attempt |
| --- | ---: | ---: |
| calls sent | 26 | 18 |
| billed by watsonx | 76,542 | 51,496 |
| of it prompt | 62,766 | 43,691 |
| of it completion | 13,776 | 7,805 |
| the cap | 80,000 | 80,000 |
| unspent | 3,458 | 28,504 |
| candidates kept | 10 of 18 | 10 of 18 |
| slots reached | 5 of 6 | 6 of 6 |

**The grouping is in the output.** "Maradona dribbled past Beardsley, Butcher
and Fenwick, carried it forward into the box, slipped past Shilton and struck
with his left foot" is every 1986 candidate's shape now, against "beat
Butcher, ran forward seventeen yards, beat Fenwick, ran forward seventeen
yards" before it. No candidate carries a yard figure, and none says "evaded
Reid": where Reid is named it is as "pressed by Beardsley and Reid", which the
records hold.

**Five of the eight drops are the model being wrong, which is the check
working.** "Álvarez back to MacAllister" over a ball 36 yards up the pitch,
twice; "MacAllister set up Di María forward" with the "forward" landing on Di
María, whose only record with two ends is the shot; "a long pass to Di María"
over a pass of 26 yards; "Ah, no." written in front of the play; and
"Incredible!".

**Three of the eight are one false refusal, and it is new.** "Under pressure
from Beardsley and Reid" is refused with `'under pressure': no record of Peter
Beardsley is marked under pressure`. The claim is true: Beardsley and Reid are
the players who pressed. The `pressured` move resolves its actor by the
framework's action before name, so it lands on Beardsley, and `support` then
asks whether Beardsley's own record carries `under_pressure`, which is
Maradona's flag and not his. "Pressed by Beardsley and Reid" passes, which is
why half the kept 1986 candidates say it that way. The beat line "X pressed
the player on the ball" is what invites the other phrasing, so this is partly
the curation's own doing and nothing was changed for it here. The fix is a
rule about who "under pressure" is about, in `app/narration_grammar.py`, and
it is one line of `support` plus a test.

**"Glided past Shilton" still passes, and "glided" is a manner word.** "Past
Shilton" is grounded, because the records hold a dribble past him; the manner
is unsaid in the data and uncheckable, like "smashed" before it was banned
outright. No candidate of the rerun used one, and nothing was changed for it.

### Task 15: the writing moved to the team, and the two places the check still refuses (steps 1 to 3, stopped at step 3)

**Shawn, 2026-11-05: at effort low the model would not place the move, so the
six hero narrations are written by the team and verified by Prelude's
grounding check like any model output.** "Verified from play data" still means
every claim traces to the records; the check is what proves it. The authorship
is disclosed rather than implied, and the model runs stay in
`docs/narration_runs/` as the evidence of the pipeline.

**Step 1, `35db706`: whose half "our half" is.** A half said with a possessive
names a side, and the band is read in that side's own frame.
`from_the_other_end` in `app/pitch_zones.py` is the arithmetic, `PITCH_X` less
the recorded `x`, and `_reads_from_the_other_end` in
`app/narration_grammar.py` is the resolution: "our" is the listening side,
"their" is the side they are not on, and with no listener in hand the phrase
is read as the vocabulary spells it, so a Storyteller's "their own half" is
still the half the side on the ball defends.

| Said | For a fan of Argentina | For a fan of France |
| ---- | ---------------------- | ------------------- |
| "deep in our own half" | where Molina played it, `x` 25.9 | France's own half, refused |
| "deep in their own half" | France's own half, refused | where Molina played it |
| "just inside our half" | `x` 50 to 60 | where the long ball was struck, 63.2, which is 56.8 from France's end |

Three more things came with it. A half with no band word in front of it ("we
started from our own half") is the broad position claim it always was and
places nothing, so the old 2022 `buddy_scored` fallback still places the move
nowhere. "Our half" is the one first person that stands on itself: every
record in "Álvarez, just inside our half on the right" is Argentina's, so
asking the play for a France listener's own side refused a true line. And a
curly apostrophe is written as a straight one before anything is read, which
is what the kept candidate of Task 14 carried.

**Step 2, `26a461a`: a telling opens on a name.** The first word is a player,
a team or a country the records hold. `opener_missing` in
`scripts/narrator_candidates.py` is the acceptance rule, beside
`places_missing` and not in the check, because a narration opening on "We"
makes no false claim and a check that refused one would be refusing cadence.
Rule 18 of the goal-call prompt asks every narrator for it and the rule
numbers before it do not move.

**Four of the eight references open elsewhere, and the rule is newer than they
are.** The 1986 Argentina Buddy and the 2022 Argentina Buddy open on "We", the
1986 Caller on "It" and the 2022 France Buddy on "In". They are still the
standard for the writing and are still checked word for word; `docs/VOICE.md`
records the tension beside the rule. Whether rule 18 should reach them is
Shawn's call and nothing here changed them. Two recorded test fixtures did
change, because both are candidates their tests mean the run to keep: the
near-copy pair opens on Molina now and the cap test's answer on Argentina.

**Step 3, `776b4a1`: the six are in the repo and read against the records.**
`scripts/authored_narrations.py` holds them verbatim with straight
apostrophes, carries `AUTHOR` ("the team") and `AUTHORSHIP` ("written by the
team, verified by the grounding check") beside every one of them, and reads
each through the three rules a candidate meets. It calls no model, freezes
nothing, writes `docs/narration_runs/authored_2026-11-07.md` and the same
answers as JSON, and exits 1.

| Slot | Check | Claims | Places | Opener | Billed |
| ---- | ----- | -----: | -----: | ------ | -----: |
| 1986 `storyteller_neutral` | **refused** | 18 | 5 | Cuciuffo | 367 |
| 1986 `buddy_scored` | **refused** | 18 | 5 | Cuciuffo | 351 |
| 1986 `buddy_conceded` | grounded | 17 | 4 | Maradona | 324 |
| 2022 `storyteller_neutral` | grounded | 23 | 5 | Argentina | 485 |
| 2022 `buddy_scored` | grounded | 23 | 4 | Molina | 449 |
| 2022 `buddy_conceded` | grounded | 22 | 4 | Molina | 428 |

All six open on a name, all six place the move four or five times, not one of
them says "who", and the six together are 2,404 billed characters of the 3,500
the budget allows. **The three 2022 slots and the 1986 `buddy_conceded` slot
are grounded. The other two 1986 slots are refused, and both refusals are the
reading pairing a place with the wrong action.**

**The first: "on into the final third" is read as being about Beardsley.** The
1986 `buddy_scored` line says "past Beardsley, on into the final third, past
Butcher on the right". `_about` in `app/narration_grammar.py` points a place at
the move before it, which is the dribble past Beardsley at (54.4, 56.4), and
that is just inside his own half. The carry the words mean ends at (87.1,
68.6), which is the final third, and "on into" is not a move the grammar
reads, so there is nothing between the place and Beardsley. The claim is true
of the records and the pairing cannot see it. Reading a place as being about
the move after it when the move before it refuses is a change to `_about` and
a judgement about which of the two is meant.

**The second: "beat Butcher on the right" leaves Butcher a bare name.**
`PAST_MARKERS` is "past", "around" and "round", so "beat" is not read as a
dribble past anybody: Butcher and Fenwick become name moves, and the zone
branch reads a place off the attacking side's own records, which a defender's
name holds none of. The 1986 `storyteller_neutral` line is refused twice over
for it, on "on the right" and on "on the edge of the box". Both places are
true: Maradona's dribbles past Butcher and Fenwick are at (87.1, 68.6) and
(97.1, 55.1). Adding "beat" to `PAST_MARKERS` would read the line as written
and would also make "beat" a claim everywhere else it is said, which is the
decision.

**Neither was reworded**, which is what the task asked: the words are Shawn's,
the refusals are the check's, and a narration bent to fit a reading is not the
thing that was written. `tests/test_authored_narrations.py` holds both
refusals in the suite, in the words the check uses, so a change to either
reading fails there rather than passing unnoticed.

**Steps 4, 5 and 6 were not done**, and all three depend on the two refusals:
the freeze requires a narration the check passes, the README disclosure would
be claiming six verified narrations when four are, and the recordings are the
frozen text spoken. Nothing was sent to the speech service and `hero.audio` is
still empty.

**The moment card was left alone.** Shawn said so during the task, so step 5's
label change ("AI AUDIO NARRATION" to "AUDIO NARRATION") was not made and
nothing in `app/web/prelude_03_moment_card.html` was touched. It also settles a
question the freeze would have raised: `app/web/narrations.json` holds one
narration per goal and the card reads `text` from it, and
`scripts/check_match_copy.py` holds the card's inline copy to that same text,
so writing six per-slot narrations into that file is a change to the card as
well unless the per-goal `text` stays as it is. That is the first thing to
settle in step 4.

**The suite and the gates.** `pytest -q` reports `1480 passed` and all five
gates exit 0. Sixty five of those tests were added by this task, over the
resolution, the opener rule and the six themselves.

### Task 14: the fallback restored, the side rule and places required (done)

**Shawn, 2026-11-05, after the zones run overwrote the six: field position is
required and not optional.** The zones run placed the move in one of its
eight kept candidates, so the vocabulary was built and the asking was what
was weak. This task puts the six fallback narrations where a run cannot
reach them, moves the side rule off the thirds of the pitch, makes a place a
condition of being a candidate, and spends one more run.

**Step 1, `a41ea38`: the six are in the repo.** `scripts/fallback_narrations.py`
holds them verbatim as Shawn kept them, re-reads each against `data/raw/` with
the current check in the persona and listening side its slot is written for,
and writes `docs/narration_runs/fallback_2026-11-05.md` and the same answers as
JSON beside it. It exits 1 if any of the six is refused, so a check change that
would cost a fallback is visible rather than quiet. **All six are grounded
today**, and not one of them places the move:

| Slot | Check | Claims | Billed | Places |
| ---- | ----- | -----: | -----: | -----: |
| 1986 `buddy_scored` | grounded | 18 | 295 | 0 |
| 1986 `buddy_conceded` | grounded | 19 | 310 | 0 |
| 1986 `storyteller_neutral` | grounded | 22 | 341 | 0 |
| 2022 `buddy_scored` | grounded | 17 | 331 | 0 |
| 2022 `buddy_conceded` | grounded | 15 | 307 | 0 |
| 2022 `storyteller_neutral` | grounded | 16 | 369 | 0 |

**Step 2, `0e1f1e1`: a side is said only where the ball is clear of the
middle.** "On the left" is `y` under 18 and "on the right" is `y` over 62, the
sides of the penalty area, where `LEFT_Y` and `RIGHT_Y` were the thirds of an
eighty yard pitch at 26.7 and 53.3. The old rule put "on the right" on four
beats between `y` 54.9 and 60.5, a yard or two past the middle, and three of
them fell in one line: the grouped 1986 dribble beat said it three times.

Nine of the twelve places the two hero passages carry are now said with no
side. Butcher's dribble at 68.6, Molina's pass at 71.8 and the long ball's
strike at 68.2 keep it; Beardsley's dribble at 56.4, Fenwick's at 55.1, the
long ball's landing at 54.9 and Enrique's pass at 60.5 lose it.
`BOX_TOP_Y` and `BOX_BOTTOM_Y` are the same two numbers and stay separate
constants, because the box bands ask whether a spot is inside the box and the
side rule asks whether it is out wide.

**One consequence, worth knowing before the pick.** Both of the zones run's
1986 Storyteller candidates say "on the right" over the grouped dribble beat,
and that is now a wrong place: the check refuses them today. The six fallback
narrations say no side anywhere and are untouched by this.

**Step 3, `823e494`: a telling that places the move nowhere is not a
candidate.** `places_missing` in `scripts/narrator_candidates.py`, and not in
`app/grounding.py`: the check refuses a place the records do not hold and a
narration naming no place holds nothing wrong, so grounding stays about truth
and the six fallback narrations still ground. Two things are asked. At least
`PLACES_WANTED` places, which is two, the floor of what rule 17 asks for. And
in a passage holding a long ball, one of those places has to hold the
coordinate the ball was struck from, which is the zones run's own finding: all
four of its 2022 tellings placed the ball where it came down and none where it
was hit.

**The long ball test is read phrase by phrase and not by the action each
phrase was said beside, which is the weaker of the two readings.** The zones
run's 2022 Storyteller passes on an "on the right" it said about Molina's
pass, because that pass and Álvarez's strike are both out wide on the right.
The stronger reading is already in `app/narration_grammar.py` as the `about`
on a zone move, and it would refuse every candidate that run produced, which
is why this is the one built. Tightening it is a change to `places_missing`
and nothing else.

A slot that keeps nothing now prints its dropped list too. `review` stopped at
"No candidate for this slot passed" and the console log was the only record of
why, which would have hidden eleven of this run's refusals; `_slot_candidates`
is lifted out of it whole for that.

**Step 4: the review file was copied aside before anything was sent**, which
Task 13 asked for and nothing automates. The copies are
`narrator_candidates_2026-11-05.before-task14-20261105T2027.md` and the JSON
beside it, in the same directory as
`hero_candidates_2026-10-30.before-task8.json`. **They are the only copy of
the zones run's eight candidates**, and this run overwrote all three 1986
slots with nothing, so the copy was needed within the hour it was made.

**Step 5, the run: all six slots, 77,480 tokens of the 80,000, and it stopped
on the cap.** Effort low, three candidates a slot, two retries allowed, 24
generations and one IAM exchange. It reached fourteen of the eighteen
candidates it asked for and kept one.

| This run, all six slots | |
| --- | ---: |
| generations sent | 24 |
| billed by watsonx | 77,480 |
| of it prompt | 60,567 |
| of it completion | 16,913 |
| the cap | 80,000 |
| unspent | 2,520 |
| candidates reached | 14 of the 18 asked for |
| candidates kept | 1 |
| refused for places | 11 |
| dropped on grounding refusals alone | 2 |
| near copies dropped | 0 |

**The one it kept is the 2022 `buddy_conceded` slot**, on its third attempt,
grounded on 22 claims, 410 billed, and it places the move five times: "deep in
his own half", "on the right", "just inside France's half", "on the right"
again and "on the edge of the box". It is the first candidate of any run to
say where the long ball was struck from. **It carries a `RIGHT SINGLE
QUOTATION MARK` (U+2019) inside "France's"**, which the review file flags and
which would reach the speech service as written.

**Eleven of the fourteen were refused for places, and the refusal is the
finding.** Every 1986 candidate placed the move nowhere at all: nine grounded
tellings of that goal, and not one of them said a band or a side. The prompt
carries rule 17 in every voice and the beats carry the places, and at effort
low the model still writes the 1986 move as a list of defenders. Two of the
2022 candidates placed it once, on the edge of the box, which is where the ball
came down.

**The 1986 slots hold nothing in the review file now.** This run produced all
three of them and kept none, and `merged` replaces a slot a run produced, so
the zones run's five 1986 candidates are out of the file. They are in the
timestamped copy and the fallback three are in the repo, so nothing is lost
this time. The 2022 `storyteller_neutral` slot was never reached, so its zones
run candidate was carried across with its own provenance.

**Twelve grounding refusals, and the 1986 `buddy_scored` slot is where they
are.** Six of the twelve are its, and the shape is the same every time: the
model answered with two whole narrations in one reply, so the first one's
goal was followed by more play and its reaction stood before the finish. Two
other refusals are the model calling Shilton's save a shot ("fired", "struck"
with Shilton as the subject) and one is "set up Maradona" read as a Cuciuffo
assist. The three new ones are worth keeping: "Ah, no." written as the first
sentence rather than the last, "under pressure from Maradona" when `Pressure`
is the presser's record, and "France's" written with a curly apostrophe that
the name check reads as a name it does not record.

**What the three readings of the long ball cost, in one line.** The
`buddy_conceded` candidate that was kept needed three attempts to say "just
inside France's half on the right", and the two before it were refused for the
apostrophe and for "the box" over MacAllister. The phrase the vocabulary wants
is reachable and it is not cheap.

### Task 13: a place on the pitch, and the run that spent the review file (done)

**Shawn, reading the six candidates of 2026-11-05 aloud: they have no field
position.** "Dribbled past Butcher" and "a long ball to MacAllister" give a
listener nothing to place. Two of the eight references say a band ("just
inside his own half") and the other six place the move only with "in his own
half" and "in the box", so the standard itself barely does it either. The
coordinate is on almost every record and nothing was turning it into words.

**Step 1, `1d29e49`: `app/pitch_zones.py`.** Eight bands of `x` and three of
`y`, on Shawn's thresholds, each one a phrase: "deep in his own half" under
40, "in his own half" 40 to 50, "just inside his own half" 50 to 60, "just
inside their half" 60 to 70, "in their half" 70 to 80, "in the final third"
80 up, "on the edge of the box" 96 to 102 inside the box's width, "in the
box" past 102 inside it, and "on the left" and "on the right" outside `y`
26.7 and 53.3. Both box bands ask for the width as well as the line, because
a ball at `x` 110 and `y` 10 is by the byline with the goal frame between it
and the posts, and anything from 80 up that is neither box band is the final
third, which is this module's reading of a coordinate the vocabulary names no
zone for.

**A place is read off the attacking side's own record.** Butcher's `Dribbled
Past` is at (33.0, 11.5) and the `Dribble` that beat him is at (87.1, 68.6),
which is the same place said twice from two ends, so reading a mirrored
record would put "on the left" and "just inside their half" over a dribble
that was neither.

**`Facts` gains the fixture's two teams.** All thirteen records of the 2022
counter are Argentina's, so the side being attacked is not in the passage and
"just inside France's half" has no name to use. They come off the lineups
file `app/recorded_names.py` already reads, which is the same StatsBomb open
data as the event feed.

**Step 2, same commit: which beats carry a place.** The first action, a ball
recovery, each defender gone past, a long ball at both ends, the assist and
the finish. Not every beat and not every pass, because every record carries a
location and a telling that places all of them is the label reading
`beat_line` was written to stop: two of the five 2022 passes say nothing about
where they were played.

**The two beat lists, from `scripts/story_beats_report.py`.** 1986, 24 records
to 10 beats:

```
   1. José Luis Cuciuffo (Argentina), deep in his own half, won the ball back
   2. José Luis Cuciuffo (Argentina) passed it forward to Héctor Enrique
   3. Héctor Enrique (Argentina), in his own half on the right, passed it
      forward to Diego Armando Maradona, which is the assist
   4. Peter Beardsley (England) pressed the player on the ball
   5. Peter Reid (England) pressed the player on the ball
   6. Diego Armando Maradona (Argentina) dribbled past Peter Beardsley just
      inside his own half on the right, Terry Butcher in the final third on
      the right and Terry Fenwick on the edge of the box on the right,
      carrying the ball forward between them, under pressure
   7. Diego Armando Maradona (Argentina) carried the ball forward on a long
      run, ending in the box, under pressure
   8. Terry Butcher (England) pressed the player on the ball
   9. Diego Armando Maradona (Argentina) dribbled past Peter Shilton in the
      box, under pressure
  10. Diego Armando Maradona (Argentina), in the box, shot with his left foot
```

2022, 13 records to 6 beats:

```
   1. Nahuel Molina (Argentina), deep in his own half on the right, passed it
      forward to Alexis MacAllister
   2. Alexis MacAllister (Argentina) passed it forward to Lionel Messi
   3. Lionel Messi (Argentina) passed it forward to Julián Álvarez
   4. Julián Álvarez (Argentina), just inside France's half on the right, hit
      a long ball forward to Alexis MacAllister again, landing on the edge of
      the box on the right
   5. Alexis MacAllister (Argentina), on the edge of the box on the right,
      passed it forward to Ángel Di María, into the box, which is the assist
   6. Ángel Di María (Argentina), in the box, shot first time with his left
      foot
```

**The side rule puts "on the right" on three beats Shawn's own list did not
name**, and all three are just over the line: Beardsley's dribble at `y`
56.4, Fenwick's at 55.1 and the long ball's landing at 54.9, against a
threshold of 53.3. The three Shawn did name a side for are at 68.6, 71.8 and
68.2. The rule as written is what is built, and the cost is that the grouped
1986 dribble beat says "on the right" three times in one line. Moving the
line, or saying a side only where it is clear of it, is a change to
`side_of` in `app/pitch_zones.py` and nothing else.

**The finish says the place instead of "from inside the box".** The box band
is the eighteen yard line and the box's width, so it is the same claim with
one more line in it; saying both would be saying it twice.

**Step 3, `d653794`: a place is a claim, and a wrong one is refused.** Twelve
spellings, hyphens allowed on all of them, and the band and the side are two
moves because either can be wrong on its own. Each is about the action it was
said beside, not about the player: `player_spots` answers where a player was
at any point in the passage, which is right for a half and far too loose for
a band, since three of Maradona's four dribbles are in different bands. The
move before the phrase owns it, or the one after where nothing is behind it,
which is the appositive the beats are written in.

**The two broad phrases are left alone.** "In his own half" and "in the box"
stay the position claims they were, because Maradona's first touch is at `x`
55.2, whose band is "just inside his own half", and three of the eight
references say "in his own half" over it: reading the whole-half phrase as a
band would refuse a true sentence and a reference with it. A band phrase is
exclusive, so "just inside his own half" over Cuciuffo at 35.2 is refused
although it is indeed his own half.

**Shawn's two tests, and two more.** "Álvarez, deep in his own half, hit a
long ball" is refused on 3869685, because his three records are at `x` 62.5,
63.2 and a pass down at 99.3. "Beat Butcher on the left" is refused on
3750191, because every record of Butcher's in the passage is England's and a
place is read off the attacking side's own location; "went past Butcher on
the left" is refused as the wrong side, which is the same sentence with the
reason Shawn meant. A half said with a name is a claim about the name too:
"just inside Argentina's half" is refused as the side in possession and
"Brazil's" as neither side.

**Step 4, `1e45340`: rule 17.** "Place the move on the pitch two or three
times: where it started, where the decisive action happened, and where it
finished. Do not give every beat a place." General to any goal, like rules 15
and 16, and no claim rule answers to it: a wrong place is refused whether or
not a rule asked for one.

**Two reporting gaps closed first, `c2ef0fd`,** because step 6 asks a run to
print what no run could. The places a candidate used, read with the same
grammar the check reads them with, so what is counted is what was verified.
And the refused attempts of a kept candidate: `gather` recorded `refused`
only on a candidate dropped altogether, so the one refusal of the Task 12 run
is on record as the number 2 and nothing else.

**Step 5, the run: all six slots, 66,242 tokens of the 70,000 allowed, and
it stopped on the cap.** Effort low, three candidates a slot, two retries
allowed, twenty calls and one IAM exchange. Eight of the sixteen candidates
it got to were kept, and the seventeenth was not sent.

| This run, all six slots | |
| --- | ---: |
| calls sent | 20 |
| billed by watsonx | 66,242 |
| of it prompt | 54,900 |
| of it completion | 11,342 |
| the cap | 70,000 |
| unspent | 3,758 |
| candidates kept | 8 of the 18 asked for |
| slots with something in them | 6 of 6 |

**The run overwrote the six candidates it was told to keep.** The review file
is named for the day and both runs are on 2026-11-05, and `merged` carries
across only the slots a run did not produce: this run produced all six, so
all six were replaced. They are not recoverable, and nothing in the repo ever
held them. The precedent for keeping them is in the same directory:
`hero_candidates_2026-10-30.before-task8.json`, copied aside by hand before
an earlier overwrite. **Copy the review file aside before any rerun**, which
is the first thing the next run should do and is not built.

**Rule 17 reached one candidate of the six slots.** The 2022 Storyteller
places the move three times ("deep in his own half", "on the right", "on the
edge of the box"), which is exactly what the rule asks for. Four of the other
seven place it once, both 1986 Buddy candidates place it not at all, and no
candidate anywhere said where the long ball was struck from: all four 2022
tellings place it where it came down. The vocabulary works and the asking is
what is weak, which is the finding to read the eight aloud against.

**What the near-copy filter did: seven of the sixteen.** Six on the words, at
0.96, 0.94, 0.94, 0.87, 0.86 and 0.85, and one on the shape. The 1986
`buddy_conceded` slot wrote one telling three times, and two of its three
went; the 2022 `buddy_conceded` slot did the same. One candidate was dropped
on three refusals.

**Five refused attempts, and three of them are new evidence.** Two belong to
kept candidates and would not have been recorded before this task. The model
is wrong in the same three ways each time: "Peter Reid" after "past" when
Reid pressed and was never dribbled past, "pressed" attributed to Maradona
when `Pressure` is the presser's record, and "first time" on the 1986 shot,
which is not recorded first time. The third one cost a whole candidate: the
1986 `buddy_scored` slot was refused three times and twice for that.

**"We won it back through Cuciuffo in half" is kept and reads wrong aloud.**
A word is missing from "in our half" and nothing refused it, because "in
half" is not a phrase the check reads: "own half" is. It is the only kept
candidate with a dropped word in it and it is the 1986 `buddy_scored` slot's
only candidate, so the slot is one telling with a hole in it.

**A gap the beats carry: the recovery line cannot be said back.** The beat
reads "Cuciuffo won the ball back", and a narration saying that is refused
twice over: "won" claims a `Foul Won` and Cuciuffo has none, and "back" is a
direction his records do not go. "Won it back" is the phrase the check holds,
and it is what the references say. Nothing was changed for it here.

**`Spot.in_the_box` is still `x >= 102` with no width.** The zone bands ask
for the box's width and that property does not, so it calls a ball at `x` 110
and `y` 10 inside the box and so does the position claim built on it. Every
recorded location from 102 up in both passages has `y` between 32.1 and 55.1,
so the two readings agree on all the real data; the difference is a hole in
the older one. Tightening it would move `in_the_box` on every beat and every
position claim, which no step asked for.

### Task 12: the hyphen, the Storyteller's full sentences and the two-slot rerun (done)

**Shawn asked for one small, last run after reading the four 2022 candidates
aloud**: the hyphen fix the earlier run's finding named, a rule keeping the
chain shorthand out of the Storyteller's text, and a rerun of `buddy_scored`
and `storyteller_neutral` only. The 2022 `buddy_conceded` candidate and all
three 1986 slots were to be kept as they are, and they were: this run asked
for nothing from them and `merged` carried them across.

**The hyphen, `6cf8fde`: it reads as the space it stands in for.** Three of
the four kept candidates of the earlier run wrote "first-time" or
"left-foot", `PHRASES` held both phrases as two words, and neither was read
as a claim. Nothing false passed, because the record is `first_time` and
`Left Foot`, so the words were true and the check did not look; the two
Storyteller candidates said the foot that way and no other, so a line the app
would label carried an unchecked body part. `hyphens_allowed` puts a hyphen
beside the space in every phrase pattern and every chain marker, so
"under-pressure", "long-ball", "one-touch" and "set-up" read as the claims
they are and "left-footed" reads as the foot. The spelling changes what is
read and never what the records hold: the same words over the 1986 shot are
still refused, and that Storyteller candidate now passes on 17 claims rather
than 15.

**The Storyteller's own idiom, same commit: no pass written as "X to Y".**
Rule 11 for that voice asks for full sentences and a verb in every pass, and
says why: the shorthand is the Buddy's idiom and the Caller's. The references
settled it before the rule did, which is the test: neither Storyteller
reference has a bare chain in it, and both 2022 Buddy references open "Molina
to MacAllister, MacAllister to Messi". Both Storyteller candidates of the
earlier run were a list of passes with three bare chains each. Rule 8 is
unchanged and still offers "X to Y" among the forms a pass may be written as;
this is the one voice that gives it up, and the Caller's style still asks for
the shortest chains.

**The run: two slots, 21,470 tokens of the 30,000 allowed**, over seven calls
and one IAM exchange. 8,530 unspent. Three of the six candidates were kept.

| This run, 2022 `buddy_scored` and `storyteller_neutral` | |
| --- | ---: |
| calls sent | 7 |
| billed by watsonx | 21,470 |
| of it prompt | 17,572 |
| of it completion | 3,898 |
| the cap | 30,000 |
| unspent | 8,530 |
| candidates kept | 3 of 6 |

**The Storyteller rule took.** Its one kept candidate writes every pass with
a verb in it: "Molina passed forward to MacAllister, who found Messi, who
gave it to Álvarez; Álvarez sent a long ball forward to MacAllister, who set
up Di María". No bare chain anywhere in the slot, in the kept candidate or in
the two dropped as near copies, against three in each candidate of the run
before it.

**The hyphen fix is in the claim counts.** The `buddy_scored` candidate that
came back on its second attempt is grounded on 21 claims, which is the most
any 2022 candidate has reached; the earlier run's best was 18. Nothing was
asked of the model to get there: the words it already liked are now read.

**Three of the six went on the near-copy filter**, at 0.93, 0.93 and 0.86,
and `storyteller_neutral` is down to one candidate because of it. That is the
filter working on a slot where the model wrote one telling three times, and
it is also the reason this slot has one rather than three: the shape of the
2022 move is five passes and a finish, and there is less to vary in it than
in the 1986 run.

**One refusal happened and the document does not say what it was.** The
`buddy_scored` candidate 2 is recorded with `attempt` 2 and
`first_attempt_grounded` false, so its first attempt was refused, and the
words and the reason are kept only for a candidate that was dropped
altogether. `gather` records `refused` on a drop and not on a retry that
later passed. It is a reporting gap rather than a check gap, and the fix is
to record the refused attempts of a kept candidate beside the kept text.
Nothing was changed for it here.

### Task 11, the second list: who "under pressure" is about, the beats as phrases, two rules and the near copies (done)

**Shawn read the ten candidates of the first Task 11 rerun aloud and wrote a
second list of steps under the same number.** The task before it is recorded
above; this is the one that followed it on 2026-11-05, and the film is set in
2022, so the Di María narration is the one the video plays and the three 2022
slots are the ones this rerun spent anything on.

**Step 1, `b0d4d2c`: "under pressure" belongs to the player on the ball.**
`support` was never the problem and neither was the pressure record: the
actor was. StatsBomb puts `under_pressure` on the record of the player being
pressed and a `Pressure` on the record of the player pressing him, so reading
the actor off the words landed the claim on Beardsley and asked his own
record for Maradona's flag. The claim is the carrier's now, whoever is named
beside it, and "under pressure from X" is a second claim of its own: X has a
`Pressure` in the buildup. Both have to hold, so the refused narration of the
earlier run passes on twenty claims and "under pressure from Fenwick", who
was dribbled past and pressed nobody, is refused with `'under pressure from
Fenwick': the records hold no pressure by Terry Fenwick in this passage`.

A comma ends the list of pressers, which is the same bluntness `CLAUSE_BREAK`
buys everywhere else and the same price: "under pressure from Beardsley, Reid
and Butcher" checks Beardsley and reads the other two as names. It is a
leniency rather than a false refusal, and it is what keeps "under pressure
from Beardsley, Maradona dribbled past Butcher" from making Maradona a
presser.

**Step 2, `8c1c437`: a beat is a phrase a narrator can say.** The beat read
"Julián Álvarez (Argentina) passed to Alexis MacAllister, long, forward",
with the recorded fields labelled after the name, and four of the five 2022
candidates wrote "Álvarez to MacAllister forward": the label read out loud.
Every beat is one clause now, computed from the same fields. The direction
sits inside the verb phrase, a pass at `LONG_PASS_YARDS` is "a long ball
forward to X", a pass reaching a player who has already received one says
"again", and the finish says first time and names the foot.

**The 2022 beat list, from `scripts/story_beats_report.py`: 13 records to 6
beats.**

```
  - Nahuel Molina (Argentina) passed it forward to Alexis MacAllister
  - Alexis MacAllister (Argentina) passed it forward to Lionel Messi
  - Lionel Messi (Argentina) passed it forward to Julián Álvarez
  - Julián Álvarez (Argentina) hit a long ball forward to Alexis
    MacAllister again
  - Alexis MacAllister (Argentina) passed it forward to Ángel Di María,
    into the box, which is the assist
  - Ángel Di María (Argentina) shot first time with his left foot from
    inside the box
```

**"Into the box" goes after the recipient and not before him**, because the
box is where the ball arrived and he is the player who was in it. MacAllister
played the assist from four yards outside, so "MacAllister passed it into the
box" is a claim about MacAllister's own position, which `player_spots`
refuses and should. A narration told in the beats' own order is grounded on
twenty claims and the same narration with the box moved in front of the
recipient is refused, which is a test.

**Step 3, `72103d7`: rules 15 and 16.** "When a pass is marked long, it is
the turn of the move; give it its own clause." and "When the finish is first
time, say so, with the foot." Both are general to any goal and neither is a
claim rule: the check holds "a long ball" and "first time" to the records
already and nothing refuses a telling that leaves them out. The earlier run
left both out of all ten.

**Step 4, `61b19cd`: a near copy is caught in the words as well as the
shape.** `play_shape` asks whether two tellings make the same moves in the
same order, and it kept two pairs that read the same aloud: "We passed from
Molina to MacAllister" and "We went from Molina to MacAllister" differ in one
word and come out with different shapes, because "passed" is a claim the
grammar reads and "went" is not. So the words are compared too, with every
player name folded to one token, the punctuation gone and the accents folded,
and `difflib`'s ratio over what is left. At 0.8 or higher the later candidate
is dropped.

| Pair, from the earlier run | Ratio |
| -------------------------- | ----: |
| 2022 `buddy_scored` 2 and 3 | 0.971 |
| 2022 `storyteller_neutral` 1 and 2 | 0.912 |
| 1986 `buddy_scored` 1 and 3 | 0.925 |
| 1986 `buddy_conceded` 1 and 3 | 0.867 |
| 1986 `buddy_conceded` 1 and `buddy_scored` 1 | 0.619 |

**Words and not characters, `autojunk` off.** Compared character by
character with the default, `SequenceMatcher` treats any character appearing
in more than one per cent of a sequence over 200 long as junk, which over a
250 character narration is the space and most of the alphabet: two 1986
candidates opening on the same clause scored 0.084 that way.

**Every same-slot pair of 1986 candidates in the document is a near copy at
this threshold**, which is why the pair this is tested against comes from two
different slots. The 1986 slots were not rerun and nothing was dropped from
them: a filter decides what a run keeps and does not reach back into a
document. If 1986 is ever rerun, two of its three slots come back with one
candidate rather than two.

**Step 5, the run: the three 2022 slots, 34,353 tokens of the 45,000
allowed.** Effort low, three candidates a slot, two retries allowed, eleven
calls and one IAM exchange. Four of the nine candidates were kept and 10,647
of the cap is unspent.

| This run, the three 2022 slots | |
| --- | ---: |
| calls sent | 11 |
| billed by watsonx | 34,353 |
| of it prompt | 29,832 |
| of it completion | 4,521 |
| the cap | 45,000 |
| unspent | 10,647 |
| candidates kept | 4 of 9 |
| slots with something in them | 3 of 3 |

The earlier rerun asked the same three slots for the same nine candidates
with no retries, sent nine calls and kept five, and its billed total is only
recorded for all six of its slots together (51,496), so the two runs' token
figures are not comparable and no comparison is printed here.

**2022 `buddy_conceded` has a candidate for the first time in three runs.**
It was empty on both of the earlier runs, and the two it dropped here were
dropped as near copies of the one it kept rather than as refusals.

**Every candidate of this run says the long ball and says first time**,
which is what rules 15 and 16 were for, and none of the four carries a
standalone "forward" after a name, which is what step 2 was for. "Álvarez
sent a long ball to MacAllister" is in all four.

**Five of the nine went on the near-copy filter and one on three refusals.**
The four near copies scored 0.97, 0.91, 0.85 and 0.83. The refusals are the
model being wrong and the check working: "Brilliant!" as an editorial
epithet, Álvarez's 36 yard ball up the pitch called a ball "back" twice, and
"We surged from our half" over a Molina who has no carry in the passage.

**The finding of this run: a hyphen gets a claim past the reading.** Three of
the four kept candidates say "first-time" or "left-foot" with a hyphen, and
`PHRASES` holds "first time" and "left foot" as two words, so neither is read
as a claim and neither is checked. Nothing false passed: the record is
`first_time` and `Left Foot`, so the words are true and the data agrees with
them. But the check did not verify them, and the storyteller candidates say
the foot that way and no other, so their body part is unchecked prose over a
line the app would label. The fix is the hyphenated spelling beside the
spaced one in `PHRASES`, which is a change to `app/narration_grammar.py` and
one test, and nothing was changed for it here.

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

## Next first action (two decisions about the reading, then the freeze)

**The six hero narrations are in the repo and four of them ground.** They are
in `scripts/authored_narrations.py`, written by the team and verified by the
grounding check, and the script reads all three rules over them:

```
.\.venv-prelude\Scripts\python.exe -I scripts\authored_narrations.py
```

It exits 1 today, because two of the six are refused, and both refusals are
the reading rather than the words. The Task 15 record above has the
coordinates; this is the decision each one needs.

| Slot | Refused for | What it would take |
| ---- | ----------- | ------------------ |
| 1986 `buddy_scored` | "the final third", read as being about the dribble past Beardsley | `_about` in `app/narration_grammar.py` may look at the move after a place when the move before it does not hold |
| 1986 `storyteller_neutral` | "on the right" and "on the edge of the box", read off Butcher's and Fenwick's own records | "beat" joins `PAST_MARKERS`, which makes it a dribble claim everywhere it is said |

**Both are Shawn's call**, because each widens what the check reads and
neither is a bug with one right answer. The first changes how a place finds
its action, which touches every zone claim in both passages. The second turns
a word that is unchecked prose today into a claim about a `Dribble` and a
`Dribbled Past` pair, which is the stricter and the more useful of the two.
Nothing was changed for either, and the two lines were not reworded.

**Then three things are owed, and they are steps 4, 5 and 6 of Task 15.**

1. **The freeze.** The six into `app/web/narrations.json`, each carrying its
   authorship, with a test that fails if a frozen narration has no authorship
   or stops grounding. `scripts/freeze_narrations.py` writes one narration per
   goal and that file holds one per goal, so this is a change to both. **The
   moment card is not to be touched**, which settles the shape: the card reads
   `text` for the goal and `scripts/check_match_copy.py` holds the card's
   inline copy to it, so the six go in beside that field rather than in place
   of it, or the card changes with them.
2. **The disclosure.** `README.md` says, in the present tense, that the six
   hero narrations were written by the team and verified by Prelude's
   grounding check against StatsBomb play data, and that the model pipeline
   and its runs are in `docs/narration_runs/`. It cannot say six until six
   ground. The label's own meaning is unchanged and `docs/GOVERNANCE.md`
   needs nothing.
3. **The recordings.** `scripts/tts_hero.py --confirm` with `--budget 3500`,
   Storyteller on `en-US_EmmaNatural` and Buddy on `en-US_EthanNatural`, six
   files under `app/web/assets/audio/`, and `hero.audio` filled per
   `voice_for` key. **Before any call, Shawn confirms the Text to Speech
   instance shows no November usage.** The script speaks one narration per
   match today, read from `narrations.json`, so six narrations and two voices
   is a change to it as well as to the frozen file.

**The six fit the budget with room.** 2,404 billed characters for the six
against the 3,500 `scripts/tts_hero.py --budget` allows, so 1,096 unspent:
1986 is 324 to 367 a slot and 2022 is 428 to 485.

**What Shawn listens for after the recordings**, which is the last line of
the task: Di María, Álvarez, MacAllister, Cuciuffo and Beardsley, and the
pacing, before anything else is tuned.

### The six fallback narrations are still in the repo, and they are not these

`scripts/fallback_narrations.py` holds the six Shawn kept from the first run
of 2026-11-05 and `docs/narration_runs/fallback_2026-11-05.md` is their
re-check. All six of those ground and none of them places the move, which is
what Task 14 built the places rule for; they are the earlier answer to the
same question and are kept because a run is never the only copy of a
narration.

### The candidate runs, and where they are

**No run was made in Task 15 and no watsonx call was sent.** The review
files outside the repo are as Task 14 left them:

| Where | What is in it |
| ----- | ------------- |
| `C:\Users\shawn\prelude-review\narrator_candidates_2026-11-05.md` | Task 14's one kept candidate (2022 `buddy_conceded`) and the carried 2022 Storyteller |
| `C:\Users\shawn\prelude-review\narrator_candidates_2026-11-05.before-task14-20261105T2027.md` | the zones run's eight, including the five 1986 ones Task 14's run replaced |

**Copy both aside before any rerun.** It is still not automated.

**The rerun command, if a slot is to be asked again.** A slot a run produces
replaces its older self and a slot it does not touch is carried across:

```
.\.venv-prelude\Scripts\python.exe -I scripts\narrator_candidates.py --confirm --match 3750191 --slot buddy_scored --reasoning-effort low --per-slot 3 --max-retries 2 --max-total-tokens 20000
```

`--plan` prints what it would spend and sends nothing; `--confirm` sends it.
A run now also refuses a grounded telling that does not open on a name, which
is rule 18 and `opener_missing`.

**The Caller has a style and no recording.** `hero.voice_for` sends no
listener to it, so there are six slots rather than eight. Its style is in
`app/goal_call_prompt.py` and its two reference narrations are in
`tests/test_reference_narrations.py`, so adding the recording later is a
change to `hero.voice_for` and not to the writing.


### Task 10's run: the ten candidates the fixes replaced

**The first run of 2026-11-05 billed 76,542 of its 80,000 and stopped on the
cap** in the 2022 `buddy_scored` slot, with ten candidates over five slots.
Shawn read those ten aloud, and Task 11 is what the reading found: one hole in
the check and three things the pipeline was doing to the output. The
candidates themselves are gone from the review file, which the rerun
overwrote; what they showed is in the Task 11 record.

### Task 9d: the eighteen candidates the curation replaced

**Task 9d was run end to end at `reasoning_effort` high and nothing was
frozen.** The eighteen are in
`C:\Users\shawn\prelude-review\narrator_candidates_2026-10-31.md`. Shawn read
them aloud on 2026-10-31 and the finding is what Task 10 is: they echo the
fact list, because the prompt handed over every recorded event.

**What that run cost.** About 817,000 tokens in all, of which 311,081 is
counted off watsonx's own `usage` object and the rest is estimated at the
14,473 tokens a call the counted runs averaged. The counting was added part
way through, which is why two of the four runs are an estimate:

| Run | Calls | Tokens |
| --- | ----: | -----: |
| the probes that measured what high effort needs | 9 | 65,038 counted |
| six slots, lost to a read timeout after one slot | 5 | about 72,000 |
| six slots, 16 of 18 kept | 30 | about 434,000 |
| the two `buddy_scored` slots again | 11 | 154,821 counted |
| the 2022 `buddy_scored` slot again | 6 | 91,222 counted |

**High effort against low, now that both have been run on this prompt.** Task
9d's eighteen at high cost about 817,000 tokens; Task 10's run at low billed
76,542 for twenty-six calls and stopped on a cap. The tellings at high were
not better, which was the open question at the end of Task 9d, and the
curation in `app/story_beats.py` is what changed the tellings rather than the
effort.

### Task 8: the candidate run Task 9 replaced

**Task 8 is run, nothing is frozen, and the freeze is one command away.** The
candidates are in `C:\Users\shawn\prelude-review\hero_candidates_2026-10-30.md`,
with the same data beside it as JSON. Both goals were rerun, so both are this
run's. Shawn picks one per goal and then:

```
.\.venv-prelude\Scripts\python.exe -I scripts\freeze_narrations.py --pick 3750191=3 --pick 3869685=3 --confirm
```

That path calls no model: the words already exist, so it reads them out of the
candidates document, re-runs the grounding check against `data/raw/`, and
writes `app/web/narrations.json` with the model that wrote them and which
candidate it was. Without `--confirm` it prints the pick and writes nothing.
It refuses a slot that is not in the file, a goal picked twice, a goal that is
not a hero, and a pick that leaves one hero unpicked. **The 1986 slots have
gaps: they are 1, 3 and 4, because slots 2 and 5 were refused.**

**Eight candidates, not ten: 1986 came back three of five.** Both of the two
that failed did so the same way, and it is the citation rather than the
sentence. The hero block prints the Beardsley step as "Diego Armando
Maradona, from facts 10, 11, 12: dribbled past Peter Beardsley", and the model
wrote the sentence citing `[10]` alone. Fact 10 is "Peter Beardsley (England)
was dribbled past", which names Beardsley and not Maradona, so his name is in
the buildup and not in the facts that sentence cited, and the check refuses it
correctly. Five of the six failed attempts are that; the sixth wrote no
citation tags at all, which is the failure
`app/narration_prompt.py::build_prompt` already describes as the harder one.

**Whether the prompt invites it cannot be told from ten generations.** The
same shortened citation is what the Task 7 prompt fix was aimed at, and that
rerun came back five of five; this one came back three of five at the same
temperature 0.8. The only change to the 1986 prompt since is one name
("Héctor Enrique" rather than "Héctor Adolfo Enrique"), which is not in any
sentence that failed. So it is either sampling or a prompt that still allows
the short citation, and the honest answer is that this run cannot say which.
Asking for one fact number per sentence, or restating that a step's sentence
cites every number printed for it, is the next thing to try, and it is a
prompt change rather than a check change.

**The 2022 goal came back five of five, all five naming all five players.**
That is the thing the Task 6 narration was short on: it named three of five
and left out Messi and Álvarez, and every candidate here names Molina,
MacAllister, Messi, Álvarez and Di María in order. They differ only in the
closing phrase and in whether a receipt is said as "received the ball" or
"received", a spread of 87 characters and 204 billed.

**Every candidate is grounded, carries one clock, ends on a sentence saying it
scored, and covers every key beat.** 1986: five of five beats, seven of the
eight recorded players, Peter Reid the one unnamed, which is right because
Reid only pressed and no fact pairs him with anything else. 2022: one of one
beat, five of five players.

**No candidate carries an unusual character.** `odd_characters` reports none
across all eight, after two of the previous run's candidates carried one. That
is not evidence the problem is gone: `app/plain_characters.py` now rewrites a
disguised space or hyphen as the model's text arrives in `app/narration.py`,
so a character that did arrive was made plain before the review file measured
anything. The review file no longer distinguishes "the model wrote none" from
"the model wrote one and it was fixed", which is a reporting loss taken
knowingly: the fix is worth more than the report, and recording what was
rewritten is a change to `Attempt` that this task did not ask for.

**Every pair fits the budget, so the price is not the thing to choose on.**
`scripts/tts_hero.py --budget` is 3,000 billed characters for the six
recordings. The cheapest pair is 1986 slot 3 with 2022 slot 3 at 2,688, and
the most expensive is 1986 slot 4 with 2022 slot 4 at 2,934. All fifteen
pairs are under 3,000, with between 66 and 312 characters to spare. The 1986
narrations run 1,473 to 1,515 billed and the 2022 ones 1,215 to 1,419.

**The 1986 narration still says "Diego Armando Maradona" six times, and the
data is why.** Task 8 was asked for recorded common names, and
`data/raw/lineups/3750191.json` records no `player_nickname` for him: the
field is null. So there is nothing shorter to say that the data says, and
`app/recorded_names.py` does not pick a surname out of a full name, because
that would be this repo's judgement about what a player is called rather than
a value read from the match. What 1986 did gain is "Héctor Enrique" for
"Héctor Adolfo Enrique", which is the one nickname in that buildup.

The 2022 goal is where the change lands: "Lionel Messi" for "Lionel Andrés
Messi Cuccittini", "Ángel Di María" for "Ángel Fabián Di María Hernández",
"Nahuel Molina" for "Nahuel Molina Lucero", "Alexis MacAllister" for "Alexis
Mac Allister". Julián Álvarez has none recorded and so is said in full.

**Still owed after the pick: the recordings.** The Text to Speech instance is
disabled above its Lite cap until November 1, so `scripts/tts_hero.py
--confirm` has not been sent and `hero.audio` is still `{}`. What to listen
for: a candidate that says "at 54:02" or "at 35:12" once still reads a colon
between two numbers aloud, which nothing here knows the sound of, and `di` in
"Di María" is still unheard.

**The vocabulary sweep has nothing to review after the pick, and that was
measured rather than assumed.** `scripts/check_vocabulary.py` reads the frozen
narrations, so a freeze changes the words it sweeps: "MacAllister" is a word
no narration has held before, and the full names that go ("Fabián",
"Hernández", "Cuccittini") take their words with them. Run with every one of
the eight candidates standing in for the frozen pair, the gate's own flagging
reports no unreviewed word either way, because a name has to carry two listed
CMU pronunciations to be flagged at all and none of these does. `di` is
already in the table, from the Task 6 narration.

### Task 7: the candidate run Task 8 replaced

**Task 7's candidates no longer exist.** Task 8 reran both goals, into the
same candidates document, so what the file holds is Task 8's eight and not
these. The reason for the rerun is in Task 8's record above: the names. What
is kept here is what the run measured, because the prompt fixes and the
prices it found are still true.

**Nothing was frozen then either**, and the freeze path is unchanged: it
reads a candidate out of the document, re-checks it against `data/raw/`, and
writes `app/web/narrations.json`. It refuses a slot that is not in the file,
a goal picked twice, a goal that is not a hero, and a pick that leaves one
hero unpicked, because freezing one of the two would leave one moment card
speaking a narration chosen on the evidence and the other speaking one chosen
before it. The slot numbers are the asked-for slots and have gaps.

**The 1986 goal was rerun with the fixed prompt and a length target, and it
went from two usable candidates to five.** Every one of the five is grounded,
eight sentences, one clock, ends on a sentence saying it scored, names seven of
the eight recorded players (all three who touched the ball, and the four
defenders beaten; Reid only pressed and no candidate names him, which is
right), and covers five of five key beats. None was dropped for its price.
`--match 3750191 --alongside 3869685=4` spent 12 generations of the 15 it was
allowed, plus one IAM exchange.

**They are five slots but two narrations.** Slots 1, 2 and 3 are one text of
447 characters at 1,458 billed, ending "Diego Armando Maradona shot and
scored". Slots 4 and 5 are one text of 466 characters at 1,503 billed, ending
"shot with his left foot and scored", which reaches the body part the earlier
1986 candidate never did. The length target is what converged them: asked for
about 450 characters, the model wrote the same telling over and over.

**Slot 5 carried a `NARROW NO-BREAK SPACE` (U+202F) inside "Terry Butcher",
which made slot 4 the one to pick of that pair.** It was the second invisible
character a candidate has arrived with, after the `NON-BREAKING HYPHEN` in the
run before it, and both passed `app/grounding.py` correctly: a narrow space is
whitespace, so the name either side of it still matched, and a hyphen is not a
name, an action, a clock or a number. `odd_characters` in
`scripts/hero_candidates.py` now reports any character that is neither plain
ASCII nor a letter, so the review file names them. It reports rather than
refuses: what may be labelled is `app/grounding.py`'s to say, and extending
its rules is a decision rather than a fix.

**The length target is 450 characters, and it is a price rather than a style.**
`HERO_TARGET_CHARACTERS` in `app/narration_prompt.py`, stated in the hero
prompt in characters and in words, with the reasoning on the constant: the
usable 1986 candidate before it came to 459 characters and 1,491 billed, and
the one that spelled every clock out in words came to 988 and 4,299, more than
the whole run may spend. `scripts/hero_candidates.py` is what enforces a
price, by dropping a grounded candidate whose recordings would not fit, since
nothing in a prompt can make a model count.

**What a pair now costs, and what it leaves for 2022.** The cheaper 1986 text
at 1,458 billed leaves 1,542 of the 3,000 budget for the other goal; the one
naming the left foot at 1,503 leaves 1,497. Both are comfortable: the five
2022 candidates of the first run came to between 1,488 and 1,605, so a 2022
rerun has room, though not unlimited room. Of those five, three fitted beside
the cheaper 1986 text and two fitted beside the longer one. That arithmetic is
a guide to what a rerun should aim at rather than a live option, because those
candidates no longer exist: see the mistake below.

**One mistake, and it cost the 2022 candidates.** The candidates document is
named by the day, and the 1986 rerun wrote that filename again, so the file
went from holding both goals to holding 1986 alone. The five 2022 candidates
in it are gone, and with them their `tagged_text`, which is the only copy of
the citations the model wrote and what a freeze re-reads before committing
anything. Their plain text survives in this file's history and in the session
report; the citations do not, and writing them by hand would make them this
repo's rather than the model's. So **freezing a 2022 narration now needs the
2022 goal rerun**, which is 15 generations, and the Task 6 narration it would
replace is still what `app/web/narrations.json` holds, so nothing is broken
while that waits.

`merged` in `scripts/hero_candidates.py` is why it cannot happen again: a
rerun carries across every goal it did not narrate, keeping that goal's own
provenance, and `tests/test_hero_candidates.py::TestMergingARerunIntoTheDocument`
holds it. A rerun of 2022 would therefore leave the 1986 five in place.

**`scripts/hero_candidates.py --refresh` remeasures without calling a model.**
The report has gained two columns since the first run (the narration's length,
and the unusual characters), and a review file written before a measurement
existed cannot be read against it. Refresh recomputes the price, the coverage
and the check from `data/raw/` for every candidate already written, and
refuses to rewrite the file if any of them has stopped passing.

**The 1986 run found a real prompt problem, and it is fixed.** Three of the
five slots in the first run failed all three attempts the same way: the model
wrote one sentence per defender in the form "Peter Beardsley was dribbled past
and Diego Armando Maradona carried the ball", and the check refuses it,
correctly, because no cited fact records a `Carry` involving Beardsley and
rule 4 asks for one action a line. The hero block was what invited it: a step
for the scorer printed as "dribbled, carried the ball" beside a beat naming
Beardsley. It now prints as "dribbled past Peter Beardsley", citing all three
facts, and a note under the step list says a dribble step is one sentence. The
rerun's five for five is that fix measured.

**The clock rule is fixed too.** It said no digits besides the one clock, and
one candidate obeyed by spelling every clock out in words instead: "at minute
fifty-four seconds two" on each of twelve sentences. Nothing in
`app/grounding.py` objects, since a clock in words carries no digits and makes
no number claim, so it passed, cost 4,299 billed, and carried the non-breaking
hyphen. The rule now says the clock is written as the fact writes it, digits
and colon, with that fact's own clock as the example, and refuses the time in
words anywhere. `app/grounding.py` is unchanged by either fix.

**The run cost 23 generations of the 30 allowed on the first run and 12 of 15
on the rerun**, plus one IAM exchange each: `openai/gpt-oss-120b` through the
chat endpoint at `reasoning_effort` low, decoding pinned to temperature 0.8,
top_p 0.9, top_k 40. The decoding is pinned because watsonx decodes greedily
unset, and five greedy candidates are one candidate five times.

**Still owed after the pick: the recordings.** The Text to Speech instance is
disabled above its Lite cap until November 1, so `scripts/tts_hero.py
--confirm` has not been sent and `hero.audio` is still `{}`. What to listen
for: a candidate that says "at 54:02" once still reads a colon between two
numbers aloud, which nothing here knows the sound of, and `di` in "Di Maria"
is still unheard.

**Task 7's brief, and the state it started from.**

**Bob task 13 is built and checked.** `4e61a10` renamed the id to `buddy` in
every live file; both written files pass `--check`, and the follow-up updated
the docs that cited the test names it renamed. `pytest -q` reports
`718 passed` and all five gates pass. It cost 21.07 Bobcoins, five times a
typical task, because a rename across 18 files is mostly reading: broad
mechanical edits are expensive for Bob, small targeted ones are cheap.

**The frozen narrations are grounded but not ready to record.** Read as audio,
the 2022 one names 4 of the 13 recorded events and leaves out Messi and
Álvarez; neither one says the shot scored; every sentence carries a clock; and
the 1986 one does not name Maradona until the last line. All four are prompt
choices, not grounding limits, and they are cheap to fix on watsonx before the
voice is spent. Task 7, briefed to Claude Code, asks for five grounded
candidates per goal with those fixed, for Shawn to choose from.

### Before Task 7: Bob task 13

**Bob task 13 in `docs/bob_brief.md` renames the persona id from `mate` to
`buddy`**, Shawn's call on 2026-10-30, made before the hero recordings exist
because their filenames are built from the id. Live code, data and tests
change; the past does not: `scripts/narration_eval.py`, `docs/narration_eval.md`,
this file's history and `bob_sessions/` keep "Mate" for the runs made under that
name. The docs that describe the current state are the follow-up's.
While it was briefed, every failure was in `tests/test_buddy_rename.py`.

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
.\.venv-prelude\Scripts\python.exe -I scripts\tts_hero.py --confirm
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
