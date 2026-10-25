"""Which model narrates, and where it runs.

A model id is not a credential. It records which model produced a line of
narration, so it belongs in the repo where a reader can see it rather than in
`.env`. `.env` holds the watsonx credentials and the TTS credentials; it no
longer carries a model id, and `.env.example` no longer lists one.

Three models appear here, for two different jobs:

  * Two comparison candidates on watsonx.ai. Phase 4 compares them for
    narration quality, and `ACTIVE_CANDIDATE` names the one in use.
  * One development model on Ollama, which is what runs during development and
    what the default provider uses.

Nothing in this file reads the environment, opens a connection, or chooses a
backend at import time. `app/narration_provider.py` does all of that.
"""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True)
class Candidate:
    """One watsonx.ai model under comparison for narration.

    `model_id` is the id watsonx expects in a request body. `label` is for
    reports and commit messages, not for app output.
    """

    model_id: str
    label: str


GRANITE_4_H_SMALL = Candidate("ibm/granite-4-h-small", "Granite 4 H Small")
GPT_OSS_120B = Candidate("openai/gpt-oss-120b", "GPT OSS 120B")

#: The two models the comparison is between, in no significant order.
CANDIDATES: tuple[Candidate, ...] = (GRANITE_4_H_SMALL, GPT_OSS_120B)

#: The candidate a watsonx request uses. Granite starts active because it is
#: the IBM model and this project runs on IBM's stack; the comparison exists to
#: test that choice rather than assume it. Switching candidates is this one
#: line, and `tests/test_narration_provider.py` asserts only that the active
#: candidate is one of `CANDIDATES`, so flipping it does not break the suite.
ACTIVE_CANDIDATE = GRANITE_4_H_SMALL


@dataclass(frozen=True)
class DevelopmentModel:
    """The model development runs against, served locally by Ollama.

    `options` goes through to Ollama's `options` field untouched.
    """

    model: str
    options: Mapping[str, Any]


DEVELOPMENT_MODEL = DevelopmentModel(
    model="granite4:micro",
    # num_gpu 0 keeps every layer on the CPU. This laptop's graphics chip
    # produces garbage output, so offloading a layer to it is not a speed
    # tradeoff: it is the difference between usable text and noise. Raise it
    # only on a machine whose output has been checked.
    options=MappingProxyType({"num_gpu": 0}),
)

#: The backend `app.narration_provider.provider()` returns when it is called
#: with no name. Ollama is local and free, so development runs there and
#: watsonx is reached only by naming it.
DEFAULT_PROVIDER = "ollama"
