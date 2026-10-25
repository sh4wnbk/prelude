# Narration: config, providers, prompt and grounding

What exists at this commit is the config, the provider layer, the prompt, the
grounding check and the pipeline that ties them together. **No narration
reaches a screen, and none of it is spoken.** This document describes the
modules that are in the repo, where their API shapes came from, and why the
test suite can prove what it proves. `docs/VOICE.md` is the written voice the
prompt and the check between them enforce.

## The three models, and the two jobs

`app/narration_config.py` is committed, and holds every model id the project
uses. A model id is not a credential: it records which model produced a line, so
it belongs where a reader can see it. `.env` holds credentials only, and
`.env.example` no longer lists a model id.

| Constant | Model | Where it runs | Job |
| -------- | ----- | ------------- | --- |
| `GRANITE_4_H_SMALL` | `ibm/granite-4-h-small` | watsonx.ai | comparison candidate |
| `GPT_OSS_120B` | `openai/gpt-oss-120b` | watsonx.ai | comparison candidate |
| `DEVELOPMENT_MODEL` | `granite4:micro` | Ollama, local | development |

`ACTIVE_CANDIDATE` names the candidate a watsonx request uses. Granite starts
active because it is the IBM model and this project runs on IBM's stack; the
comparison exists to test that choice rather than assume it. Switching
candidates is one line, and the suite does not pin which one is active, only
that it is one of the two.

### The development model runs on the CPU

`DEVELOPMENT_MODEL.options` is `{"num_gpu": 0}`, which keeps every layer off the
graphics chip. On this laptop that is not a speed tradeoff: the graphics chip
produces garbage output, so offloading a layer is the difference between usable
text and noise. The option is load-bearing, a test stands over it, and the
recorded response in `tests/golden/ollama_development_model.json` was recorded
with it set.

## One interface, two backends

`app/narration_provider.py` holds the interface and both backends. Standard
library only, like the rest of `app/`.

| Name | What it is |
| ---- | ---------- |
| `NarrationProvider` | the protocol narration code calls: `narrate(prompt) -> Narration` |
| `Narration` | the result: `text`, `provider`, `model` |
| `OllamaProvider` | the default backend, against a local Ollama server |
| `WatsonxProvider` | the watsonx.ai backend, reached only by naming it |
| `provider(name=None)` | returns the default unless given a name |
| `post` | the real transport, and the only function here that opens a connection |

### watsonx is never reached by accident

`provider()` with no argument returns `DEFAULT_PROVIDER`, which is `"ollama"`.
`WatsonxProvider` comes back only from `provider("watsonx")`. Three tests cover
it: the default is Ollama, the default is not watsonx, and an unknown name is an
error rather than a silent fall back to the default.

Building `WatsonxProvider` reads `WATSONX_API_KEY`, `WATSONX_PROJECT_ID` and
`WATSONX_URL` from the environment and raises `MissingCredentials` naming
whichever is unset, before any request is sent. It never opens `.env`:
`CLAUDE.md` forbids that, so the symptom is reported by variable name and the
file is left to the user.

### Where the API shapes came from

The watsonx request and response shapes were read from IBM's published schema,
not written from memory. `narrate` is two requests: the IAM exchange that turns
the API key into a bearer token, then the generation call.

| What | Value | Source |
| ---- | ----- | ------ |
| Generation endpoint | `POST {WATSONX_URL}/ml/v1/text/generation?version=2025-02-11` | IBM OpenAPI schema, IBM docs |
| Request body | `model_id`, `input`, `project_id`, `parameters.max_new_tokens` | IBM OpenAPI schema |
| Response body | `model_id`, `created_at`, `results[].generated_text`, `generated_token_count`, `input_token_count`, `stop_reason` | IBM OpenAPI schema |
| IAM endpoint | `POST https://iam.cloud.ibm.com/identity/token` | IBM OpenAPI schema `securitySchemes` |
| IAM grant type | `urn:ibm:params:oauth:grant-type:apikey` | IBM OpenAPI schema `securitySchemes` |
| IAM response field | `access_token` | IBM Cloud IAM docs |

Citations:

