# Phase 6 as it was handed over, and the doc sweep that closed Phase 5

Moved out of `HANDOFF.md` unchanged, when that file was restructured as a
running snapshot plus the latest record. **This is the record as it was written
when each task closed, not a description of the repo today**: present tense in
it means the day of the task. `HANDOFF.md` carries the current state, and
`docs/history/README.md` says where each decision from here now lives.

The Orchestrate handover and the document corrections that emptied the register of stale passages. The standing part of the Orchestrate setup is in `HANDOFF.md` under Current state.

---

## Phase 6, as it was handed over (Shawn runs Bob, then the Orchestrate import)

**The endpoint is deployed and the spec is briefed.** Task 18 above is the
record: <https://prelude-api.onrender.com> answers, Task 15 in
`docs/bob_brief.md` is the brief for `orchestrate/prelude_tools.yaml`, its 64
acceptance tests are in `tests/test_orchestrate_spec.py` and all of them fail,
and `docs/orchestrate_agent.md` is the agent's instructions.

**The first action is Shawn's: run Bob on Task 15.** Nothing Claude Code can
do comes before it; the file is reserved for that session the way every other
task of Bob's was. Then, in the lab's Orchestrate UI, import the file (Toolset,
Add tool, Import, Import from file), select both operations, skip the
connection because the API takes none, and paste the block from
`docs/orchestrate_agent.md` into the agent. Wake `/health` first: the standing
section at the top of this file says why.

