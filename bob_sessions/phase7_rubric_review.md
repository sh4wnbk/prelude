# Task: score Prelude against the lab rubric. Read only.

Orient: read README.md, then HANDOFF.md "Current state" only, then
docs/IBM_STACK.md. Open other files only to confirm a specific claim.
Do not read bob_sessions/ or docs/history/.

Rules: change no file, run no command that writes, commit nothing.
If you reach 10 Bobcoins, stop and report what you have.

Steps:
1. For each criterion, give a score out of 5 and the evidence for it as
   file paths or URLs:
   - Completeness and feasibility
   - Creativity and innovation
   - Design and usability
   - Effectiveness and efficiency
2. For each criterion, name the one change that would raise the score
   most and could be done before Nov 22.
3. List any claim in README.md that you could not confirm from the code.

Exit: a single report with a 4-row table (criterion, score, evidence,
one change), then the unconfirmed-claims list. No em dashes.

---

**Status:** active  **Date:** 2026-11-19

---

### 👤 User

Task: score Prelude against the lab rubric. Read only.

Orient: read README.md, then HANDOFF.md "Current state" only, then
docs/IBM_STACK.md. Open other files only to confirm a specific claim.
Do not read bob_sessions/ or docs/history/.

Rules: change no file, run no command that writes, commit nothing.
If you reach 10 Bobcoins, stop and report what you have.

Steps:
1. For each criterion, give a score out of 5 and the evidence for it as
   file paths or URLs:
   - Completeness and feasibility
   - Creativity and innovation
   - Design and usability
   - Effectiveness and efficiency
2. For each criterion, name the one change that would raise the score
   most and could be done before Nov 22.
3. List any claim in README.md that you could not confirm from the code.

Exit: a single report with a 4-row table (criterion, score, evidence,
one change), then the unconfirmed-claims list. No em dashes.

---

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — c:\Users\shawn\Documents\src\prelude\README.md

### 🤖 Assistant

> 🔧 called: read_file, read_file



> 🔧 **read_file** — IBM services used, Watson TTS billed characters, watsonx services details

> 🔧 **read_file** — current state of the project, what works, what does not

### 🤖 Assistant

> 🔧 called: read_file, read_file

Now let me confirm a few specific claims from the README by spot-checking key files.

> 🔧 **read_file** — grounding check, the label, verified claim, sentence-by-sentence verification

> 🔧 **read_file** — number of screens, what screens exist, capabilities

### 🤖 Assistant

> 🔧 called: read_file, read_file



> 🔧 **read_file** — hosted API, cost per visit, efficiency claims, static site

> 🔧 **read_file** — design palette, mobile size, testing, design decisions

### 🤖 Assistant

> 🔧 called: glob, glob

Now let me check a couple of specific claims I want to verify or flag.

> 🔧 **glob** — tests/browser/test_the_label_waits.py

> 🔧 **glob** — .github/workflows/ci.yml

### 🤖 Assistant

> 🔧 called: list_files



> 🔧 **list_files** — c:\Users\shawn\Documents\src\prelude

### 🤖 Assistant

> 🔧 called: list_files, list_files



> 🔧 **list_files** — c:\Users\shawn\Documents\src\prelude\tests

> 🔧 **list_files** — c:\Users\shawn\Documents\src\prelude\.github\workflows

### 🤖 Assistant

> 🔧 called: list_files



> 🔧 **list_files** — c:\Users\shawn\Documents\src\prelude\tests\browser

### 🤖 Assistant

> 🔧 called: read_file, read_file

The `test_the_label_waits.py` does exist. The glob couldn't find it because the glob searched the workspace root directly. Now let me check a few of the claims I want to verify.

> 🔧 **read_file** — narration_eval.md: model comparison results, 155 calls, two models

> 🔧 **read_file** — ci.yml: what it runs - unit suite, five gates, browser suite

### 🤖 Assistant

> 🔧 called: grep



> 🔧 **grep** — 155

### 🤖 Assistant

The 155 calls figure is confirmed. Now I have enough to write the full report.

---

Here is the rubric scorecard.

## Prelude -- Lab Rubric Score

### Scoring table

