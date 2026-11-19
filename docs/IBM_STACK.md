# The IBM stack

Which IBM parts this project runs on. Built is what is in the repo at this
commit, with the file and the test behind each statement. Planned is anything
not yet built, labelled as planned, which is what `CLAUDE.md` requires; it is
empty at this commit.

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

Seventeen sessions, one export each with the screenshot of its task summary,
committed rather than ignored because the submission guide requires them to be
present in the final repo. `bob_sessions/README.md` is the index and the
scrubbing rule.

| Phase | Task | Export | Screenshot | Export committed in |
| ----: | ---- | ------ | ---------- | ------------------- |
| 3 | 1. build `StatsBombEventFeed` | `bob_sessions/phase3_task1_eventfeed.md` | `bob_sessions/phase3_task1_eventfeed.png` | `7970216` |
| 3 | 2. end event windows at the goal shot | `bob_sessions/phase3_task2_window_fix.md` | `bob_sessions/phase3_task2_window_fix.png` | `7970216` |
| 4 | 3. add `buildup` | `bob_sessions/phase4_task3_buildup.md` | `bob_sessions/phase4_task3_buildup.png` | `e0bbbdd` |
| 4 | 4. the orchestrator | `bob_sessions/phase4_task4_orchestrator.md` | `bob_sessions/phase4_task4_orchestrator.png` | `be0426f` |
| 4 | 5. the game-focused header | `bob_sessions/phase4_task5_header.md` | `bob_sessions/phase4_task5_header.png` | `4826671` |
| 4 | 6. the header on the moment card | `bob_sessions/phase4_task6_card_header.md` | `bob_sessions/phase4_task6_card_header.png` | `95341d1` |
| 4 | 7. the screen copy | `bob_sessions/phase4_task7_screen_copy.md` | `bob_sessions/phase4_task7_screen_copy.png` | `76e0d15` |
| 4 | 8. where the 1986 fan steps away | `bob_sessions/phase4_task8_step_away.md` | `bob_sessions/phase4_task8_step_away.png` | `3380bf3` |
| 4 | 9. the listener card | `bob_sessions/phase4_task9_listener_card.md` | `bob_sessions/phase4_task9_listener_card.png` | `4f12bea` |
| 4 | 10. the Profile screen | `bob_sessions/phase4_task10_profile.md` | `bob_sessions/phase4_task10_profile.png` | `b2d29a2` |
| 5 | 11. audio playback on the moment card | `bob_sessions/phase5_task11_player.md` | `bob_sessions/phase5_task11_player.png` | `076e914` |
| 5 | 12. the narrators on Profile | `bob_sessions/phase5_task12_narrators.md` | `bob_sessions/phase5_task12_narrators.png` | `d0837ac` |
| 5 | 13. rename the persona id from mate to buddy | `bob_sessions/phase5_task13_buddy_rename.md` | `bob_sessions/phase5_task13_buddy_rename.png` | `473b98e` |
| 5 | 14. the narrator picker | `bob_sessions/phase5_task14_narrator_picker.md` | `bob_sessions/phase5_task14_narrator_picker.png` | `9f98e91` |
| 6 | 15. the OpenAPI file watsonx Orchestrate imports | `bob_sessions/phase6_task15_orchestrate_spec.md` | `bob_sessions/phase6_task15_orchestrate_spec.png` | `39856bd` |
| 6 | a read-only review of the app | `bob_sessions/phase6_review_app.md` | `bob_sessions/phase6_review_app.png` | `927ad9e` |
| 7 | the tagline | `bob_sessions/phase7_tagline.md` | `bob_sessions/phase7_tagline.png` | `f40af46` |
| 7 | three README claims, stopped at the cost limit with nothing committed | `bob_sessions/phase7_readme_claims.md` | `bob_sessions/phase7_readme_claims.png` | `788b5a4` |
| 7 | a read-only score against the lab rubric, run after the Bobalytics export | `bob_sessions/phase7_rubric_review.md` | `bob_sessions/phase7_rubric_review.png` | `00c3110` |

The commit above is the one that added the export, read with
`git log --diff-filter=A`. The commit the work itself landed in is the status
line at the head of that task in `docs/bob_brief.md`.

The last four rows carry no numbered task, because `docs/bob_brief.md` ends at
Task 15 and each was run to a brief written outside it.

