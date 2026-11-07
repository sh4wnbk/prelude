"""One narration interface, two backends.

`NarrationProvider` is the interface narration code calls. Two backends satisfy
it:

  * `OllamaProvider`, the default. It talks to a local Ollama server and runs
    the development model from `app/narration_config.py`.
  * `WatsonxProvider`, used only when it is asked for by name. Building it
    reads the watsonx credentials from the environment and fails with the names
    of whichever are unset.

`provider()` returns the default backend unless it is given a name, so no code
path reaches watsonx without naming it.

Every request goes through a `Transport`: a callable taking a URL, an encoded
body and headers, returning the decoded JSON response. `post` is the real one,
built on `urllib`. Tests pass a transport that replays a response from
`tests/golden/`, so the suite never opens a socket; `tests/conftest.py` fails
the suite if anything tries.

This file never opens the credentials file itself. `app/credentials.py` does
that, reading from outside the repo, and a missing variable is reported here by
name for the user to go and look at themselves.

Standard library only, like every module in `app/` but the hosted
service in `app/api.py`.
"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping, Protocol, runtime_checkable

from app.credentials import describe
from app.credentials import load as load_credentials
from app.narration_config import (
    ACTIVE_CANDIDATE,
    CANDIDATES,
    Candidate,
    DEFAULT_PROVIDER,
    DEVELOPMENT_MODEL,
    Decoding,
)

# Ollama's local HTTP API. 127.0.0.1 rather than localhost, so the request does
# not depend on how the machine resolves a hostname.
OLLAMA_HOST = "http://127.0.0.1:11434"
OLLAMA_GENERATE_PATH = "/api/generate"

# watsonx.ai text generation, and the IAM exchange that authorises it. Both are
# taken from IBM's published schema rather than from memory; the citations are
# in docs/narration.md.
WATSONX_GENERATE_PATH = "/ml/v1/text/generation"
#: The chat endpoint, for a model the generation endpoint will not serve.
WATSONX_CHAT_PATH = "/ml/v1/text/chat"
WATSONX_API_VERSION = "2025-02-11"
IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"
IAM_GRANT_TYPE = "urn:ibm:params:oauth:grant-type:apikey"

#: The variables watsonx needs. The names come from `.env.example`, which is
#: the template in the repo; the values come from the credentials file outside
#: it. See `app/credentials.py`.
WATSONX_ENV_VARS = ("WATSONX_API_KEY", "WATSONX_PROJECT_ID", "WATSONX_URL")

#: A CPU-only generation is slow, so the timeout is generous.
#:
#: It is not generous enough for a reasoning model at `reasoning_effort`
#: high. The candidate run of 2026-10-31 read one slot and then lost a call to
#: `TimeoutError` after five minutes: a call that writes 14,000 completion
#: tokens before it answers takes longer than a call that writes 300.
#: `WatsonxProvider` takes a `timeout` for that reason, and
#: `scripts/narrator_candidates.py --timeout` is how a run sets one.
DEFAULT_TIMEOUT = 300.0

#: Length cap sent to watsonx. Ollama has no equivalent default worth setting.
DEFAULT_MAX_NEW_TOKENS = 200

#: The length cap the paid comparison sends instead. Two measurements set it.
#: The longest completion measured locally was 185 tokens a call against a cap
#: of 200, close enough that a longer narration would be cut off, fail the
#: ending rule for not reaching the goal, and be recorded as a model failure
#: that was really a cap. Then a smoke call found that `openai/gpt-oss-120b`
#: writes its reasoning into the same budget and spent all of 400 on it
#: without reaching an answer at all. 2000 is where both candidates finish.
#:
#: It lives here rather than in `app/narration_config.py` because that file is
#: held to carrying no variable name that could hide a credential, and this
#: one is a request parameter in a module that already sends them.
#:
#: **It is enough at `reasoning_effort` low and nowhere near enough at high.**
#: Measured on 2026-10-31, one goal-call prompt of 2,746 prompt tokens, the
#: same prompt both times:
#:
#: | Effort | Completion tokens | Finish | Answer |
#: | ------ | ----------------: | ------ | ------ |
#: | low | 295 | stop | 194 characters |
#: | high | 2,000 | length | none, all of it reasoning |
#: | high | 4,000 | length | none |
#: | high | 6,000 | length | none |
#: | high | 8,000 | length | none |
#: | high | 14,141 (cap 16,000) | stop | 269 characters |
#:
#: So high effort costs about fifty times what low costs on this prompt and
#: needs a cap around 16,000 to answer at all. `--max-new-tokens` on
#: `scripts/narrator_candidates.py` is how a run raises it, because the cap a
#: run needs is a property of the effort that run chose.
COMPARISON_MAX_NEW_TOKENS = 2000

#: Characters a token is worth, for the one figure here that has to be
#: estimated rather than read.
#:
#: Every other token count in this module comes off watsonx's own `usage`
#: object. `token_cap` cannot: it decides whether to send a call before the
#: call has been billed, and asking watsonx how many tokens a prompt holds is
#: a paid request sent to find out what a paid request will cost. Four
#: characters a token is the usual figure for English prose, and it is the
#: smaller half of the estimate anyway: a call's worst case is the prompt plus
#: the whole of `max_new_tokens`, which at effort high is 16,000 against a
#: prompt of under 3,000.
CHARACTERS_A_TOKEN = 4.0

#: Seconds before an IAM token's stated expiry that it is treated as expired.
#: A token that expires while a request is in flight is a 401 that costs a
#: retry, and a minute of slack is cheaper than finding out.
IAM_EXPIRY_MARGIN = 60.0


class NarrationProviderError(RuntimeError):
    """A provider could not be built, or answered with something unreadable."""


class AnsweredWithoutContent(NarrationProviderError):
    """The model spent its whole budget before it wrote an answer.

    `openai/gpt-oss-120b` at `reasoning_effort` high answers with
    `choices[0].message` holding a `reasoning` field, no `content` and
    `finish_reason` "length" when the cap stops it mid-thought. That is an
    attempt that produced no narration, not a backend that is broken, so
    `app/narration.py` records it as a failed attempt and retries, the way it
    does an ungrounded one. Before this existed, one such answer raised out of
    the retry loop and ended the run, which on a paid run of six slots throws
    away every candidate already written.

    The cause is a cap too small for the effort; `COMPARISON_MAX_NEW_TOKENS`
    has the measurements.
    """


class TokenCapReached(NarrationProviderError):
    """The run has been billed what it was allowed, so nothing more is sent.

    Raised before a call rather than after it, because a call already sent is
    a call already billed: a cap that notices afterwards is a report and not a
    cap. What it compares is the run's tally so far plus this call's worst
    case, so the cap is never passed rather than being passed once and then
    noticed.

    **Why there is a cap at all.** Task 9d ran at `reasoning_effort` high and
    cost about 817,000 tokens, and nothing in the run could have stopped it:
    the plan printed an estimate before anything was sent and then the run
    spent whatever it spent. `scripts/narrator_candidates.py` takes
    `--max-total-tokens` with no default for that reason, and this is what it
    arrives as.

    `scripts/narrator_candidates.py` keeps every candidate already written
    when it catches this, because the ones already paid for are the whole
    point of stopping rather than crashing.
    """


class MissingCredentials(NarrationProviderError):
    """A backend needs credentials that are not set.

    The message names the variables and says which file was looked in, and
    stops there. `CLAUDE.md` forbids putting a credential anywhere it could be
    read, so this reports the symptom and leaves the file to the user.
    """


@dataclass(frozen=True)
class Narration:
    """One generated passage, and what produced it.

    `model` is the id the backend reported, which is not always the id that was
    asked for, so it is read back from the response rather than assumed.
    """

    text: str
    provider: str
    model: str


class Transport(Protocol):
    """Sends one POST and returns the decoded JSON response."""

    def __call__(
        self,
        url: str,
        body: bytes,
        headers: Mapping[str, str],
    ) -> Mapping[str, Any]:
        ...


@runtime_checkable
class NarrationProvider(Protocol):
    """Turns a prompt into narration text."""

    name: str
    model: str

    def narrate(self, prompt: str) -> Narration:
        """Return the model's answer to `prompt`."""
        ...


