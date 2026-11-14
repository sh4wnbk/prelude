# Prelude review for IBM Bob. Ask mode only. Do not create, edit, or delete any file.
Do not open, read, or search for any .env file or anything outside this repo.
Do the tasks in order. Answer each one under its own heading in this chat.

Context
Prelude is an MVP for the IBM SkillsBuild AI Experiential Learning Lab, Track 3
(Fan-Centric Sports and Entertainment). A fan at a live match steps away from
their seat; when a goal is scored, Prelude narrates the buildup to them in audio,
built from StatsBomb play data and checked claim by claim before it carries the
label "Verified from play data". Judges score four axes: completeness and
feasibility, creativity and innovation, design and usability, effectiveness and
efficiency. The lab's reference MVP is an AI agent shown end to end: one user,
one problem, one outcome; real data; visible reasoning; a metric that proves value.

Read first: README.md, docs/GOVERNANCE.md, docs/VOICE.md (skim), app/orchestrator.py,
app/personas.py, app/grounding.py (skim), app/narration.py, docs/narration_eval.md,
docs/orchestrate_agent.md, orchestrate/prelude_tools.yaml, app/web/ (the screens).

Task 1: The name
- Does "Prelude" tell a fan what the app does? Give one reason it works and one it doesn't.
- Does it hold up beside the tagline "Leave your seat. Stay in the game."?
- Do not propose a new name unless the current one fails on both counts.
Exit: a verdict of keep, keep with a change, or replace, with the reasons.

Task 2: Is it agentic?
- List each part of the system that makes a decision. For each, say whether an AI
  model decides or fixed rules decide, citing the file and function.
- Map the system onto the lab's demo order: trigger, reasoning, output, loop,
  guardrails, metric. Mark each step as present, partial, or missing, with evidence.
- Name the single change that would most strengthen the agentic story without new inputs.
  Prelude has exactly three inputs (play data, GPS presence, audio narration); do not
  propose a fourth.
Exit: a table of decision points, a six-row demo-order table, one recommendation.

Task 3: The judge's four questions
Answer each from the repo, citing files:
- Does it actually work?
- How do you measure it?
- Why is the AI necessary? (If a simple rule could do it, say so.)
- What if it's wrong?
Exit: four answers, each with the evidence a judge could check.

Task 4: Score it
- Score each of the four judging axes from 1 to 5, with the evidence for each score.
- Name the three weakest points a judge would find, most serious first.
Exit: four scores, three weaknesses.

Task 5: Claims
- Find any line in the screens, README, or docs that promises more than the code does.
- Quote the line, name the file, say what the code actually does.
Exit: a list of overclaims, or "none found".

When you finish, print this reminder: "Screenshot the task summary and export the
task markdown into bob_sessions/."

---

**Status:** active  **Date:** 2026-11-14

---

### 👤 User

Prelude review for IBM Bob. Ask mode only. Do not create, edit, or delete any file.
Do not open, read, or search for any .env file or anything outside this repo.
Do the tasks in order. Answer each one under its own heading in this chat.

Context
Prelude is an MVP for the IBM SkillsBuild AI Experiential Learning Lab, Track 3
(Fan-Centric Sports and Entertainment). A fan at a live match steps away from
their seat; when a goal is scored, Prelude narrates the buildup to them in audio,
built from StatsBomb play data and checked claim by claim before it carries the
label "Verified from play data". Judges score four axes: completeness and
feasibility, creativity and innovation, design and usability, effectiveness and
efficiency. The lab's reference MVP is an AI agent shown end to end: one user,
one problem, one outcome; real data; visible reasoning; a metric that proves value.

Read first: README.md, docs/GOVERNANCE.md, docs/VOICE.md (skim), app/orchestrator.py,
app/personas.py, app/grounding.py (skim), app/narration.py, docs/narration_eval.md,
docs/orchestrate_agent.md, orchestrate/prelude_tools.yaml, app/web/ (the screens).

