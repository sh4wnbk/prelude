# The documents

Every document in this repo, and what it covers. `README.md` is the short
page; these are where it sends a reader who wants the whole of something.

| Document | What it covers |
| -------- | -------------- |
| [`docs/CAPABILITIES.md`](CAPABILITIES.md) | the authoritative list of what Prelude can do at this commit |
| [`docs/HARNESS.md`](HARNESS.md) | everything you run to exercise the repo, and what each thing stands on |
| [`docs/VERIFICATION.md`](VERIFICATION.md) | what this repo claims, and what checks each claim |
| [`docs/GOVERNANCE.md`](GOVERNANCE.md) | the rules in `CLAUDE.md`, and what enforces each one |
| [`docs/IBM_STACK.md`](IBM_STACK.md) | which IBM parts are built, and which are planned |
| [`docs/THE_LABEL.md`](THE_LABEL.md) | what "Verified from play data" claims, and the two layers under it |
| [`docs/VOICE.md`](VOICE.md) | the narration voice the prompt and the grounding check enforce |
| [`docs/narration.md`](narration.md) | the narration modules, where their shapes came from, and what they are not |
| [`docs/narration_eval.md`](narration_eval.md) | generated: the narration runs, their pass rates and what they cost |
| [`docs/DESIGN.md`](DESIGN.md) | the mark, and the screens cited against the markup |
| [`docs/HOSTED_API.md`](HOSTED_API.md) | the read-only API on Render, its three endpoints and what it does not hold |
| [`docs/orchestrate_agent.md`](orchestrate_agent.md) | the instructions pasted into the watsonx Orchestrate agent, and why each one is there |
| [`docs/bob_brief.md`](bob_brief.md) | the brief IBM Bob built the EventFeed module to |
| [`docs/CREDENTIALS.md`](CREDENTIALS.md) | where the live credentials are, and why they are not here |
| [`docs/DATA.md`](DATA.md) | the play data this project uses, and its attribution |
| [`docs/data_check.md`](data_check.md) | generated: the 1986 goals and shot counts, from the data |
| [`docs/history/`](history) | the task records `HANDOFF.md` used to carry inline, and the index of them |
| [`bob_sessions/README.md`](../bob_sessions/README.md) | one row per Bob session: the export, the screenshot and the commits |
| [`HANDOFF.md`](../HANDOFF.md) | the state of the repo, the next first action and the latest task record |

`docs/HARNESS.md`, `docs/VERIFICATION.md`, `docs/GOVERNANCE.md` and
`docs/IBM_STACK.md` put the file and a test beside nearly every statement they
make, and `scripts/check_docs.py` resolves every one of those citations
against a live pytest collection, so a renamed test breaks the gate rather
than leaving a citation pointing nowhere.