Afterwards, three things come back to Claude Code: the export committed to
`bob_sessions/`, the follow-up the brief predicts (the quoted `pytest -q`
result in `docs/bob_brief.md`, the suite's state in `docs/HARNESS.md` and Task
15's status line), and `docs/IBM_STACK.md` finished with the Orchestrate layer
in it.

The paragraphs below are Phase 5's close and still read true, except where
Task 17 says otherwise: the hosted service holds no keys, so the first of the
three settled things is now a statement about a service that reads no
credentials at all.

**Phase 5 is finished and the documents agree with the code.** The six
narrations are written, verified, frozen and recorded, the moment card shows
the words and plays the recording, and a fan chooses their narrator on
Profile. The authorship beside each of the six says what `README.md` says:
drafted with an AI assistant, edited by Shawn, verified by the grounding
check. `docs/IBM_STACK.md`, `bob_sessions/README.md`, `docs/HARNESS.md`,
`docs/VOICE.md`, `CLAUDE.md`, `app/credentials.py`, `.env.example` and the
`scripts/tts_hero.py` docstring were each read against the code and corrected.
The register of stale passages is empty; what is left is three sentences
parked under "For Phase 7's doc pass" below. The suite is at 1524 passed and
the five gates are at exit 0.

**The first action is the hosted narration endpoint**, with nothing in front
of it, because the OpenAPI spec describes an endpoint and the endpoint has to
exist before a spec can be checked against it. The Plan's Phase 6 above is the order: a small hosted
backend holding the IBM keys with rate limiting (Claude Code), then the
OpenAPI tool spec for that endpoint (Bob, in a brief written the way the
others were, with its acceptance tests first), then the agent and the tool
import in Orchestrate (Shawn), then the spec checked against the live
endpoint, a keepalive against a cold start, and `docs/IBM_STACK.md` finished
(Claude Code).

Three things are settled before any of it is written:

- **The keys stay outside the repo.** `~/.prelude/.env`, or wherever
  `PRELUDE_ENV_FILE` points, is read by `app/credentials.py` and by nothing
  else, and the hosting provider's own environment is where the deployed copy
  goes. Nothing reads that file to put it there.
- **The saved audio is the fallback.** The six recordings in
  `app/web/assets/audio/` are what a judge hears if the endpoint is down,
  which is what the Plan says and what the player already does.
- **Hosting adds no input.** The three real inputs in `CLAUDE.md` are play
  data, GPS presence and audio narration. A hosted endpoint is where the
  existing pipeline runs, not a fourth one.

**`docs/IBM_STACK.md` is corrected, which is part of the last Phase 6
bullet.** Seven passages in it described a repo that had moved on. Three were
the ones recorded here when the drift was found; reading the rest of the
document against the code turned up four more. Each is now present tense and
only what exists, with a file or a test behind it:

| What it said | What it says now |
| ------------ | ---------------- |
| `app/tts.py` returns WAV and "No screen reaches it, so no fan hears anything yet" | the format is the caller's through `accept`, and the six MP3s under `app/web/assets/audio/` are what the player plays, with the voice and the billed count per file |
| "That a narration has been spoken. None has." | the six were spoken on 2026-11-07 for 2,403 billed characters, and no screen calls `app/tts.py` at runtime |
| the third voice belongs to "the Mate" | the Buddy, `en-US_EthanNatural`, which is what `app/personas.py` declares |
| "Three sessions, one export each" | fourteen, each row with its export, its screenshot and the commit that added it |
| "The comparison has not been run" | it was Task 4b: 87 narrations over 155 generation calls, reported in `docs/narration_eval.md` |
| "The prosody fields are still empty and unconfirmed" | the delivery lives in `app/delivery.py`, eight rows, and all three personas carry `prosody_confirmed` true |
| "the same decision as the three gates" | four of the five gates, with `scripts/check_vocabulary.py` the exception that a test does cover |

None of the seven was caught by `scripts/check_docs.py`: it checks paths, test
citations, counts, quoted output and dashes, and these were all prose. The
document now also states what it does not claim in terms that are true: that
the pipeline did not write the six, that the Caller has never been heard
because it has no recording, and that the delivery numbers are Shawn's by ear
rather than measured.

**The three passages outside that document are fixed too, and so is the
`.env.example` comment.** `bob_sessions/README.md` lists all fourteen sessions,
each with its export, its screenshot, the commit the work landed in and the
commit that added the export; the five Bobcoin figures that were read as the
sessions ran are kept and the other nine say they come from the Bobalytics
export at submission, which is Phase 7's line above. `docs/HARNESS.md` names
the five gates instead of three, in both places, and labels
`scripts/data_check.py` and `scripts/check_vocabulary.py` as gates in its
script table. The `scripts/tts_hero.py` docstring says `buddy_scored` and
`buddy_conceded`. `.env.example` says that nothing reads either George voice
name or `TTS_VOICE`, and that `TTS_API_KEY` and `TTS_URL` are read by
`app/tts.py` through `app/credentials.py`.

**`tests/test_buddy_rename.py` now catches the name inside an identifier**,
which is why that docstring survived three tasks: the pattern was a word-bounded
`mate`, and an underscore is a word character, so `mate_scored` never matched.
It is a letter on either side that makes it another word now, which leaves
"estimate" and "teammate" alone and catches `MATE`, `THE_MATE` and
`mate_scored`. Widening it caught two more: two tests in
`tests/test_grounding.py::TestThePartisanVoice` still had `_the_mate_` in their
names, and they are renamed with the citation of one of them in
`docs/VOICE.md`.

**The register is clear.** `docs/HARNESS.md` and `docs/VOICE.md` were the
last two documents describing an app that had moved on, and both are corrected:

- **`docs/HARNESS.md`, what the screens do.** The bullet that said no screen
  plays audio now says that no screen calls `app/tts.py` and that the moment
  card plays the committed MP3 for the listener's own key out of `hero.audio`.
  The bullet that said no screen reads narration now says the moment card
  reads `app/web/narrations.json` by that same key, through the one lookup in
  `app/web/match-content.js`, so the words under the label are the words the
  voice reads.
- **`docs/HARNESS.md`, the pass rate.** No test measures it, because
  `tests/conftest.py` blocks the network and a pass rate needs a model;
  `scripts/narration_eval.py` measures it with its own `pass_rate`, and the
  figure is the one in `docs/narration_eval.md`: 22 of 27 first attempts
  grounded on the development model over nine goals, three runs each.
- **`docs/HARNESS.md`, the scripts.** Twenty-three, read off `scripts/`, and
  the table names every one of them: the seven it never listed are
  `write_headers.py`, `write_narrators.py`, `story_beats_report.py`,
  `hero_candidates.py`, `narrator_candidates.py`, `authored_narrations.py` and
  `fallback_narrations.py`. Two of those reach watsonx, so eleven scripts reach
  a paid or local service rather than nine, and the claim that two scripts are
  imported is replaced by which ones are and why.
- **`docs/VOICE.md`, the persona name.** The sentence that licensed the old
  name is settled first: the display name and the id are both the Buddy, and
  `tests/test_buddy_rename.py::test_no_live_file_says_mate` holds that no live
  file says otherwise. Fourteen lines of present-tense design text say the
  Buddy now, and the run records keep Mate, which the new paragraph beside the
  rename states as the rule rather than leaving to be inferred.
- **`CLAUDE.md` and `app/credentials.py`** say `.env.example` lists the
  variable names and holds no secrets, which is what is true of it: the two
  values in it are a public endpoint URL and a voice name.