Task 1: The name
- Does "Prelude" tell a fan what the app does? Give one reason it works and one it doesn't.
- Does it hold up beside the tagline "Leave your seat. Stay in the game."?
- Do not propose a new name unless the current one fails on both counts.
Exit: a verdict of keep, keep with a change, or replace, with the reasons.

Task 2: Is it agentic?
- List each part of the system that makes a decision. For each, say whether an AI
  model decides or fixed rules decide, citing the file and function.
- Map the system onto the lab's demo order: trigger, reasoning, output, loop,
  guardrails, metric. Mark each step as present, partial, or missing, with evidence.
- Name the single change that would most strengthen the agentic story without new inputs.
  Prelude has exactly three inputs (play data, GPS presence, audio narration); do not
  propose a fourth.
Exit: a table of decision points, a six-row demo-order table, one recommendation.

Task 3: The judge's four questions
Answer each from the repo, citing files:
- Does it actually work?
- How do you measure it?
- Why is the AI necessary? (If a simple rule could do it, say so.)
- What if it's wrong?
Exit: four answers, each with the evidence a judge could check.

Task 4: Score it
- Score each of the four judging axes from 1 to 5, with the evidence for each score.
- Name the three weakest points a judge would find, most serious first.
Exit: four scores, three weaknesses.

Task 5: Claims
- Find any line in the screens, README, or docs that promises more than the code does.
- Quote the line, name the file, say what the code actually does.
Exit: a list of overclaims, or "none found".

When you finish, print this reminder: "Screenshot the task summary and export the
task markdown into bob_sessions/."

---

### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — 
[-] Read core files: README.md, docs/GOVERNANCE.md, docs/VOICE.md, app/orchestrator.py, app/personas.py, app/grounding.py, app/narration.py, docs/narration_eval.md, docs/orchestrate_agent.md, orchestrate/prelude_tools.yaml, app/web/
[ ] Task 1: The name
[ ] Task 2: Is it agentic?
[ ] Task 3: The judge's four questions
[ ] Task 4: Score it
[ ] Task 5: Claims


### 🤖 Assistant

> 🔧 called: read_file, list_files



> 🔧 **list_files** — c:\Users\shawn\Documents\src\prelude

> 🔧 **read_file** — c:\Users\shawn\Documents\src\prelude\README.md

### 🤖 Assistant

> 🔧 called: read_file, read_file



> 🔧 **read_file** — governance rules, what is enforced, guardrails

> 🔧 **read_file** — voice guide, narration style, personas

### 🤖 Assistant

> 🔧 called: read_file, read_file



> 🔧 **read_file** — orchestrator logic, decisions made, what it computes, persona selection, header

> 🔧 **read_file** — personas definitions, ids, names, voices, partisan flag

### 🤖 Assistant

> 🔧 called: read_file, read_file



> 🔧 **read_file** — narration pipeline, generate, check, retry, fallback, label assignment

> 🔧 **read_file** — grounding check logic, how it decides, what it refuses, claim verification

### 🤖 Assistant

> 🔧 called: read_file, read_file



> 🔧 **read_file** — narration evaluation, pass rates, metrics, model performance

> 🔧 **read_file** — orchestrate agent workflow, what it does, agentic loop, trigger, reasoning steps

### 🤖 Assistant

> 🔧 called: read_file, list_files



> 🔧 **list_files** — c:\Users\shawn\Documents\src\prelude\app\web

> 🔧 **read_file** — prelude tools, API endpoints, tool definitions

### 🤖 Assistant

> 🔧 called: read_file, read_file



> 🔧 **read_file** — what the screens say, app copy, tagline, branding, feature claims

> 🔧 **read_file** — moment card screen, what it shows, narration display, grounding label, audio player

### 🤖 Assistant

> 🔧 called: read_file, read_file



> 🔧 **read_file** — live seated screen, what it shows, goal alert, GPS presence, trigger

> 🔧 **read_file** — IBM stack, what IBM services are used, what is built vs planned

### 🤖 Assistant

> 🔧 called: read_file, read_file