`bob_sessions/README.md` carries a Bobcoin figure for every session: seven read
from the screenshots, one from Bob's cost-limit message, and the rest from the
Bobalytics export committed beside them. That export totals
by day, so where sessions shared a day the row gives the day's total and says
which sessions it covers.

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

| Candidate | `model_id` | Label | Endpoint | Reasoning effort |
| --------- | ---------- | ----- | -------- | ---------------- |
| IBM Granite | `ibm/granite-4-h-small` | Granite 4 H Small | chat | not applicable |
| GPT OSS, served on watsonx | `openai/gpt-oss-120b` | GPT OSS 120B | chat | low |

**`ACTIVE_CANDIDATE` is the GPT OSS one, and Shawn picked it on the Task 4b
results.** Granite was active first because it is the IBM model and this
project runs on IBM's stack, and the comparison existed to test that choice
rather than assume it. It tested it: `openai/gpt-oss-120b` wrote 33 of 33
narrations that `app/grounding.py` accepted on the first attempt, with no
retry and no fallback, against Granite's 16 of 54 with 23 fallbacks, and it is
cheaper per narration because it does not retry. `docs/narration_eval.md` holds
the run.

**The settings each candidate needs travel with it.** The endpoint and the
reasoning effort are columns of the table above because they are on
`Candidate` in `app/narration_config.py`, not arguments at a call site: a
model id switched without its endpoint is a model that answers with the tail
of its own prompt, which is what Task 4b found on the generation endpoint.
`tests/test_narration_provider.py::TestTheShippedSettings::test_the_default_provider_sends_the_active_candidates_settings`
holds the shipped path to it, and
`tests/test_narration_provider.py::TestTheShippedSettings::test_a_model_that_is_not_a_candidate_inherits_nothing`
holds that a model which is not a candidate picks up nobody else's.

Switching is still one line, and
`tests/test_narration_provider.py::TestConfig::test_exactly_one_candidate_is_active`
asserts only that the active candidate is one of the two, so flipping it does
not break the suite.
`tests/test_narration_provider.py::TestConfig::test_the_two_comparison_candidates`
holds both ids, and
`tests/test_narration_provider.py::TestWatsonxBackend::test_it_requests_the_active_candidate`
holds that a request asks for the active one.

**The comparison has been run**, which is what Task 4b above was: 87
narrations over 155 generation calls across the two candidates, with the
first-attempt grounded rate measured for both and reported per arm.
`docs/narration_eval.md` holds the run, the arms and what it cost, and the
records it was written from are in `docs/narration_runs/`. The number it turns
on is the one `app/narration.py` exposes as `pass_rate`
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

### Watson Text to Speech

Phase 5. `app/tts.py` is the backend: it takes a header, a narration, a
persona and a situation, and returns the audio bytes the service sent. The
format is the caller's, through `accept`: `WAV_ACCEPT` is the default and is
what the probe measured, and `MP3_ACCEPT` is what the recordings the site
ships are asked for, because a WAV of a twenty second narration is an order of
magnitude larger than the MP3 of it and these files live in the repo.

**The six recordings the site serves were made with it**, by
`scripts/tts_hero.py` on 2026-11-07, one file per `hero.voice_for` key per
hero goal, for 2,403 billed characters against the 3,500 the run's `--budget`
allowed:

| File, under `app/web/assets/audio/` | Voice | Billed |
| ----------------------------------- | ----- | -----: |
| `3750191_storyteller_neutral.mp3` | `en-US_EmmaNatural` | 371 |
| `3750191_buddy_scored.mp3` | `en-US_EthanNatural` | 346 |
| `3750191_buddy_conceded.mp3` | `en-US_EthanNatural` | 324 |
| `3869685_storyteller_neutral.mp3` | `en-US_EmmaNatural` | 485 |
| `3869685_buddy_scored.mp3` | `en-US_EthanNatural` | 449 |
| `3869685_buddy_conceded.mp3` | `en-US_EthanNatural` | 428 |
| **total** | | **2,403** |

2,865 characters were submitted and 2,343 spoken; the difference is the
pronunciation markup, which IBM bills and does not speak.

