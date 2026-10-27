# The IBM stack

Which IBM parts this project runs on. The first half is what is in the repo at
this commit, with the file and the test behind each statement. The second half
is planned and is labelled as planned, which is what `CLAUDE.md` requires of
anything not yet built.

## Built

### IBM Bob built the EventFeed module

`app/statsbomb_event_feed.py` is Bob's. `CLAUDE.md` reserves the EventFeed and
moment-detection module for Bob, and `app/event_feed.py` is the contract it was
built against: shapes and a protocol, with no behaviour, no file access and no
detection rules.

| What | Where |
| ---- | ----- |
| the contract | `app/event_feed.py` |
| the implementation | `app/statsbomb_event_feed.py` |
| the brief it was built to | `docs/bob_brief.md` |
| the acceptance tests | `tests/test_event_feed.py` |

The contract is held by tests rather than by convention:
`tests/test_event_feed.py::TestContract::test_satisfies_the_event_feed_protocol`
and
`tests/test_event_feed.py::TestBuildup::test_the_implementation_satisfies_the_buildup_protocol`.

What the module does, each with the test that holds it:

| Behaviour | Test |
| --------- | ---- |
| returns a match's events in feed order, untouched | `tests/test_event_feed.py::TestContract::test_load_match_returns_the_whole_feed` |
| finds the 1986 match's three goals | `tests/test_event_feed.py::Test1986::test_finds_exactly_three_goals` |
| reports the raw floored clock, adding nothing | `tests/test_event_feed.py::Test1986::test_minutes_are_the_raw_floored_clock` |
| excludes the 2022 shootout | `tests/test_event_feed.py::Test2022::test_shootout_penalties_are_not_defining_moments` |
| ends a window at the goal shot | `tests/test_event_feed.py::TestEventWindow::test_window_ends_at_the_moment` |
| returns the goal's whole possession as a buildup | `tests/test_event_feed.py::TestBuildup::test_the_1986_goal_is_one_possession_ending_on_the_shot` |
| reaches back one possession for a set piece | `tests/test_event_feed.py::TestBuildup::test_each_2022_penalty_reaches_back_one_possession` |
| so the foul that won a penalty is in the run-up | `tests/test_event_feed.py::TestBuildup::test_each_2022_penalty_includes_the_foul_that_won_it` |

Phase 4 calls the module rather than reaching around it: `app/narration.py`
takes an `EventFeed` and asks it for a buildup, and `app/narration_prompt.py`
reads its numbered facts off what comes back.

### The session exports

Three sessions, one export each, committed rather than ignored because the
submission guide requires them to be present in the final repo.
`bob_sessions/README.md` is the index and the scrubbing rule.

| Phase | Task | Export | Screenshot | Commit |
| ----: | ---- | ------ | ---------- | ------ |
| 3 | build `StatsBombEventFeed` | `bob_sessions/phase3_task1_eventfeed.md` | `bob_sessions/phase3_task1_eventfeed.png` | `3ce6bca` |
| 3 | end event windows at the goal shot | `bob_sessions/phase3_task2_window_fix.md` | `bob_sessions/phase3_task2_window_fix.png` | `343c712` |
| 4 | add `buildup` | `bob_sessions/phase4_task3_buildup.md` | `bob_sessions/phase4_task3_buildup.png` | `24e1a8d` |

The Bobcoin figure for each session is read from its own task summary, which is
what the screenshots record; `bob_sessions/README.md` carries the numbers.

Exports are transcripts, so they are scrubbed of anything secret before every
commit, by hand. Nothing in the repo scrubs them. The Task 3 export needed no
scrubbing, and that was a scan rather than an assumption: no variable name from
`.env.example`, no bearer token, key, project id or URL carrying a query string.
Its two mentions of `.env` are the rule text telling Bob not to open it.

### The watsonx.ai provider

`WatsonxProvider` in `app/narration_provider.py` is the watsonx backend. It is
reached only by naming it, so a development run cannot land on a paid endpoint
by accident:

| Behaviour | Test |
| --------- | ---- |
| the default backend is Ollama, not watsonx | `tests/test_narration_provider.py::TestSelection::test_the_default_is_ollama` |
| watsonx comes back only when named | `tests/test_narration_provider.py::TestSelection::test_watsonx_needs_naming` |
| an unknown name is an error rather than a silent default | `tests/test_narration_provider.py::TestSelection::test_an_unknown_name_is_an_error_not_a_default` |
| both backends satisfy the one interface | `tests/test_narration_provider.py::TestSelection::test_both_backends_satisfy_the_interface` |