> 🔧 **read_file** — narrator names, profile descriptions shown to fan

> 🔧 **read_file** — HANDOFF notes, what is next, what is not built

### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — 
[x] Read core files: README.md, docs/GOVERNANCE.md, docs/VOICE.md, app/orchestrator.py, app/personas.py, app/grounding.py, app/narration.py, docs/narration_eval.md, docs/orchestrate_agent.md, orchestrate/prelude_tools.yaml, app/web/
[-] Task 1: The name
[ ] Task 2: Is it agentic?
[ ] Task 3: The judge's four questions
[ ] Task 4: Score it
[ ] Task 5: Claims


### 🤖 Assistant

> 🔧 called: update_todo_list

---

## Task 1: The name

**Does "Prelude" tell a fan what the app does?**

The word means "an action or event serving as an introduction to something more important; the opening movement of a piece of music." Applied to football: a goal is the event, and Prelude narrates the *buildup* — the phase of play that preceded it. That correspondence is precise and intentional; the README subtitle confirms it: *"Prelude narrates a football moment in audio, saying only what the play data can prove."*

**One reason it works:** The word names exactly the temporal structure the app addresses. A fan misses a goal; what they receive is the narrative of the *play that led to it* — the pre-lude, the thing that came before. For anyone who thinks about it for a second, that is a good fit.

**One reason it doesn't:** A fan who has never read the tagline picks up the phone and sees "PRELUDE" at the top of the screen. They have no immediate frame of reference for what it *does*. The word is abstract and arts-adjacent; it does not signal "sports audio app" on its face. Discoverability and first-impression clarity suffer.

**Does it hold up beside the tagline "Leave your seat. Stay in the game."?**

Yes, it does — and the tagline carries the weight the name cannot. "Leave your seat" is the action, "Stay in the game" is the promise, and "Prelude" positions the product as the narrative bridge between the two. The tagline is functional enough that the name does not need to do the utility work. The pairing is coherent.

**Verdict: Keep.** The name works within its frame, the tagline compensates for the clarity gap, and the word's musical-structural connotation (the buildup before the climax) maps precisely onto what the app delivers. The case against it is weak unless the app is ever marketed without the tagline.

---

> 🔧 **update_todo_list** — 
[x] Read core files: README.md, docs/GOVERNANCE.md, docs/VOICE.md, app/orchestrator.py, app/personas.py, app/grounding.py, app/narration.py, docs/narration_eval.md, docs/orchestrate_agent.md, orchestrate/prelude_tools.yaml, app/web/
[x] Task 1: The name
[-] Task 2: Is it agentic?
[ ] Task 3: The judge's four questions
[ ] Task 4: Score it
[ ] Task 5: Claims


### 🤖 Assistant

> 🔧 called: update_todo_list

---

## Task 2: Is it agentic?

### Decision points table