- [`watsonx-openapi.json`, IBM's assistant-toolkit starter kit](https://github.com/watson-developer-cloud/assistant-toolkit/blob/master/integrations/extensions/starter-kits/language-model-watsonx/watsonx-openapi.json)
- [Generating text, IBM watsonx.ai documentation](https://www.ibm.com/docs/SSLSRPV_latest/wsj/analyze-data/fm-api-generation.html)
- [watsonx.ai API reference, IBM Cloud](https://cloud.ibm.com/apidocs/watsonx-ai)

The Ollama shape was not read from documentation at all. It was read off a real
response; see below.

## The tests make no network calls

Every request goes through a `Transport`: a callable taking a URL, an encoded
body and headers, returning the decoded JSON response. `post` is the real one.
Tests pass one that replays a golden file, so no test calls a model.

That is enforced rather than promised. `tests/conftest.py` installs an autouse
fixture that replaces `urllib.request.urlopen` and `socket.socket.connect` with
functions that raise, for every test in the suite. Two tests in
`TestNoNetwork` check the guard itself, because a guard nobody tests is a guard
that can quietly stop working.

### The two golden files are not the same kind of thing

This distinction matters, and the tests assert that each file declares which it
is.

**`tests/golden/ollama_development_model.json` is a recording.** A real call
went to a real local Ollama server running `granite4:micro` with `num_gpu` 0,
and both halves of it are in the file verbatim.
`scripts/record_narration_golden.py` made it and can make it again. Its
response half is therefore evidence: Ollama really does answer in that shape,
and with that option set the output is coherent English.

**`tests/golden/watsonx_text_generation.json` is a schema fixture**, written by
hand from the sources cited above. No watsonx call has been made from this
repo, so there is nothing to record: that would mean a paid call against live
credentials, and `.env` is out of reach. Its response half is not evidence of
what watsonx returns, only of what IBM documents it returns. What the tests do
get from it is real, though: the request half was written from the schema by
hand, the provider builds its request independently, and the two agreeing is a
genuine check that the code matches the documented API. If IBM's schema is
wrong, these tests cannot know it.

The fixture's values are obvious placeholders. The token is not a token, and
`generated_text` reads `PLACEHOLDER FIXTURE TEXT, NOT MODEL OUTPUT.` so it can
never be mistaken for narration.

## Recording a fresh golden

The recorder is run by hand and is not part of the suite. It needs a local
Ollama server with the development model pulled:

```
ollama pull granite4:micro
.\.venv-prelude\Scripts\python.exe -I scripts\record_narration_golden.py
```

It writes the one request it sent and the one response it got, plus a
provenance block. The replaying test rebuilds the request from
`OllamaProvider.payload` and asserts it matches the recorded one, so changing
the request body fails the test rather than quietly invalidating the recording.

## The prompt, the check and the pipeline

| Module | What it does |
| ------ | ------------ |
| `app/narration_prompt.py` | `Facts` read off one `Buildup`, the prompt built from them, and the fallback narration |
| `app/grounding.py` | decides whether a narration's claims trace back to the data |
| `app/narration.py` | generates, checks, retries, falls back, and records every attempt |

**`Facts` is the whole of what a narration may mention**: the players, the
teams, the minutes, the actions, and the goal's own shot type and body part.
Every field is copied from a raw record. Nothing is counted, ranked or
inferred, because a fact the extractor invented is a fact the check would then
happily approve.

**The prompt states the rules the check enforces**, in the same words, because
a prompt asking for less than the check requires would set the model up to fail
and the retry would not help it.

**The check is whole-narration.** `CLAUDE.md` gives no partial credit, so a
narration passes or fails together. It reports every failing claim rather than
the first, which is what a retry and the failure log both need.

**The pipeline never returns anything ungrounded.** A failing narration is
generated again, up to twice. If it still fails, the fallback assembles a short
plain narration straight from the events, which is grounded by construction and
is checked anyway. If even that failed there would be nothing safe to say, and
`narrate` raises instead of returning something unlabelled.

**The pass rate counts first attempts only.** `Narrated.first_attempt_grounded`
is the number to measure; counting retries would hide how often a model drifts.

### What the check cannot do

It verifies that everything a line names is in the data. It does not verify
that the line's reading of those facts is right. `docs/VOICE.md` works through
a line that passes the check and still describes something that did not happen.
The check catches invention, which is the failure a language model actually
has; it does not catch misdescription.

## What is not built

- No audio. Narration text is not spoken, and the TTS variables in
  `.env.example` are unused by any code in the repo. Watson Text to Speech is
  Phase 5; `HANDOFF.md` records the service and voice details it will need.
- No screen reads narration. The prompt, the check and the pipeline are
  callable from Python and from nowhere else.
- No measured pass rate. `app/narration.py` exposes `pass_rate`, and nothing
  in the repo runs it over the nine goals and writes the result down.