| Criterion | Score | Evidence | One change before Nov 22 |
|-----------|------:|----------|--------------------------|
| **Completeness and feasibility** | 4/5 | Seven screens, two matches, six MP3 recordings, three IBM services all running end-to-end today ([`docs/CAPABILITIES.md`](docs/CAPABILITIES.md)); CI runs on every push ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)); smoke workflow checks the deployed site and API after each deploy ([`.github/workflows/smoke.yml`](.github/workflows/smoke.yml)); unit suite (1,000+ tests) passes; five gates pass; browser suite passes; Orchestrate agent live and evidenced ([`docs/evidence/orchestrate_2022_argentina_fan.png`](docs/evidence/orchestrate_2022_argentina_fan.png)). Two stated gaps hold the score below 5: the Caller persona has no recording (`hero.voice_for` sends no listener to it, leaving two voices rather than three), and nothing wires the EventFeed to the screens for non-hero moments. | Record the two Caller MP3s with `scripts/tts_hero.py`. The delivery table, voice, and personas entry for the Caller already exist; `tts_hero.py` already has the budget flag. The Caller is the only incomplete persona, and completing it closes the gap the README itself names. |
| **Creativity and innovation** | 5/5 | The grounding check ([`app/grounding.py`](app/grounding.py), [`docs/THE_LABEL.md`](docs/THE_LABEL.md)) reads every sentence of a narration claim-by-claim against StatsBomb records before the "Verified from play data" label appears. A browser test asserts the label over every frame the moment card passed through ([`tests/browser/test_the_label_waits.py`](tests/browser/test_the_label_waits.py)). A paid model comparison over 155 real watsonx calls measured two candidates and chose the one with a 100% first-attempt grounded rate ([`docs/narration_eval.md`](docs/narration_eval.md) line 259). QR codes on demo tickets open the right match without any app to install ([`app/web/assets/tickets/`](app/web/assets/tickets/)). Watson TTS voices are differentiated by persona and listener side via a delivery table ([`app/delivery.py`](app/delivery.py)), not by text alone. | None needed for this criterion; the grounding-check innovation is fully built, documented and tested. The only additional move would be extending narration to non-hero goals -- which is listed under "not built yet" and is a completeness item, not a creativity one. |
| **Design and usability** | 4/5 | Coherent dark-only design system: 18 tokens in use, one amber accent, one font ramp, one spacing scale, all locked in a Tailwind config block that is byte-identical across all screens ([`docs/DESIGN.md`](docs/DESIGN.md)). Eleven iPhone startup images drawn from one layout script ([`scripts/brand/build_svg.py`](scripts/brand/build_svg.py)). Launch screen timing measured in headless Chromium at 390 by 844. Phone-frame bezel for desktop. The browser suite checks accessible names, label timing, player behavior, sharing, and the first load. Keyboard focus is explicitly noted as absent for all buttons except the text input, and the toggle has `focus:outline-none` with no replacement ([`docs/DESIGN.md`](docs/DESIGN.md) line 689-690). The Caller narrator listed on Profile as "coming soon." | Add a visible focus style to the play button on the moment card. This is one CSS addition (`focus-visible:ring-2 focus-visible:ring-primary-container` on the button), it is already called out as a gap in the design doc, and the browser suite already has an accessible-names test to extend. |
| **Effectiveness and efficiency** | 4/5 | The API serves frozen narrations and pre-made MP3s: a thousand calls cost what one does ([`docs/HOSTED_API.md`](docs/HOSTED_API.md)); this is tested by `tests/test_api.py::TestWhatItDoesNotReach`. The app on GitHub Pages calls no API at visit time ([`HANDOFF.md`](HANDOFF.md) line 99-101). Watson TTS was billed once for 2,403 characters across six files ([`docs/IBM_STACK.md`](docs/IBM_STACK.md) line 248). IAM token is cached for the life of the provider, avoiding repeated exchange calls ([`docs/IBM_STACK.md`](docs/IBM_STACK.md) line 108-109). The Render free tier sleeps after 15 minutes idle, so a cold Orchestrate call waits up to 82 seconds; the keepalive workflow (`PRELUDE_KEEPALIVE`) is off by default and must be manually enabled before judging. | Turn on `PRELUDE_KEEPALIVE` before judging (Settings, Secrets and variables, Actions, Variables). This is one toggle, it is called out explicitly in [`HANDOFF.md`](HANDOFF.md) lines 29-32, and it is the only operational step standing between a judge and a first-call timeout. |

---

### Unconfirmed claims from README.md

1. **"over eighteen sessions"** -- [`docs/IBM_STACK.md`](docs/IBM_STACK.md) lists 18 session exports (17 numbered phases plus the tagline row), but the HANDOFF table counts 18 rows including one phase-7 entry that "stopped at the cost limit with nothing committed." The README says "eighteen sessions" and the table has 18 rows, but the README wording implies 18 productive sessions; one was stopped early. Minor discrepancy, not a false claim, but the number could be read either way.

2. **"155 calls compared two models"** -- Confirmed at [`docs/narration_eval.md`](docs/narration_eval.md) line 259. No issue.

3. **"checked in a browser at 390 by 844 on every push"** -- CI runs the browser suite on every push, confirmed in [`.github/workflows/ci.yml`](.github/workflows/ci.yml). The launch-screen test does run at 390 by 844, confirmed in [`docs/DESIGN.md`](docs/DESIGN.md) line 522. The claim is accurate but it covers only the launch-screen comparison; the broader browser suite runs at a wider set of viewports (including 412 by 915 for Android). The claim is not wrong but understates what runs.

4. **"The live demo does not depend on the API"** -- Stated in README as a callout, confirmed by HANDOFF ("Nothing is loaded from anywhere else" and Pages "calls no API"), and by the test `tests/browser/test_every_screen.py` which asserts no screen leaves its own origin. Confirmed.

5. **"a watsonx Orchestrate agent answers about a match from two read-only tools"** -- The agent is live as of 2026-11-07 (screenshot evidence in [`docs/evidence/`](docs/evidence/)), the OpenAPI file is at [`orchestrate/prelude_tools.yaml`](orchestrate/prelude_tools.yaml), and the API is read-only. Confirmed from files. The live status of the agent in Orchestrate's own UI cannot be confirmed from the repo alone; the screenshots are the only evidence.