| # | Decision | AI or fixed rules | File · Function |
|---|----------|-------------------|-----------------|
| 1 | Is it today or tonight? | Fixed rules (time comparison) | [`app/orchestrator.py`](app/orchestrator.py) · [`greeting_word()`](app/orchestrator.py:43) |
| 2 | Which phase of the match (early/middle/late)? | Fixed rules (ratio thresholds) | [`app/orchestrator.py`](app/orchestrator.py) · [`phase()`](app/orchestrator.py:54) |
| 3 | What did the goal do to the score? (extend / take lead / overtake / draw level / close gap) | Fixed rules (score comparison) | [`app/orchestrator.py`](app/orchestrator.py) · [`transition()`](app/orchestrator.py:102) |
| 4 | Which persona to assign by default? (Buddy vs Storyteller) | Fixed rules (listener allegiance) | [`app/orchestrator.py`](app/orchestrator.py) · [`default_persona()`](app/orchestrator.py:149) |
| 5 | Is the fan ahead, level or behind? | Fixed rules (score comparison) | [`app/orchestrator.py`](app/orchestrator.py) · [`score_state()`](app/orchestrator.py:71) |
| 6 | Generate a narration from the buildup facts | **AI model** (watsonx `openai/gpt-oss-120b` or local `granite4:micro`) | [`app/narration.py`](app/narration.py) · [`narrate()`](app/narration.py:158) → [`app/narration_provider.py`](app/narration_provider.py) |
| 7 | Does the narration's every claim trace back to the data? (grounded or not) | Fixed rules (regex grammar + lookup tables) | [`app/grounding.py`](app/grounding.py) · [`check()`](app/grounding.py:841) |
| 8 | Retry, fall back to template, or return? | Fixed rules (loop up to `MAX_RETRIES=2`, then template) | [`app/narration.py`](app/narration.py) · [`narrate()`](app/narration.py:255-307) |
| 9 | Which delivery rate/pitch to use? | Fixed rules (table lookup by persona × situation) | [`app/delivery.py`](app/delivery.py) |
| 10 | Watsonx Orchestrate agent: map fan's natural-language match reference to a match id | **AI model** (Orchestrate-hosted LLM, model fixed by IBM lab admins) | [`docs/orchestrate_agent.md`](docs/orchestrate_agent.md) — instructions block |
| 11 | Watsonx Orchestrate agent: determine which tool to call and with what `listener` value | **AI model** | Same agent, rules 6–8 of the instructions |
| 12 | Does a word in the spoken text need a pronunciation override? | Fixed rules (lookup table) | [`app/pronunciation.py`](app/pronunciation.py) · `for_speech()` |

**Summary:** Two AI decisions exist — the LLM that writes narration prose (decision 6) and the Orchestrate agent that interprets the fan's intent (decisions 10–11). Every other decision is deterministic code.

---

### Six-row demo-order mapping

| Demo step | Present / Partial / Missing | Evidence |
|-----------|----|----|
| **Trigger** — a signal that an event happened | **Partial** | In the demo the fan presses "HEADING OUT" manually ([`prelude_02_live_seated.html`](app/web/prelude_02_live_seated.html:73)), which advances the internal clock. The trigger is the fan's own action, not an automated event-detection signal. GPS presence is listed as an input in `CLAUDE.md` but `README.md` explicitly says "No GPS" at this commit. The EventFeed module detects moments from historical data (`app/statsbomb_event_feed.py`), which shows the detection logic, but nothing wires a live goal event to the screen. |
| **Reasoning** — the AI works through the problem | **Present** | `app/narration.py` calls the LLM via `app/narration_provider.py`, receives generated prose, and `app/grounding.py` applies claim-by-claim reasoning (104 test-covered rules) to accept or reject it. The Orchestrate agent reasons over its tools to map a fan's question to a match id and listener type. |
| **Output** — a result the user receives | **Present** | The moment card shows the frozen narration text with the "Verified from play data" label and plays the IBM TTS recording. The Orchestrate agent returns the narration text word-for-word. Both are real, working outputs in the demo. |
| **Loop** — the agent acts, observes, and can act again | **Partial** | Within narration: generate → check → retry up to twice → fallback, in `narrate()`. That is a loop over attempts. At the user-session level there is no loop: the demo is one moment, one trigger, one narration. The Orchestrate agent supports multi-turn conversation (ask "who are you with?" then call `/buildup`) but only across two matches with frozen narrations. No persistent loop monitors new events. |
| **Guardrails** — constraints that bound output | **Present** | The grounding check in [`app/grounding.py`](app/grounding.py) is an extensive, tested guardrail: it refuses invented names, wrong clocks, present-tense verbs, verdict nicknames, em dashes, first-person for wrong persona, and more (104 tests). The agent instructions carry 11 explicit rules against paraphrasing, label misuse, and asking for internal IDs. `scripts/scan_copy.py` guards screen copy. These are some of the strongest guardrails in any submitted MVP. |
| **Metric** — a number that proves value | **Partial** | First-attempt grounding pass rate is defined and measured: 81% across 27 narrations on the development model (`docs/narration_eval.md`), 33/33 on `openai/gpt-oss-120b` (Task 4b). Coverage of key beats is also measured. However, neither metric is computed at runtime and shown to a judge; both live in development reports. `Narrated.first_attempt_grounded` exists as a property but no screen displays it. |

