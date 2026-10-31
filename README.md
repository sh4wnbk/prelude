# Prelude

Prelude narrates a football moment in audio, saying only what the play data can prove.

**Live demo: https://sh4wnbk.github.io/prelude/**

## Demo tickets

Point your phone's camera at a code to open that ticket in Prelude.

| Argentina vs England | Argentina vs France |
| :------------------: | :-----------------: |
| ![QR code for Argentina vs England, section 108, row 14, seat 8](app/web/assets/tickets/3750191.png) | ![QR code for Argentina vs France, section 215, row 9, seat 6](app/web/assets/tickets/3869685.png) |

Each code is a link to the demo, so the phone's own camera app opens it; no app
install and nothing to type. `scripts/make_tickets.py` generates them and
decodes each image back before it writes it.

What the demo is, precisely:

- **The screens and the navigation work.** You can move through the event list,
  the ticket scanner, ticket details, the live seated screen, the moment card and
  the moments list, and the bottom tabs switch between them. Profile has no
  screen, so that tab is deliberately disabled rather than faked.
- **Scanning and manual entry work.** The scanner reads the QR code on a demo
  ticket from the camera and opens that match; manual entry picks the match from
  a list and takes a seat. Both land on ticket details, and Enter match opens the
  match at its pre-moment state.
- **There is no audio.** Playback and the generated narration arrive in later
  phases. The play buttons change their own icon and nothing else; the waveforms
  are static markup, and the timers are empty on purpose, waiting for real
  values.
- **Nothing is live.** The demo replays StatsBomb historical data: the 1986
  Argentina vs England quarter-final and the 2022 Argentina vs France final,
  each presented as if it were unfolding now. There is no live feed, no venue,
  and no GPS.

