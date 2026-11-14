# The Plan, as agreed with Shawn

Moved out of `HANDOFF.md` unchanged, when that file was restructured as a
running snapshot plus the latest record. **This is the record as it was written
when each task closed, not a description of the repo today**: present tense in
it means the day of the task. `HANDOFF.md` carries the current state, and
`docs/history/README.md` says where each decision from here now lives.

The per-task plan entries from Task 3d onward, and the Phase 5, 6 and 7 outlines. Everything in it is built except the Phase 7 bullets, which `HANDOFF.md` carries under Next first action.

---

## Plan

Tasks 3d through Phase 7, as agreed with Shawn, copied here so a fresh session
has the whole arc rather than one task at a time.

**Everything in this section is planned work except where a task is marked
done.** Tasks 3d, 4a, 4b, 4c, 5, 6a, 6b, 6c, 6d, 7, 8 and 9 are built, and so
are Bob's tasks through task 13; the pick, the freeze, the disclosure and the
recordings are done, so what is left is Shawn's listening pass over the six
and then Phases 6 and 7. Paths a doc
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

**The first bullet was rewritten on 2026-11-07, when Shawn settled what the
hosted part is.** It was a backend holding the IBM keys with rate limiting, so
judges would get live, varied narration. It is a read-only API instead, which
holds no keys and makes no paid call, and the saved audio is what a judge
hears whether or not it is up. Task 17 above is the record.

- Claude Code: a small hosted read-only API on Render's free tier, so watsonx
  Orchestrate has a stable public URL to call (done, Task 17, `app/api.py` and
  `render.yaml`; nothing is deployed yet).
- Claude Code: a keepalive so a judge never hits a cold start (done,
  `.github/workflows/keepalive.yml`; it waits on the deployed URL).
- Shawn: create the Render service and hand the URL back. The checklist is
  under Task 17 above.
- Bob: write the OpenAPI tool spec for the endpoint (the YAML the lab guide's
  exercise uses).
- Shawn: recreate the prelude agent in Orchestrate and import the spec as its
  tool. Optionally host the orchestrator's routing there.
- Claude Code: check the spec against the live endpoint, turn the keepalive
  schedule on or leave it for the public repo, and finish
  `docs/IBM_STACK.md`.

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