---

### Single recommendation

**Wire the grounding check verdict to the moment card at demo time.**

The app already has everything it needs: `Narrated.first_attempt_grounded`, `Narrated.failure_log`, and the `labelled` flag are all computed by `narrate()` in `app/narration.py`. Surfacing even one number on the moment card — e.g. "first-attempt pass: yes / no, 3 retries" — would turn a development metric into a live, visible demonstration of AI reasoning and self-correction. This uses only the three existing inputs and no new data sources. It converts the "metric: partial" to "metric: present" and directly answers "how do you measure it?" in the demo itself.

---

> 🔧 **update_todo_list** — 
[x] Read core files: README.md, docs/GOVERNANCE.md, docs/VOICE.md, app/orchestrator.py, app/personas.py, app/grounding.py, app/narration.py, docs/narration_eval.md, docs/orchestrate_agent.md, orchestrate/prelude_tools.yaml, app/web/
[x] Task 1: The name
[x] Task 2: Is it agentic?
[-] Task 3: The judge's four questions
[ ] Task 4: Score it
[ ] Task 5: Claims


### 🤖 Assistant

> 🔧 called: update_todo_list

---

## Task 3: The judge's four questions

### Does it actually work?

**Yes, with clearly stated limits.**

What demonstrably works at this commit (all from [`README.md` Capability Honesty](README.md:87-433)):

- Seven screens navigate correctly, including QR scan and manual entry.
- The moment card loads the frozen narration for the listener's slot from [`app/web/narrations.json`](app/web/narrations.json) and plays the corresponding MP3 recording. The play button, scrubber, timer and waveform visualiser all function.
- The narration pipeline (`app/narration.py`) generates text via an LLM, checks every claim via `app/grounding.py`, retries up to twice, and falls back to a template — with no ungrounded text ever returned. All 31 tests in `tests/test_narration.py` pass.
- The grounding check (`app/grounding.py`) has 104 tests, all passing.
- IBM Watson TTS synthesised the six recordings; they are committed and serve.
- The hosted REST API (`app/api.py`) is live at `https://prelude-api.onrender.com`; `/health`, `/moments`, `/buildup` all respond. 92 tests pass.
- The watsonx Orchestrate agent was live-tested on 2026-11-07, and the two failures found (float serialisation of match ids, truncated narration) were diagnosed and fixed ([`docs/orchestrate_agent.md`](docs/orchestrate_agent.md:14-116)).
- 1,059+ tests pass in the unit suite (`tests/`) with no network calls.

What does **not** work at this commit: GPS presence detection (not built), live goal event triggering (not wired), narration for any goal other than the two hero goals, the EventFeed not connected to the screens.

The demo's honest position is stated in [`README.md`](README.md:40-43): "Nothing is live. The demo replays StatsBomb historical data."

---

### How do you measure it?

**Two measurements exist and are documented; neither surfaces in the live demo.**

**First-attempt grounding pass rate** ([`app/narration.py`](app/narration.py:139)·[`first_attempt_grounded`](app/narration.py:139)): The rate at which the LLM's first attempt passes `app/grounding.py` without a retry. Measured results:
- `granite4:micro` (development): **22 of 27** (81%) — [`docs/narration_eval.md`](docs/narration_eval.md:41)
- `openai/gpt-oss-120b` (watsonx): **33 of 33** (100%) on the comparison run — [`docs/IBM_STACK.md`](docs/IBM_STACK.md:183)

**Coverage of key beats**: The share of key narrative beats (dribbles past defenders, fouls, the shot) the narration mentions. At Task 4a, first-attempt grounded narrations covered 45% of key beats on complex goals; after adding beat prompting (Task 4c), 95% — [`docs/narration_eval.md`](docs/narration_eval.md:84).