def post(
    url: str,
    body: bytes,
    headers: Mapping[str, str],
    timeout: float = DEFAULT_TIMEOUT,
) -> Mapping[str, Any]:
    """POST `body` to `url` and return the decoded JSON response.

    The only function in this module that opens a connection.
    """
    request = urllib.request.Request(
        url, data=body, headers=dict(headers), method="POST"
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


class OllamaProvider:
    """The default backend: the development model on a local Ollama server.

    The server has to be running already. Ollama is started outside this repo
    and this class does not try to start it; a refused connection surfaces as
    the `urllib` error it is, because that is the symptom worth reading.
    """

    name = "ollama"

    def __init__(
        self,
        model: str | None = None,
        options: Mapping[str, Any] | None = None,
        host: str = OLLAMA_HOST,
        transport: Transport = post,
    ) -> None:
        self.model = model or DEVELOPMENT_MODEL.model
        self.options = dict(
            DEVELOPMENT_MODEL.options if options is None else options
        )
        self.host = host.rstrip("/")
        self._transport = transport

    @property
    def url(self) -> str:
        return self.host + OLLAMA_GENERATE_PATH

    def payload(self, prompt: str) -> dict[str, Any]:
        """The request body.

        Public because the golden recorder and the replaying test both need the
        exact body, and a recording is worth nothing if the replay sends
        something else.
        """
        return {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": dict(self.options),
        }

    def narrate(self, prompt: str) -> Narration:
        body = self._transport(
            self.url,
            json.dumps(self.payload(prompt)).encode("utf-8"),
            {"Content-Type": "application/json"},
        )
        if "response" not in body:
            raise NarrationProviderError(
                "Ollama answered without a 'response' field; its keys were "
                f"{sorted(body)}"
            )
        return Narration(
            text=body["response"],
            provider=self.name,
            model=body.get("model", self.model),
        )


def candidate_for(model: str | None) -> "Candidate | None":
    """The configured candidate a model id belongs to, or None.

    `None` for the model means the active candidate, which is the shipped
    path. A model id that is not one of `CANDIDATES` has no settings to
    inherit, which is the right answer: this is how a one-off model is tried
    without quietly picking up another model's endpoint.
    """
    if model is None:
        return ACTIVE_CANDIDATE
    for candidate in CANDIDATES:
        if candidate.model_id == model:
            return candidate
    return None


class WatsonxProvider:
    """The watsonx.ai backend, reached only by naming it.

    Construction reads the variables in `WATSONX_ENV_VARS` through
    `app/credentials.py`, which loads them from outside the repo, and raises
    `MissingCredentials` naming whichever is unset, so a missing credential
    fails before any request is sent rather than as a 401 later.

    The first `narrate` is two requests: the IAM exchange that turns the API
    key into a bearer token, then the generation call. **The token is cached
    for the life of the provider**, so later narrations are one request each.
    IBM states the token's lifetime in the exchange, and it is reused until
    `IAM_EXPIRY_MARGIN` before that, or until a call comes back 401, which is
    the case a clock cannot predict: a key revoked mid-run answers 401 and the
    next attempt fetches a fresh token rather than failing the run.

    It held no cache at first, on the grounds that nothing ran long enough to
    need one. The paid comparison in `scripts/narration_compare.py` runs more
    than two hundred generations, and one IAM exchange each is both waste and
    a good way to be rate limited.

    `decoding` pins how the model samples. Left unset the payload carries no
    decoding fields and watsonx uses its own default, which is greedy: three
    runs of a greedy model are one run three times. The comparison pins it so
    that two candidates are decoded identically and a difference between them
    is a difference between the models.

    `chat` sends the prompt to the chat endpoint rather than the generation
    one, for a model the generation endpoint will not serve. It is one
    endpoint for the whole comparison or none: a pass rate measured across two
    different APIs would be comparing those as much as the models.
    """

    name = "watsonx"

    def __init__(
        self,
        model: str | None = None,
        env: Mapping[str, str] | None = None,
        transport: Transport = post,
        api_version: str = WATSONX_API_VERSION,
        decoding: Decoding | None = None,
        chat: bool | None = None,
        max_new_tokens: int = DEFAULT_MAX_NEW_TOKENS,
        reasoning_effort: str | None = None,
        timeout: float | None = None,
        token_cap: int | None = None,
    ) -> None:
        env = load_credentials() if env is None else env
        missing = [name for name in WATSONX_ENV_VARS if not env.get(name)]
        if missing:
            # describe() reports variable names and no values, so this is safe
            # to print. It says which file was read, which is the question a
            # missing credential actually raises.
            raise MissingCredentials(
                "watsonx needs " + ", ".join(missing) + ", which is not set. "
                + describe().summary
                + ". .env.example lists the variable names."
            )
        # The settings a candidate needs travel with it, so a model id
        # switched in `app/narration_config.py` cannot ship with the endpoint
        # the other one wanted. An explicit argument still wins, which is
        # what the comparison script and the schema tests use.
        candidate = candidate_for(model)
        self.model = model or ACTIVE_CANDIDATE.model_id
        self.host = env["WATSONX_URL"].rstrip("/")
        self.api_version = api_version
        self._api_key = env["WATSONX_API_KEY"]
        self._project_id = env["WATSONX_PROJECT_ID"]
        # A timeout is the transport's argument rather than this class's, so a
        # run that needs a longer one gets it by wrapping the transport it was
        # given. Only when one is asked for: the recorded transports in the
        # tests take three arguments and are never handed a fourth.
        self.timeout = timeout
        if timeout is None:
            self._transport = transport
        else:
            def with_timeout(url, body, headers, inner=transport):
                return inner(url, body, headers, timeout=timeout)

            self._transport = with_timeout
        self.decoding = decoding
        self.chat = (
            (candidate.chat if candidate else False) if chat is None else chat
        )
        # Bound to the provider rather than passed to every call, because
        # `NarrationProvider` is `narrate(prompt)` and `app/narration.py`
        # calls it that way. A cap the pipeline cannot reach is a cap that
        # silently stays at its default on the run that needed it raised.
        self.max_new_tokens = max_new_tokens
        # Only a reasoning model has this, and only the chat endpoint carries
        # it. It is the one setting the paid comparison does not hold equal
        # between the candidates, because it is how one of them would ship:
        # a model that thinks for a thousand tokens before every narration is
        # one a fan waits through on every attempt.
        self.reasoning_effort = (
            (candidate.reasoning_effort if candidate else None)
            if reasoning_effort is None
            else reasoning_effort
        )
        self._token: str | None = None
        self._token_expires_at = 0.0
        #: Counted so a paid run can report what it spent on authorisation
        #: rather than estimate it.
        self.iam_exchanges = 0
        #: The tokens watsonx says it billed, summed over every call this
        #: provider made, read off the `usage` object the service returns.
        #: Counted for the same reason as `iam_exchanges`: Task 9d stated an
        #: estimate before the run, and an estimate is worth checking against
        #: what the run actually cost. A response without a `usage` object
        #: adds nothing rather than a guess.
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0
        #: The tokens this provider may be billed in all, or `None` for no
        #: cap. It is read against the tally above before every call: see
        #: `TokenCapReached` and `would_exceed_cap`.
        self.token_cap = token_cap

    @property
    def url(self) -> str:
        path = WATSONX_CHAT_PATH if self.chat else WATSONX_GENERATE_PATH
        query = urllib.parse.urlencode({"version": self.api_version})
        return f"{self.host}{path}?{query}"

    def payload(
        self, prompt: str, max_new_tokens: int = DEFAULT_MAX_NEW_TOKENS
    ) -> dict[str, Any]:
        """The request body, for whichever endpoint this provider is using.

        The generation shape is the documented one and is what
        `tests/test_narration_provider.py` holds to the golden fixture. The
        chat shape carries the same prompt as a single user message, and its
        decoding fields sit at the top level rather than under `parameters`,
        which is the chat API's own shape rather than a choice made here.
        """
        if self.chat:
            body: dict[str, Any] = {
                "model_id": self.model,
                "project_id": self._project_id,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_new_tokens,
            }
            if self.decoding is not None:
                body["temperature"] = self.decoding.temperature
                body["top_p"] = self.decoding.top_p
            if self.reasoning_effort is not None:
                body["reasoning_effort"] = self.reasoning_effort
            return body

        parameters: dict[str, Any] = {"max_new_tokens": max_new_tokens}
        if self.decoding is not None:
            parameters["decoding_method"] = "sample"
            parameters["temperature"] = self.decoding.temperature
            parameters["top_p"] = self.decoding.top_p
            parameters["top_k"] = self.decoding.top_k
        return {
            "model_id": self.model,
            "input": prompt,
            "project_id": self._project_id,
            "parameters": parameters,
        }

    def access_token(self) -> str:
        """Exchange the API key for an IAM bearer token."""
        body = urllib.parse.urlencode(
            {"grant_type": IAM_GRANT_TYPE, "apikey": self._api_key}
        ).encode("utf-8")
        answer = self._transport(
            IAM_TOKEN_URL,
            body,
            {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
        )
        if "access_token" not in answer:
            raise NarrationProviderError(
                "the IAM exchange answered without an 'access_token' field; "
                f"its keys were {sorted(answer)}"
            )
        self.iam_exchanges += 1
        # IBM states the lifetime in the exchange. A response without one is
        # treated as already expired rather than as lasting forever, so the
        # cache can only ever shorten the life of a token, never extend it.
        lifetime = float(answer.get("expires_in") or 0.0)
        self._token = answer["access_token"]
        self._token_expires_at = (
            time.monotonic() + lifetime - IAM_EXPIRY_MARGIN
            if lifetime
            else 0.0
        )
        return self._token

    def _authorisation(self) -> str:
        """The cached bearer token, exchanging for a new one if it has aged out."""
        if self._token is None or time.monotonic() >= self._token_expires_at:
            return self.access_token()
        return self._token

    def narrate(
        self, prompt: str, max_new_tokens: int | None = None
    ) -> Narration:
        """One generation, authorised with the cached token.

        A 401 is the one expiry a clock cannot predict: a token revoked or
        invalidated mid-run answers 401 whatever its stated lifetime said. So
        the token is dropped and fetched once more, and a second 401 is a real
        authorisation failure and is raised.
        """
        cap = (
            self.max_new_tokens if max_new_tokens is None else max_new_tokens
        )
        over = self.would_exceed_cap(prompt, cap)
        if over is not None:
            raise TokenCapReached(
                "watsonx has billed this run {:,} tokens and this call could "
                "take it to {:,}, past the {:,} it was allowed, so it was not "
                "sent".format(self.total_tokens, over, self.token_cap)
            )
        body = self._send(prompt, cap)
        self._count(body)
        if self.chat:
            return self._read_chat(body)
        return self._read_generation(body)

    def would_exceed_cap(
        self, prompt: str, max_new_tokens: int
    ) -> int | None:
        """What this call could take the run's tally to, if that is over the
        cap, and `None` where it is not or where there is no cap.

        The worst case rather than the likely one: the prompt estimated at
        `CHARACTERS_A_TOKEN`, plus the whole of `max_new_tokens`, because a
        reasoning model writes its reasoning into that budget and at effort
        high it used 14,141 of a 16,000 cap. A cap read against the likely
        cost is a cap a run can walk through.
        """
        if self.token_cap is None:
            return None
        would = (
            self.total_tokens
            + round(len(prompt) / CHARACTERS_A_TOKEN)
            + max_new_tokens
        )
        return would if would > self.token_cap else None

    def _count(self, body: Mapping[str, Any]) -> None:
        """Add what this call billed to the run's tally.

        Counted before the answer is read, so a call that answered with
        reasoning and no narration is counted too: it was billed whether or
        not it produced a line. Nothing is inferred from a response carrying
        no `usage` object.
        """
        usage = body.get("usage")
        if not isinstance(usage, Mapping):
            return
        self.prompt_tokens += int(usage.get("prompt_tokens") or 0)
        self.completion_tokens += int(usage.get("completion_tokens") or 0)
        self.total_tokens += int(usage.get("total_tokens") or 0)

    def _send(self, prompt: str, max_new_tokens: int) -> Mapping[str, Any]:
        encoded = json.dumps(self.payload(prompt, max_new_tokens)).encode("utf-8")

        def once() -> Mapping[str, Any]:
            return self._transport(
                self.url,
                encoded,
                {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": f"Bearer {self._authorisation()}",
                },
            )

        try:
            return once()
        except urllib.error.HTTPError as failure:
            if failure.code != 401:
                raise
        self._token = None
        return once()

    def _read_generation(self, body: Mapping[str, Any]) -> Narration:
        results = body.get("results") or []
        if not results or "generated_text" not in results[0]:
            raise NarrationProviderError(
                "watsonx answered without results[0].generated_text; its keys "
                f"were {sorted(body)}"
            )
        return Narration(
            text=results[0]["generated_text"],
            provider=self.name,
            model=body.get("model_id", self.model),
        )

    def _read_chat(self, body: Mapping[str, Any]) -> Narration:
        """The chat endpoint's answer, which nests the text one level deeper."""
        choices = body.get("choices") or []
        choice = (choices[0] or {}) if choices else {}
        message = choice.get("message")
        if message and "content" not in message and "reasoning" in message:
            usage = body.get("usage") or {}
            raise AnsweredWithoutContent(
                "watsonx answered with reasoning and no narration: "
                f"finish_reason {choice.get('finish_reason')!r}, "
                f"{usage.get('completion_tokens')} completion token(s) of a "
                f"{self.max_new_tokens} cap, all of them before it wrote "
                "anything"
            )
        if not message or "content" not in message:
            raise NarrationProviderError(
                "watsonx chat answered without choices[0].message.content; "
                f"its keys were {sorted(body)}"
            )
        return Narration(
            text=message["content"],
            provider=self.name,
            model=body.get("model_id", self.model),
        )


#: Every backend, by the name `provider()` accepts.
BACKENDS = {
    OllamaProvider.name: OllamaProvider,
    WatsonxProvider.name: WatsonxProvider,
}


def provider(name: str | None = None, **kwargs: Any) -> NarrationProvider:
    """Return a narration provider.

    With no name this is `DEFAULT_PROVIDER` from `app/narration_config.py`,
    which is Ollama. watsonx comes back only when "watsonx" is passed, which is
    what keeps a development run from reaching a paid endpoint by accident.
    """
    chosen = DEFAULT_PROVIDER if name is None else name
    if chosen not in BACKENDS:
        raise NarrationProviderError(
            f"unknown narration provider {chosen!r}; "
            f"the backends are {', '.join(sorted(BACKENDS))}"
        )
    return BACKENDS[chosen](**kwargs)