> **Status: skeleton.** This README is structure first. The sections below are
> headings awaiting the code that fills them, and the evidence column is
> deliberately empty. What actually runs today is listed under
> [Capability honesty](#capability-honesty), and nothing else here should be read
> as working.

## The problem

<!-- To be written. -->

## What makes it different

<!-- To be written. -->

## How it works

### The loop

<!-- One loop, written once the code exists. -->

### Pillars

<!-- The pillars the loop rests on, written once the code exists. -->

## Judging criteria → evidence

Each row pairs a judging criterion with something a reader can actually run and
watch succeed. Rows stay empty until the code that proves them exists; an
entry is earned by a command, not by a description.

| Judging criterion            | Runnable evidence |
| ---------------------------- | ----------------- |
| Completeness and feasibility |                   |
| Creativity and innovation    |                   |
| Design and usability         |                   |
| Effectiveness and efficiency |                   |

## Capability honesty

This section is the authoritative list of what Prelude can do at this commit.
Everything above it is structure.

**Runs today:**

- `scripts/fetch_statsbomb.py`: downloads the StatsBomb open-data files the
  project uses into `data/raw/` (gitignored, reproducible): the competition and
  match indexes, both matches' event feeds, and both matches' lineups, which
  are what record a player's `player_nickname`.
- `scripts/data_check.py`: reads the 1986 Argentina vs England event feed,
  lists every goal and the shot counts per team, and writes
  [`docs/data_check.md`](docs/data_check.md) from that output.
- `scripts/scan_copy.py`: checks the screens and `app/web/matches.json` for
  banned copy, and for the grounding label sitting anywhere but over narration.
  Exits non-zero on any hit.
- `scripts/check_match_copy.py`: checks every name, minute, score and count in
  `app/web/matches.json` against `data/raw/`, and the inline copy in the screens
  against `app/web/matches.json`.
- `scripts/make_tickets.py`: writes a demo ticket QR code per match into
  `app/web/assets/tickets/`, and reads each one back with a decoder before it
  counts as written.
- `scripts/check_docs.py`: checks that these docs still match the code they
  describe, and exits non-zero when one has gone stale.
- `scripts/narration_compare.py`: the paid comparison of the two watsonx
  candidates, by persona. `--plan` prints the narrations, the calls and the
  estimated tokens and makes no call; `--confirm` has to name the same arms as
  `--arms`; `--max-tokens` stops the run between narrations.
- `scripts/freeze_narrations.py`: narrates both hero goals on watsonx with the
  active model and writes the ones the grounding check passed to
  `app/web/narrations.json`, with the facts each cited and the check's
  verdict beside the text. A narration that reaches the template fallback is
  not frozen: the run writes nothing and exits 1. `--plan` prints the call
  count and makes no call; `--confirm` sends it. The moment card shows what it
  writes and `scripts/tts_hero.py` speaks it, so a rerun changes the words in
  both places and costs a paid call.
- `scripts/tts_probe.py`: measures which delivery controls change the audio on
  each of the three candidate IBM voices, by synthesizing one fixed sentence
  per arm and reading the duration, the pitch and the bytes back. `--plan`
  prints the character count and makes no call; `--confirm` sends it;
  `--from-audio` re-measures what is already on disk. It writes WAV files
  outside the repo. What it found is in [`docs/VOICE.md`](docs/VOICE.md).
- `scripts/narration_eval.py`: narrates goals several times, in one persona or
  all of them, and measures what came back: the first-attempt and after-retry
  pass rates, coverage of the passage's key beats, words per sentence, tokens
  and time. Writes [`docs/narration_eval.md`](docs/narration_eval.md), which
  holds three runs. Ollama only.
- `app/statsbomb_event_feed.py`: `StatsBombEventFeed`, the EventFeed
  implementation. Reads a match from `data/raw/`, returns its goals as
  moments (periods 1 to 4, so the shootout is excluded), and returns the run-up
  to a goal as untouched source records. `buildup` returns the goal's whole
  possession, plus the previous possession when the goal came from a set piece,
  which is how the foul that won a penalty reaches a caller.
- `tests/test_event_feed.py`: 28 tests over the EventFeed contract, including
  `buildup`. All 28 pass against `app/statsbomb_event_feed.py`.
- `app/narration_provider.py`: one narration interface with two backends,
  Ollama (the default, local) and watsonx.ai (only when named). Callable from
  Python; no screen calls it. `provider()` returns the Ollama backend, and
  nothing reaches watsonx without passing its name.
- `scripts/record_narration_golden.py`: calls the local Ollama server once and
  records the request and response into `tests/golden/`, so the tests can
  replay a real response instead of making a call.
- `scripts/narrate_once.py`: narrates one goal with a real model and prints
  every attempt, the claims the check refused, and whether the first attempt
  was grounded. Defaults to the 1986 goal at 54:18; takes a match id and a
  clock for any other. It needs a local Ollama server and writes nothing.
- `tests/test_narration_provider.py`: 60 tests over the config and both
  backends, including the answer that is all reasoning and no narration, the
  timeout a run sets for itself and the tokens watsonx says it billed. All 60
  pass, and none of them opens a connection:
  `tests/conftest.py` replaces `urllib.request.urlopen` and
  `socket.socket.connect` with functions that raise, for every test in the
  suite.
- `app/narration_prompt.py`: turns one buildup into a numbered list of plain
  past-tense facts, one per recorded event, built by code out of the records
  and naming each player by the recorded nickname where there is one;
  the prompt that asks a model to narrate from that list in the past tense, cite
  the facts each sentence used, and stop on the goal; `NARRATION_STYLE`, the one
  style every narration is written in, printed into that prompt in every voice;
  and the fallback narration, one sentence per fact, assembled with no model.
- `app/plain_characters.py`: rewrites a disguised space or hyphen as the plain
  one: `NO-BREAK SPACE`, `NARROW NO-BREAK SPACE`, every other Unicode space
  separator, `NON-BREAKING HYPHEN`, `MINUS SIGN` and the zero-width
  characters, which are removed rather than replaced. Applied as a model's
  narration arrives in `app/narration.py`, again in `app/grounding.py` before
  a claim is read, and again in `app/tts.py` before a speech request is built.
  A dash is left exactly as written: the em dash and the en dash are refused
  by the check and banned from copy, so rewriting either as a hyphen would
  undo a ban in the one place nobody would look.
- `tests/test_plain_characters.py`: 40 tests over the rewrite, including the
  two characters live candidates actually arrived with, the sixteen space
  separators, the dashes left alone and the em dash still being refused after
  it. All 40 pass.
- `app/recorded_names.py`: reads `player_nickname` out of
  `data/raw/lineups/<match_id>.json` and maps it to the full name the event
  feed records, so a narration can say "Lionel Messi" rather than "Lionel
  Andrés Messi Cuccittini". It is a reader and not a chooser: there is no
  fallback that shortens a name the file does not shorten, so a player with no
  recorded nickname keeps their full recorded name. Maradona is one of those,
  so the 1986 narration says his name in full.
- `tests/test_recorded_names.py`: 7 tests over the reader and over what the two
  lineups files record, including the four nicknames the 2022 hero buildup has
  and the nickname the 1986 file does not record for the scorer. All 7 pass.
- `app/grounding.py`: decides whether a narration's claims trace back to the
  data, sentence by sentence, against the facts that sentence cited. Refuses
  invented names, numbers, clocks and actions; a name or action in the passage
  but not in the cited facts; a name paired with an action no single cited fact
  records; a short form of a player's name that neither the event feed nor the
  lineups file records, while accepting either of the two names they do; a sentence that cites nothing or cites a fact that does not exist; a
  present-tense verb, in a passage that already happened; a narration that does
  not end on the goal's own shot; a wrong shot type or body part; verdict
  nicknames, editorial epithets, claims about the result, lines addressed to the
  fan, em dashes, any angle bracket; and narration that asserts nothing
  checkable. It takes the
  persona and the listener's side, which change one thing: a partisan persona
  may say "we", "our" and "us" about that side, in a sentence citing a fact
  recorded against it, and no other voice may say them at all. The prompt asks
  for none of them in any voice, so that rule is a guard against a model that
  writes the first person anyway rather than a permission anything uses.
- `app/personas.py`: the three personas, each with an id, a name, a one-line
  Profile description of what it sounds like, and whether it is offered to fans
  only. They are separated by sound and not by text: the narration is one style
  in every voice, and each persona now carries the IBM voice Shawn picked for
  it. The rate, the pitch and the two sentence breaks are still `None` and
  marked unconfirmed, because Shawn sets them by ear. Three measured runs
  behind that decision are in `docs/narration_eval.md`. No screen offers a
  choice yet.
- `app/tts.py`: the speech backend. Takes the header, the narration, a persona
  and a situation, and returns the audio bytes IBM Watson Text to Speech
  sent, in the format the caller asked for: WAV by default, MP3 for the
  recordings the site ships.
  Callable from Python; no screen reaches it. It refuses a narration that still
  carries its citation tags, applies the pronunciation table, and puts the
  pauses in only for a voice whose breaks work. Credentials come through
  `app/credentials.py` and a missing one is named before any request.
- `tests/test_tts.py`: 56 tests over the backend, replaying a real recorded
  exchange from `tests/golden/tts_synthesize.json`. All 56 pass, and none of
  them reaches the service.
- `scripts/record_tts_golden.py`: records one real speech exchange for that
  replay. `--plan` prints the request and its character count and makes no
  call; `--confirm` sends it.
- `scripts/check_vocabulary.py`: collects every word the app can speak, from
  the header wording, the event verbs, the narration template, the team names
  in `app/web/matches.json` and the recorded narrations in `tests/golden/`, and
  reports the ones the CMU Pronouncing Dictionary lists more than one
  pronunciation for. Exits non-zero when a flagged word has not been reviewed;
  `tests/test_vocabulary.py` is the same condition in the suite. No network:
  the dictionary is a dev dependency and ships its own data.
- `tests/test_vocabulary.py`: 22 tests over the collector, the two review
  lists and the three heteronyms in the table. All 22 pass.
- `scripts/tts_samples.py`: both hero goals in every voice, with the Mate from
  both sides, written outside the repo for Shawn to listen to. The words are
  the orchestrator's header and the code-built narration, so no model runs.
  `--plan` prints the character count and makes no call, `--budget` refuses a
  run above a character count, `--personas` reruns one voice's files without
  paying for the rest, and `--confirm` sends it.
- `scripts/tts_hero.py`: the recordings the site serves, one per listener per
  match, as MP3 under `app/web/assets/`, with `hero.audio` in
  `app/web/matches.json` written from the files on disk. The words are the
  orchestrator's header and the frozen narration in `app/web/narrations.json`,
  which a model wrote and the grounding check passed, so these speak what the
  moment card shows rather than the template the samples speak.
  `--plan` prints the character count three ways
  and makes no call, `--budget` refuses a run above the billed count,
  `--confirm` sends it, and `--map` rewrites the map alone. **No recording
  exists yet:** the service answered HTTP 403 to every request on
  2026-10-30, so `hero.audio` is still empty and the moment card's play
  button stays disabled.
- `app/delivery.py`: the delivery table, one row per persona per situation,
  holding the rate, the pitch and the two pauses. The values are Shawn's, set
  by ear, with the rules enforced around them: no lowered pitch, no pause on a
  voice whose breaks do nothing, no rate outside IBM's bounds, and no Mate
  that is cheerful when the other side scored. The situation comes from the
  moment and the listener, never from a model.
- `tests/test_delivery.py`: 47 tests over the situations, the eight rows, the
  values in them, the bounds and the Mate rule. All 47 pass.
- `app/pronunciation.py`: the pronunciation table, word to IPA, with three
  entries: `lead` to `liːd`, which is needed, since Shawn heard "extend the
  lead" read as "led" without it and "leed" with it; `minute` to `ˈmɪnɪt`,
  which all three voices read as "my-NEWT"; and `close` to `kloʊz`, which the
  dictionary flagged and nobody has heard yet. `for_speech` marks the listed
  words up as `<phoneme>` elements for the speech request, and nothing else in
  `app/` may import it: markup in the text a screen shows is a fan reading
  tags, and markup in the text `app/grounding.py` reads is a sound narration
  refused for tags it never wrote. The check refuses any angle bracket, and a
  test reads source as the second layer, for the header, which no check sees.
  Text holding no listed word is returned identically.
- `tests/test_pronunciation.py`: 35 tests over the table, the markup, the
  round trip that proves a pronunciation never changes a word, the seven
  modules forbidden to import it, the one module that applies it, and the real
  1986 narration through the real backend. All 35 pass.
- `tests/test_personas.py`: 27 tests over the config's shape, the ids against
  `app/orchestrator_contract.py`, the three picked voices, the unconfirmed
  prosody fields and the Profile copy. All 27 pass.
- `app/narration.py`: narrates one moment. Generates, checks, regenerates up to
  twice, then falls back to the template, and records every attempt with the
  claims that failed. Nothing ungrounded is returned. The citation tags are
  stripped from the text it returns and kept beside it for audit.
- `app/credentials.py`: finds and reads the credentials file, which lives
  **outside this repo**: `~/.prelude/.env` by default, or wherever
  `PRELUDE_ENV_FILE` points. A path inside the repo is refused rather than
  read. `describe` reports which variable names a file defines and never a
  value, so a missing credential can be diagnosed without one reaching a
  terminal.
- `tests/test_credentials.py`: 29 tests over the loader. Every one writes a
  fake credentials file into a temporary directory; none reads the real one,
  and `tests/conftest.py` points `PRELUDE_ENV_FILE` at an absent path for the
  whole suite so none can.
- `tests/test_narration_prompt.py`: 94 tests over the facts, the numbered fact
  list, the prompt, the one narration style printed in it, the key beats of a
  passage, the move the hero prompt prints as steps, the fallback narration,
  which has to reach every one of those beats, and the recorded fields a goal
  call says out loud: the play pattern, the pressure, the pass recipient and
  length, the assist, the first-time flag, the body part, the two field
  positions read off a coordinate and the duration read off the timestamps.
  All pass.
- `tests/test_grounding.py`: 104 tests over the cited reading of the grounding
  check, one per way a narration can be wrong or can look wrong and be fine,
  including the misdescription it refuses by pairing a name with an action and
  the first person, which only the Mate may use and only over its own side's
  facts. All pass.
- `tests/test_narration_grammar.py`: 85 tests over the goal-call reading in
  `app/narration_grammar.py`, one mechanism at a time: the name parts that
  pick out one player, the pronoun that means the player with the ball, the
  chains, which name owns a claim, "past X" as a dribble past X, the field
  positions, the shape of a run, which way the ball went, a run with yards in
  it, the carry that is asked to deliver the ball and the recorded fields a
  goal call says out loud. All pass.
- `tests/test_reference_narrations.py`: 58 tests holding the narration
  standard: the eight reference narrations in `docs/VOICE.md`, checked word
  for word with the narrator and the listener side given, the eleven lines the
  check has to keep refusing, the words a narration may land the finish on,
  the force words it may not, the verdicts about history it may not, and the
  reaction layer: where a reaction may stand, who may cheer in one and what
  makes a short sentence play instead. All pass.
- `tests/test_narrator_candidates.py`: 123 tests over
  `app/goal_call_prompt.py` and `scripts/narrator_candidates.py`: the four
  styles, one per narrator and situation, the invented match their examples
  are shown through and the reaction each example ends on, the records the
  prompt prints with no clock on them and with which way and how far on them,
  the six recorded slots read off `hero.voice_for`, the price of one
  recording, the request for tellings that differ in structure, the
  reasoning effort the run chooses for itself and the call count and token
  estimate the run prints before it sends anything. All pass, and none calls
  a model.
- `tests/test_narration.py`: 31 tests over the pipeline, covering the retries,
  the fallback, the citation stripping, the failure log, the first-attempt pass
  rate, the characters made plain as a model's text arrives and the attempt
  that came back with reasoning and no narration in it. All pass, and no test
  calls a model.
- `tests/test_narration_eval.py`: 72 tests over the coverage measure, the
  token recorder and the goal selection in `scripts/narration_eval.py`,
  including the live thin narration that passes the grounding check and
  reaches one key beat of five. All pass.

**Exists but does nothing yet:**

- `app/orchestrator.py`: picks the line said before the narration starts:
  "today" or "tonight" from the kickoff time, a header, and a default persona
  from the listener's side. The shapes and the wording live in
  `app/orchestrator_contract.py`. Callable from Python; no screen calls it yet.
  The header is the game focused one: what the goal did to the score, in the
  same words for every listener.
- `tests/test_orchestrator.py`: 72 tests over the orchestrator, covering every
  goal in both demo matches and a made-up sixty minute sport whose scores move
  three at a time. All 72 pass.
- `app/event_feed.py`: the data shapes and the `EventFeed` interface. A
  contract only; `app/statsbomb_event_feed.py` is what implements it.
- `app/narration_config.py`: the model ids and which one is active. Values
  only, with no behaviour: it reads no environment variable and opens no
  connection.
- The play buttons and waveforms on the moment card and the moments list. They
  change their own icons and nothing else, because there is no audio yet.

**Not built yet:** narration on a screen, audio output, and GPS presence
handling. Narration itself runs: `scripts/narrate_once.py` generates it for one
goal, the check decides whether it may carry "Verified from play data", and the
pipeline falls back when it may not. What nothing does yet is measure how often
a first attempt is grounded across the nine goals, or put a narration in front
of a reader. The screens read their content from `app/web/matches.json` and
carry the selected match between them; what they do not have is sound or
narration. Nothing wires the EventFeed to the screens yet: the module returns
moments, event windows and buildups, and no screen reads them.
`docs/narration.md` records what the narration modules are and what they are
not, and `docs/VOICE.md` is the written voice the prompt and the grounding check
enforce between them, with what the check still cannot decide.

No claim in this README is intended to run ahead of the code. If you find one
that does, it is a bug in the README.

## The label, and the two layers under it

The label is **"Verified from play data"**, written once in `app/narration.py`
so nothing spells it differently or softens it. There is no partial credit and
no shortened variant: it goes over narration that passed the check in
`app/grounding.py`, and over nothing else.

What it claims is that **every event in the narration happened as told**. A
narration has two layers, and that sentence is exactly true of both.

**The play** is who, what, where and how it finished, and it is checked claim
by claim against `data/raw/`: the names, the passes from one named player to
another, the defenders gone past, the positions on the pitch, which way the
ball went, how far a carry ran, the body part the goal was scored with.
Nothing in it is inferred, recalled or softened, and a narration with one
unsupported claim in it is refused whole.

**The reaction** is the narrator feeling the moment, in at most eight words:
"Oh, lovely!", "What a finish!", and for the side that conceded "Ah, no.". It
stands once, at the goal, with nothing after it, and it is not checked against
the data, because it asserts nothing about the data: no player, no team, no
pronoun, no number, nothing about where the ball was or what anybody did. It
is the narrator's own voice, and it leaves the label's claim untouched. It is
still held to everything else: no verdict about where the goal stands among
other goals, no words for how hard the ball was struck, and never "you".

[`docs/VOICE.md`](docs/VOICE.md) has the two layers in full, the eight
reference narrations that are the standard for the play, and what the check
still cannot decide. [`docs/VERIFICATION.md`](docs/VERIFICATION.md) has one
test per kind of claim and one per kind of mistake.


## The documents

| Document | What it covers |
| -------- | -------------- |
| [`docs/HARNESS.md`](docs/HARNESS.md) | everything you run to exercise the repo, and what each thing stands on |
| [`docs/VERIFICATION.md`](docs/VERIFICATION.md) | what this repo claims, and what checks each claim |
| [`docs/GOVERNANCE.md`](docs/GOVERNANCE.md) | the rules in `CLAUDE.md`, and what enforces each one |
| [`docs/IBM_STACK.md`](docs/IBM_STACK.md) | which IBM parts are built, and which are planned |
| [`docs/VOICE.md`](docs/VOICE.md) | the narration voice the prompt and the grounding check enforce |
| [`docs/narration.md`](docs/narration.md) | the narration modules, where their shapes came from, and what they are not |
| [`docs/DESIGN.md`](docs/DESIGN.md) | the screens, cited against the markup |
| [`docs/bob_brief.md`](docs/bob_brief.md) | the brief IBM Bob built the EventFeed module to |
| [`docs/data_check.md`](docs/data_check.md) | generated: the 1986 goals and shot counts, from the data |
| [`HANDOFF.md`](HANDOFF.md) | what was built when, what was deviated from, and what is next |

The first four put the file and a test beside nearly every statement they make,
and `scripts/check_docs.py` resolves every one of those citations against a live
pytest collection, so a renamed test breaks the gate rather than leaving a
citation pointing nowhere.

## Credentials

No credential is in this repo. `.env.example` lists the variable names and
holds no values. The live file lives outside the working directory, at
`~/.prelude/.env` by default or wherever `PRELUDE_ENV_FILE` points, so that no
search over the repo can reach it whatever the tool or the command. That is not
a precaution in the abstract: a recursive search over the working directory
once swept the old repo-root file into a transcript without ever naming it, and
a rule about one filename cannot stop a command that searches everything.

`app/credentials.py` is what reads it. A path inside the repo is refused rather
than read. The `.env` entry in `.gitignore` and the `Read(./.env)` deny rule in
`.claude/settings.json` stay as a second layer, in case a file is ever created
at the repo root by habit; neither is the live location.

## Data and attribution

Play data comes from the [StatsBomb open data](https://github.com/hudl/open-data)
repository, used under its terms. Any research, analysis, or insight published
from this project states StatsBomb as the data source.

Data provided by StatsBomb.