The `pass_rate()` function in [`app/narration.py`](app/narration.py:332) computes this programmatically. `scripts/narration_eval.py` runs the full measurement and writes [`docs/narration_eval.md`](docs/narration_eval.md). `scripts/check_match_copy.py` and `scripts/scan_copy.py` gate static copy accuracy.

The gap: both metrics are offline development measurements. No dashboard, no runtime display, no judging-visible number. A judge must run a script or read a markdown file.

---

### Why is the AI necessary?

**For the narration, the AI is genuinely necessary. For most other decisions, it is not.**

The core value of Prelude is producing *natural language narration* of a goal buildup — a paragraph of prose that reads event records as a story, in a voice calibrated to whether your team scored or conceded. No deterministic rule can write that prose: `app/narration_prompt.py` builds a numbered list of plain past-tense facts from the event records, and what the LLM must do is *select*, *order*, *phrase*, and *connect* those facts into fluent, varied English sentences. The fallback template in `app/narration_prompt.py` (one sentence per fact) demonstrates exactly what the non-AI version produces — it passes the grounding check but it is not narration, it is a list read aloud. The 104-rule grounding check (`app/grounding.py`) then verifies the AI's output against the source data.

For the Orchestrate agent: the AI's role is to map informal fan language ("the one Messi won", "the 86 quarter final") to a structured API call. A rule-based approach would require exhaustively enumerating every fan phrasing in advance. An LLM handles open-ended natural language matching, which is precisely the right tool.

For everything else — greeting word, phase, score transition, delivery table, persona default — a simple rule does it, and that is what the code uses. This is well-engineered: AI is applied where it adds value and rules are used where they are sufficient.

---

### What if it's wrong?

**The system has layered defences against different failure modes.**

**Wrong narration (hallucination or misdescription):** `app/grounding.py` refuses it. A narration with one unsupported claim — an invented name, a wrong action, a player paired with an action no cited fact records, a present-tense verb — fails whole. The pipeline retries up to twice, then falls back to the template. Nothing ungrounded ever reaches a fan. The label "Verified from play data" is applied only by `app/narration.py` and only on a passing check; `scripts/scan_copy.py` ensures no screen can display it outside that context.

**Wrong model output / LLM refusal:** `AnsweredWithoutContent` in `app/narration_provider.py` catches a response with no narration text; that attempt is logged and the pipeline retries.

**Template fallback is wrong:** If even the template fails the grounding check, `narrate()` raises `NarrationNotGrounded` — explicitly refusing to voice anything rather than returning something unverified ([`app/narration.py`](app/narration.py:302-306)).

**Stale screen copy:** `scripts/check_match_copy.py` checks every name, minute, score and count in the screens against `data/raw/`; `scripts/scan_copy.py` checks for banned copy and misplaced labels. Both exit non-zero on any failure.

**Orchestrate agent paraphrases or abbreviates the narration:** Rules 1–4 in the agent instructions prohibit it; `tests/test_orchestrate_agent.py` (40 tests) holds those rules.

**Data incorrect:** StatsBomb open data is the source of record. No inference, no memory, no secondary source is permitted by `CLAUDE.md`'s three-input rule.

The main unguarded failure mode is a fan receiving the template narration (a bare recitation of events, not a story) without knowing they received a fallback. The app does not currently distinguish template from model output in the UI.

---

> 🔧 **update_todo_list** — 
[x] Read core files: README.md, docs/GOVERNANCE.md, docs/VOICE.md, app/orchestrator.py, app/personas.py, app/grounding.py, app/narration.py, docs/narration_eval.md, docs/orchestrate_agent.md, orchestrate/prelude_tools.yaml, app/web/
[x] Task 1: The name
[x] Task 2: Is it agentic?
[x] Task 3: The judge's four questions
[-] Task 4: Score it
[ ] Task 5: Claims


### 🤖 Assistant

> 🔧 called: update_todo_list

---

## Task 4: Score it

### Four axes, 1–5

