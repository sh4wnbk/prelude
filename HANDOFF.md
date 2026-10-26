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
`tests/test_narration_provider.py` is 28 tests, and `tests/conftest.py`
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

**The suite.** `tests/test_event_feed.py::TestBuildup` is 13 tests. While the
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
| 1986 | 2H 48', ARG 0-0 ENG | 2H 55', ARG 2-0 ENG |
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

## Next first action (Phase 4, task 4)

**Measure the pass rate, then wire narration to a screen.** The prompt, the
grounding check and the pipeline are built. What nothing does yet is run
`app/narration.py` over the nine goals and write down how often the first
attempt is grounded. `pass_rate` is there for it, and
`Narrated.first_attempt_grounded` is the number it reports: retries must not be
counted, or the figure hides how often the model drifts.

`scripts/narrate_once.py` is one goal through a real model, so the loop over
nine is what is missing rather than the call. Two runs of it over the 1986
54:18 goal had no grounded first attempt, and the task 3b section records why,
so expect the measured rate on `granite4:micro` to be low and do not read that
as the prompt failing: every refusal in those runs was a real miscitation. The
comparison the rate is for is between models, which is what
`app/narration_config.py` holds the two watsonx candidates for.

What is in place:

| What | Where |
| ---- | ----- |
| The contract | `app/event_feed.py`, shapes and protocol |
| The implementation | `app/statsbomb_event_feed.py`, class `StatsBombEventFeed` |
| The tests | `tests/test_event_feed.py`, 27 tests, all passing |
| The buildup tests | the 13 in `tests/test_event_feed.py::TestBuildup` |
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