**No screen calls `app/tts.py` at runtime.** The moment card's player plays
the committed MP3 for the listener's own key, looked up in `hero.audio` in
`app/web/matches.json`, and nothing in `app/web/` names the module or the
service: the speech is bought once, by hand, and shipped as files
(`tests/test_narration_player.py::TestTheAudioMap`,
`tests/test_narration_player.py::TestThePlayer`).

`scripts/tts_probe.py` is what measured the service before any of it was
written: one fixed sentence per arm on three candidate voices, with the audio
that came back measured rather than assumed. It writes WAV files outside the
repo.

| Behaviour | Test |
| --------- | ---- |
| it replays a real recorded exchange | `tests/test_tts.py::TestTheGoldenIsARecording::test_it_says_it_is_a_recording` |
| the request matches the one that was recorded | `tests/test_tts.py::TestTheReplaySendsWhatWasRecorded::test_the_request_matches_the_one_that_was_recorded` |
| it returns the bytes the service sent, unmodified | `tests/test_tts.py::TestTheReplaySendsWhatWasRecorded::test_it_returns_exactly_the_bytes_the_service_sent` |
| one request, since the key goes in directly and there is no token to exchange | `tests/test_tts.py::TestTheReplaySendsWhatWasRecorded::test_it_sends_one_request` |
| a narration still carrying its citation tags is refused | `tests/test_tts.py::TestItRefusesTaggedText` |
| the rate and pitch are sent only once decided | `tests/test_tts.py::TestTheRequestShape::test_an_unset_parameter_is_not_sent_and_a_zero_one_is` |
| pauses reach the Caller's voice and no other | `tests/test_tts.py::TestOnlyTheCallerGetsPauses` |
| no request object holds the host or the token | `tests/test_tts.py::TestNothingSecretIsInTheRequest` |
| a missing credential is named and nothing is sent | `tests/test_tts.py::TestCredentials::test_a_missing_credential_is_named_and_nothing_is_sent` |

**The suite makes no speech call.** `tests/golden/tts_synthesize.json` is a
real exchange, recorded once by `scripts/record_tts_golden.py` at a cost of 83
submitted characters, and the fixture carries its own provenance block saying
what it holds: the request, and the first 128 bytes of the response with the
full length and SHA-256 of the rest. Unlike the watsonx fixture, this one is a
recording and says so.

| What | Value |
| ---- | ----- |
| Service | IBM Watson Text to Speech |
| Endpoint | `POST /v1/synthesize`, from IBM's published API |
| Auth | basic, with the literal user name `apikey`, which is IBM's documented example for this service |
| Format the probe asked for | `audio/wav`, and all three voices answered 24000 Hz, 1 channel, 16 bit |
| Variables read | `TTS_API_KEY`, `TTS_URL`, through `app/credentials.py` |
| Candidate voices | `en-AU_HeidiNatural`, `en-US_EmmaNatural`, `en-US_EthanNatural` |

**What the probe found is in `docs/VOICE.md`**, with the numbers. In short:
`<prosody>` is ignored on all three voices, which is what IBM documents for
Natural voices; `rate_percentage` works on all three; `pitch_percentage` works
upward and is ignored at -20; `<break>` works on `en-AU_HeidiNatural` alone;
and `<phoneme>` works on all three, which took a second arm to establish
because the first one asked for the pronunciation the voices already used in
that one sentence.

**No test covers the probe,** and that is the same decision as four of the
five gates: it is a measuring instrument whose evidence is its own output, and
a test standing in for the service would be testing the stand-in.
`scripts/check_vocabulary.py` is the one exception, because half of what it
does is a rule a test can hold instead of a report somebody reads:
`tests/test_vocabulary.py` imports it and fails when a flagged word is on
neither review list. `tests/conftest.py` blocks the network in every test, so
nothing in the suite can reach the service by accident.

**The three voices are recorded against the personas.** `app/personas.py`
carries one each, with `voice_confirmed` true, which says Shawn chose them:
the Caller is `en-AU_HeidiNatural`, the Storyteller `en-US_EmmaNatural` and
the Buddy `en-US_EthanNatural`
(`tests/test_personas.py::TestTheVoices::test_every_voice_is_one_the_probe_measured`).

