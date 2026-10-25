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

This file never opens `.env`. The values arrive through the environment, and a
missing one is reported by name for the user to go and look at themselves.

Standard library only, like the rest of `app/`.
"""

import json
import os
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping, Protocol, runtime_checkable

from app.narration_config import (
    ACTIVE_CANDIDATE,
    DEFAULT_PROVIDER,
    DEVELOPMENT_MODEL,
)

# Ollama's local HTTP API. 127.0.0.1 rather than localhost, so the request does
# not depend on how the machine resolves a hostname.
OLLAMA_HOST = "http://127.0.0.1:11434"
OLLAMA_GENERATE_PATH = "/api/generate"

# watsonx.ai text generation, and the IAM exchange that authorises it. Both are
# taken from IBM's published schema rather than from memory; the citations are
# in docs/narration.md.
WATSONX_GENERATE_PATH = "/ml/v1/text/generation"
WATSONX_API_VERSION = "2025-02-11"
IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"
IAM_GRANT_TYPE = "urn:ibm:params:oauth:grant-type:apikey"

#: The variables watsonx needs. The names come from `.env.example`.
WATSONX_ENV_VARS = ("WATSONX_API_KEY", "WATSONX_PROJECT_ID", "WATSONX_URL")

#: A CPU-only generation is slow, so the timeout is generous.
DEFAULT_TIMEOUT = 300.0

#: Length cap sent to watsonx. Ollama has no equivalent default worth setting.
DEFAULT_MAX_NEW_TOKENS = 200


class NarrationProviderError(RuntimeError):
    """A provider could not be built, or answered with something unreadable."""


class MissingCredentials(NarrationProviderError):
    """A backend needs environment variables that are not set.

    The message names the variables and stops there. `CLAUDE.md` forbids
    opening `.env`, so this reports the symptom and leaves the file to the
    user.
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


class WatsonxProvider:
    """The watsonx.ai backend, reached only by naming it.

    Construction reads the variables in `WATSONX_ENV_VARS` and raises
    `MissingCredentials` naming whichever is unset, so a missing credential
    fails before any request is sent rather than as a 401 later.

    Each `narrate` is two requests: the IAM exchange that turns the API key
    into a bearer token, then the generation call. The token is not cached,
    because nothing here runs long enough for that to matter and a cache would
    mean holding it somewhere.
    """

    name = "watsonx"

    def __init__(
        self,
        model: str | None = None,
        env: Mapping[str, str] | None = None,
        transport: Transport = post,
        api_version: str = WATSONX_API_VERSION,
    ) -> None:
        env = os.environ if env is None else env
        missing = [name for name in WATSONX_ENV_VARS if not env.get(name)]
        if missing:
            raise MissingCredentials(
                "watsonx needs " + ", ".join(missing) + " in the environment. "
                ".env.example lists the variable names."
            )
        self.model = model or ACTIVE_CANDIDATE.model_id
        self.host = env["WATSONX_URL"].rstrip("/")
        self.api_version = api_version
        self._api_key = env["WATSONX_API_KEY"]
        self._project_id = env["WATSONX_PROJECT_ID"]
        self._transport = transport

    @property
    def url(self) -> str:
        query = urllib.parse.urlencode({"version": self.api_version})
        return f"{self.host}{WATSONX_GENERATE_PATH}?{query}"

    def payload(
        self, prompt: str, max_new_tokens: int = DEFAULT_MAX_NEW_TOKENS
    ) -> dict[str, Any]:
        """The generation request body."""
        return {
            "model_id": self.model,
            "input": prompt,
            "project_id": self._project_id,
            "parameters": {"max_new_tokens": max_new_tokens},
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
        return answer["access_token"]

    def narrate(
        self, prompt: str, max_new_tokens: int = DEFAULT_MAX_NEW_TOKENS
    ) -> Narration:
        token = self.access_token()
        body = self._transport(
            self.url,
            json.dumps(self.payload(prompt, max_new_tokens)).encode("utf-8"),
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {token}",
            },
        )
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