The first `narrate` is two requests: the IBM Cloud IAM exchange that turns the
API key into a bearer token, then the generation call. **The token is then
cached for the life of the provider**, so later narrations are one request
each. It held no cache at first, on the grounds that nothing ran long enough
to need one; the paid comparison in `scripts/narration_compare.py` made 155
generation calls in one run, and one IAM exchange each would have been both
waste and a way to be rate limited.

IBM states the token's lifetime in the exchange and it is reused until
`IAM_EXPIRY_MARGIN` before that. A response with no stated lifetime is treated
as already expired, so the cache can only ever shorten a token's life
(`tests/test_narration_provider.py::TestTheTokenIsCached::test_a_token_with_no_stated_lifetime_is_not_reused`).
A 401 is the one expiry a clock cannot predict, so the token is dropped and
fetched once more and a second 401 is raised
(`tests/test_narration_provider.py::TestTheTokenIsCached::test_a_401_drops_the_token_and_tries_once_more`).

| What | Value | Test |
| ---- | ----- | ---- |
| generation path | `/ml/v1/text/generation` | `tests/test_narration_provider.py::TestWatsonxBackend::test_the_request_matches_the_documented_shape` |
| API version sent | `2025-02-11` | `tests/test_narration_provider.py::TestWatsonxBackend::test_the_request_matches_the_documented_shape` |
| IAM token URL | `https://iam.cloud.ibm.com/identity/token` | `tests/test_narration_provider.py::TestWatsonxBackend::test_the_iam_exchange_uses_the_apikey_grant` |
| the generation call carries the token it fetched | as a bearer header | `tests/test_narration_provider.py::TestWatsonxBackend::test_it_authorises_the_generation_call_with_the_token_it_fetched` |
| the answer is read out of `results[0].generated_text` | | `tests/test_narration_provider.py::TestWatsonxBackend::test_it_reads_the_text_out_of_the_documented_response` |
| an empty `results` array is an error | | `tests/test_narration_provider.py::TestWatsonxBackend::test_an_empty_results_array_is_an_error` |

**The tests still make no watsonx call.** The request and response shapes in
`tests/golden/watsonx_text_generation.json` come from IBM's published schema
rather than from a recording, and the file says so in its own provenance
block, with its citations;
`tests/test_narration_provider.py::TestWatsonxBackend::test_the_golden_says_it_is_not_a_recording`
holds that claim in place. Recording one would mean a paid call against live
credentials, which `CLAUDE.md` puts out of reach. `docs/narration.md` records
where each shape came from.

**Task 4b made the first real calls**, 155 generations across two candidates,
from `scripts/narration_compare.py` and by hand. It found that the schema the
tests were written to is correct and that it is the wrong endpoint for this
job: `/ml/v1/text/generation` applies no chat template, so one candidate
prefixed its answer with the end of the prompt and the other returned its
reasoning as the answer. The comparison ran on `/ml/v1/text/chat` instead,
which `WatsonxProvider` reaches with `chat=True`.

| What | Value | Test |
| ---- | ----- | ---- |
| chat path | `/ml/v1/text/chat` | `tests/test_narration_provider.py::TestTheChatEndpoint::test_it_posts_to_the_chat_path` |
| the prompt goes in as one user message | | `tests/test_narration_provider.py::TestTheChatEndpoint::test_the_prompt_goes_in_as_one_user_message` |
| the answer is read out of `choices[0].message.content` | | `tests/test_narration_provider.py::TestTheChatEndpoint::test_it_reads_the_text_out_of_a_chat_answer` |
| a chat answer without content is an error | | `tests/test_narration_provider.py::TestTheChatEndpoint::test_a_chat_answer_without_content_is_an_error` |

The comparison also pins the decoding, because watsonx decodes greedily
unless told otherwise and three runs of a greedy model are one run reported as
three
(`tests/test_narration_provider.py::TestTheDecodingIsPinned::test_pinned_decoding_asks_watsonx_to_sample`).
`openai/gpt-oss-120b` is sent `reasoning_effort: low`, which is the one
setting the candidates do not share: at the default effort it spent 1,496
completion tokens thinking before one narration, against Granite's 60, and a
fan waits through that on every attempt. `docs/narration_eval.md` holds the
numbers.