| Axis | Score | Evidence |
|------|-------|----------|
| **Completeness and feasibility** | **3 / 5** | The pipeline from play data → LLM narration → grounding check → TTS is completely built and tested. The API is deployed and the Orchestrate agent is wired and live-tested. What is not built: GPS presence, live event triggering, narration for any goal other than the two hero goals, EventFeed-to-screen wiring. The README says this outright: "What nothing does yet is measure how often a first attempt is grounded across the nine goals... Nothing wires the EventFeed to the screens yet." A judge following the demo sees one moment, two matches, and a manually-triggered transition. The feasibility of the full loop is argued but not demonstrated end to end. |
| **Creativity and innovation** | **4 / 5** | The claim-by-claim grounding check is a genuinely novel element: a 104-rule verifier that reads AI output against structured event data, sentence by sentence, before any copy reaches a user. The listener-side narration variation (Buddy scored / Buddy conceded / Storyteller neutral) is a creative design decision. The factored voice-separation — same prose text, differentiated purely through TTS delivery parameters — solves a real problem the evaluation data revealed (text registers did not separate across personas). The Watson TTS probe methodology (measure first, then pick values by ear) is disciplined. The Orchestrate agent's verbatim-quote rule, backed by test, is an innovative approach to guardrailing an LLM against rewrites. The idea itself (audio narration of the buildup for a fan who stepped away) is original. Loss of one point: Caller voice has no recordings, the loop is not live, and "step away" is simulated by a button press. |
| **Design and usability** | **4 / 5** | Seven screens, navigable, QR-scan onboarding, waveform scrubber, keyboard shortcuts, 500 ms audio padding for iPhone wake delay, ARIA labels, full viewport safety areas. The moment card is production-quality. The Profile tab is explicitly disabled rather than faked. The design system is coherent (Hanken Grotesk + Material Symbols, amber primary on dark surface). The "HEADING OUT" button is a natural gesture. Loss of one point: the "LIVE AUDIO SYNC" button on the moment card does nothing (shows "SYNCED" for 1.8s and resets — [`prelude_03_moment_card.html`](app/web/prelude_03_moment_card.html:126-132)); the "AT VENUE · GPS" badge on the Live screen asserts GPS that does not exist; the waveform bars on the Moments list are static fixtures ([`README.md`](README.md:451-453)). |
| **Effectiveness and efficiency** | **3 / 5** | The core effectiveness claim — narration that is verified against the data before it reaches a fan — is real and the mechanism is rigorous. The metric (first-attempt pass rate) is defined and measured in development, but it does not appear in the demo. The TTS pipeline is efficient: six recordings were bought once and shipped as committed files, so runtime cost is zero. The API is deployed and cold-start is managed with a keepalive. Loss of two points: the metric is not visible to a judge during the demo; the system does not demonstrate itself working in real time (all narrations are frozen, all events are historical, the trigger is manual). The judges can be told the system is effective, but they cannot watch it being effective. |

---

### Three weakest points, most serious first

**1. The end-to-end loop is never demonstrated.**
The fan scenario is: step away → goal scored → app narrates the buildup. None of that is live. The trigger is a manual button press. The goal is a known historical event. The narration was written and frozen in advance and is not generated at demo time. The EventFeed is not connected to the screens. A judge watching the demo does not see an AI agent respond to an event; they see a playback system with a manually triggered screen transition. This is the gap between the concept and the demo that most directly affects the "completeness and feasibility" score.

**2. The metric is invisible to the judge.**
"First-attempt grounding pass rate" is the right metric — it measures exactly whether the AI is doing its job. It is computed by real code, with real data, producing real results (81% on development model, 100% on the watsonx model selected for production). But a judge must run `scripts/narration_eval.py` or read `docs/narration_eval.md` to find it. Nothing on any screen shows it. The "Verified from play data" label appears on the moment card, but that is a binary outcome, not the probability distribution a judge wants to see. This directly weakens the "effectiveness and efficiency" score.