**The delivery is set too, and it does not live on the persona.**
`app/delivery.py` holds eight rows, one per persona per situation less the
neutral row the Buddy cannot have, each with a rate, a pitch and, for the
Caller alone, two pauses; all three personas carry `prosody_confirmed` true
(`tests/test_delivery.py::TestTheTableHasEveryRowAndNoOthers`,
`tests/test_delivery.py::TestTheValuesAreShawnsAndTheTableSaysSo`). The values
are Shawn's by ear. The one figure still unmeasured is the Caller's rate
ceiling in words per minute, and a test says so rather than leaving it to be
noticed
(`tests/test_delivery.py::TestTheValuesAreShawnsAndTheTableSaysSo::test_the_callers_rate_ceiling_is_not_measured_yet`).

**`TTS_VOICE` is still read by no code.** `.env.example` carries it as the
working default from before the probe, and it names a voice no persona uses.

**The final voice pick is Shawn's, by ear, and is not to be settled from a spec
sheet.** `HANDOFF.md` records that, and that the two files in the gitignored
`voice_test/` are an earlier audition of a different pair.

### watsonx Orchestrate

An agent in watsonx Orchestrate answers a fan's question about one of the two
matches. It answers from two read-only tools and from nothing else: it lists
the goals, and it hands over the narration Prelude already wrote for the one
goal it narrates, in the voice that fan is entitled to hear. The agent lives
in Orchestrate's own UI, so what is in this repo is the tools it imports and
the words it is given.

| What | Where |
| ---- | ----- |
| the two tools, as one OpenAPI file the agent imports | `orchestrate/prelude_tools.yaml` |
| the service they call | `app/api.py`, deployed at <https://prelude-api.onrender.com> |
| the instructions pasted into the agent, and the reason for each | `docs/orchestrate_agent.md` |
| the agent answering both matches, live | `docs/evidence/orchestrate_2022_argentina_fan.png` and `docs/evidence/orchestrate_1986_neutral.png` |

The imported file is held to the service it describes rather than to a copy of
it. `tests/test_orchestrate_spec.py` reads `app.openapi()` and compares: the
two operations, their parameters, which are required, the enums, the response
fields and every status code.

| Behaviour | Test |
| --------- | ---- |
| the file describes exactly the two tools, and `/health` is not one | `tests/test_orchestrate_spec.py::TestTheTwoOperations::test_the_file_holds_exactly_the_two` |
| every field, status code and response type it declares is the service's own | `tests/test_orchestrate_spec.py::TestTheResponses` |
| it asks for no credential and names no other host | `tests/test_orchestrate_spec.py::TestItAsksForNoCredentials`, `tests/test_orchestrate_spec.py::TestWhatTheFileMayNotCarry::test_it_names_no_other_host` |
| the matches the agent is told it serves are the app's own | `tests/test_orchestrate_agent.py::TestTheMatchesItServes` |
| the answer is the narration text and nothing added to it | `tests/test_orchestrate_agent.py::TestTheAnswerIsTheNarration` |
| the narration is handed over word for word | `tests/test_orchestrate_agent.py::TestTheVerbatimRule` |
| the label is never written by the agent | `tests/test_orchestrate_agent.py::TestTheLabelRule` |

**Nothing here holds an Orchestrate credential.** The tools call a public
read-only URL, `app/api.py` reads no environment variable and makes no paid
call, and `.env.example` gains no name for this.

**It is not a fourth input.** The tools serve what `data/raw/` and the frozen
narrations already hold, which is what `app/api.py` exists for.

## Planned

Nothing. Every IBM part this project uses is in the section above, with the
file and the test behind each statement. An entry comes back here the day
something is planned and not yet built.

## What this document deliberately does not claim

- That `granite4:micro` narrates well. `docs/VOICE.md` carries what it actually
  produced, including a run where every model attempt was refused.
- That the watsonx pipeline wrote the six narrations the site speaks. It did
  not: they were drafted with an AI assistant, edited by Shawn and verified by
  the grounding check, which `README.md` and `scripts/authored_narrations.py`
  both say. The pipeline's own candidates are in `docs/narration_runs/`.
- That the Caller has been heard in the app. It has no recording:
  `hero.voice_for` sends no listener to it, so there are six recordings rather
  than eight.
- That the delivery numbers have been measured from real audio. They are
  Shawn's by ear, and the words per minute that would put a ceiling on the
  Caller's rate is still unmeasured.