**Credentials are named, never printed.** Building the provider reads
`WATSONX_API_KEY`, `WATSONX_PROJECT_ID` and `WATSONX_URL` through
`app/credentials.py`, which loads them from outside the repo, and raises naming
whichever is unset, so a missing credential fails before any request rather than
as a 401 later
(`tests/test_narration_provider.py::TestWatsonxBackend::test_missing_credentials_are_named_and_nothing_is_sent`).
One blank value is enough to refuse
(`tests/test_narration_provider.py::TestWatsonxBackend::test_one_blank_credential_is_enough_to_refuse`).
`.env.example` lists the names and holds no values. See `docs/GOVERNANCE.md` for
the whole credentials rule.

### Both candidate model ids

`app/narration_config.py` holds the two watsonx models the narration comparison
is between, and the local model development runs on. A model id is not a
credential: it records which model produced a line of narration, so it belongs
in the repo where a reader can see it.

| Candidate | `model_id` | Label |
| --------- | ---------- | ----- |
| IBM Granite | `ibm/granite-4-h-small` | Granite 4 H Small |
| GPT OSS, served on watsonx | `openai/gpt-oss-120b` | GPT OSS 120B |

`ACTIVE_CANDIDATE` is the Granite one. It starts active because it is the IBM
model and this project runs on IBM's stack, and the comparison exists to test
that choice rather than assume it. Switching is one line, and
`tests/test_narration_provider.py::TestConfig::test_exactly_one_candidate_is_active`
asserts only that the active candidate is one of the two, so flipping it does
not break the suite.
`tests/test_narration_provider.py::TestConfig::test_the_two_comparison_candidates`
holds both ids, and
`tests/test_narration_provider.py::TestWatsonxBackend::test_it_requests_the_active_candidate`
holds that a request asks for the active one.

**The comparison has not been run.** Nothing in the repo has generated narration
on watsonx, and the number the comparison needs, how often a first attempt is
grounded, is not measured yet for any model. `app/narration.py` exposes
`pass_rate` for it
(`tests/test_narration.py::TestPassRate::test_it_counts_first_attempts_only`).

### IBM Granite runs locally too

Development runs against `granite4:micro` on a local Ollama server, which is the
same Granite family as the active watsonx candidate and is not IBM Cloud. It is
set as `DEVELOPMENT_MODEL` in `app/narration_config.py`, with `num_gpu` 0 so
every layer stays on the CPU, because this laptop's graphics chip produces
garbage output
(`tests/test_narration_provider.py::TestConfig::test_the_development_model_runs_on_the_cpu`).
`docs/VOICE.md` records what two live runs of it produced, and
`scripts/narrate_once.py` is how to run another.

## Planned

Nothing in this section is in the repo. No code here reads any of it, and no
test covers it.

### Watson Text to Speech

Phase 5. Narration is text today and nothing speaks it, which `README.md` and
`docs/narration.md` both say.

| What | Value | Where it is recorded |
| ---- | ----- | -------------------- |
| Service | IBM Watson Text to Speech | `HANDOFF.md` |
| Instance | the Dallas instance in the team's IBM Cloud account | `HANDOFF.md` |
| Variables | `TTS_API_KEY`, `TTS_URL`, `TTS_VOICE` | `.env.example` |
| Working default voice | `en-GB_GeorgeExpressive` | `.env.example`, `HANDOFF.md` |
| Alternative voice | `en-GB_GeorgeNatural` | `.env.example`, `HANDOFF.md` |

The three variables are in `.env.example` and are read by no code in this repo,
which `.env.example` itself says. The values came from Shawn rather than from
the credentials file, which nothing here opens.

**The final voice pick is Shawn's, by ear, and is not to be settled from a spec
sheet.** `HANDOFF.md` records that, and that the two files in the gitignored
`voice_test/` are an earlier audition of the same pair.

### watsonx Orchestrate

Planned, and nothing about it exists here: no module, no variable in
`.env.example`, no test. When it arrives it gets a section above this one, with
the file and the test behind each statement, and this entry goes away.

## What this document deliberately does not claim

- That the watsonx backend has been run. It has not; see above.
- That the model comparison has a result. It has not been run.
- That any audio exists. None does.
- That `granite4:micro` narrates well. `docs/VOICE.md` carries what it actually
  produced, including a run where every model attempt was refused.