**3. Two UI elements promise capabilities that do not exist.**
The "AT VENUE · GPS" badge on [`prelude_02_live_seated.html`](app/web/prelude_02_live_seated.html:9) states GPS is active when no GPS code exists in the repo. The "LIVE AUDIO SYNC" button on [`prelude_03_moment_card.html`](app/web/prelude_03_moment_card.html:115) flashes "SYNCED" and does nothing. A judge who taps the sync button or notes the GPS badge will find that neither does what it implies. These are not errors the codebase is unaware of — [`README.md`](README.md:455-456) acknowledges "No GPS" — but the UI does not communicate this to a judge who has not read the README.

---

> 🔧 **update_todo_list** — 
[x] Read core files: README.md, docs/GOVERNANCE.md, docs/VOICE.md, app/orchestrator.py, app/personas.py, app/grounding.py, app/narration.py, docs/narration_eval.md, docs/orchestrate_agent.md, orchestrate/prelude_tools.yaml, app/web/
[x] Task 1: The name
[x] Task 2: Is it agentic?
[x] Task 3: The judge's four questions
[x] Task 4: Score it
[-] Task 5: Claims


### 🤖 Assistant

> 🔧 called: update_todo_list

---

## Task 5: Claims

Three overclaims found. All three are in the UI; the README, Python source, and docs are honest about their own limits.

---

**Overclaim 1 — GPS is active when it is not**

> `AT VENUE · GPS`

File: [`app/web/prelude_02_live_seated.html`](app/web/prelude_02_live_seated.html:9), status badge in the header area of the Live Seated screen.

What the code actually does: There is no GPS code in the repo. [`README.md`](README.md:455) states explicitly: "GPS presence handling — Not built yet." `docs/GOVERNANCE.md` says "GPS presence is whether tracking exists for a match, and no code in this repo reads or decides it yet." The badge asserts a live GPS fix that the application has no mechanism to obtain or verify.

---

**Overclaim 2 — "LIVE AUDIO SYNC" implies real-time synchronisation**

> `LIVE AUDIO SYNC` (button, moment card)

File: [`app/web/prelude_03_moment_card.html`](app/web/prelude_03_moment_card.html:115-118), secondary actions deck.

What the code actually does: Tapping the button changes its label to "SYNCED" for 1,800 ms, then resets to the original ([`prelude_03_moment_card.html`](app/web/prelude_03_moment_card.html:126-132)). No network request is made, no audio stream is contacted, no synchronisation of any kind occurs. It is a visual animation with no backing function.

---

**Overclaim 3 — "Play data connected · AI narration ready" on the event picker**

> `Play data connected · AI narration ready`

File: [`app/web/prelude_01_picker.html`](app/web/prelude_01_picker.html:33), repeated for both match cards (lines 33 and 46).

What the code actually does: This is static text rendered unconditionally for both cards. No connection to a data feed is made. No readiness check is performed. The app serves pre-frozen historical data and pre-recorded audio. When the fan presses "CONFIRM EVENT", the button label cycles through "Synchronizing Play Data..." → "Connected to Venue Feed" via a `setTimeout` with no actual network activity ([`prelude_01_picker.html`](app/web/prelude_01_picker.html:144-154)). Both states are theatrical. The README confirms: "Nothing is live."

---

*Note: The confirmation button animation ("Synchronizing Play Data..." then "Connected to Venue Feed") could be considered a fourth overclaim — it simulates a live data connection with no backing action. It is a subset of Overclaim 3 and does not appear on its own in the README's honesty section.*

---

> 🔧 **update_todo_list** — 
[x] Read core files: README.md, docs/GOVERNANCE.md, docs/VOICE.md, app/orchestrator.py, app/personas.py, app/grounding.py, app/narration.py, docs/narration_eval.md, docs/orchestrate_agent.md, orchestrate/prelude_tools.yaml, app/web/
[x] Task 1: The name
[x] Task 2: Is it agentic?
[x] Task 3: The judge's four questions
[x] Task 4: Score it
[x] Task 5: Claims


### 🤖 Assistant

---

Screenshot the task summary and export the task markdown into `bob_sessions/`.