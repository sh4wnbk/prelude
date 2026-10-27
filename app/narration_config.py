"""Which model narrates, and where it runs.

A model id is not a credential. It records which model produced a line of
narration, so it belongs in the repo where a reader can see it rather than in
the credentials file. That file holds the watsonx and TTS credentials, lives
outside the repo (see `app/credentials.py`), and carries no model id; neither
does `.env.example`.

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
    """One watsonx.ai model, and how it has to be asked.

    `model_id` is the id watsonx expects in a request body. `label` is for
    reports and commit messages, not for app output.

    **The request settings travel with the model.** `chat` and
    `reasoning_effort` are not preferences; they are what Task 4b found each
    candidate needs in order to answer at all, and a model id switched
    without them is a model that answers with the tail of its own prompt. So
    they sit on the candidate rather than at a call site, and switching
    `ACTIVE_CANDIDATE` switches them with it.

    `chat` sends `/ml/v1/text/chat` instead of `/ml/v1/text/generation`. Both
    candidates need it: the generation endpoint applies no chat template, and
    on it one candidate prefixed its narration with the end of the prompt and
    the other returned its reasoning as the answer.

    `reasoning_effort` is for a model that thinks before it writes. At its
    default effort `openai/gpt-oss-120b` spent most of its output budget
    reasoning before it wrote anything, about twenty five times what Granite
    spends on a whole narration, and a fan waits through that on every
    attempt and every retry. `docs/narration_eval.md` holds the figures.
    """

    model_id: str
    label: str
    chat: bool = False
    reasoning_effort: str | None = None


GRANITE_4_H_SMALL = Candidate(
    "ibm/granite-4-h-small", "Granite 4 H Small", chat=True
)
GPT_OSS_120B = Candidate(
    "openai/gpt-oss-120b", "GPT OSS 120B", chat=True, reasoning_effort="low"
)

#: The two models the comparison is between, in no significant order.
CANDIDATES: tuple[Candidate, ...] = (GRANITE_4_H_SMALL, GPT_OSS_120B)

#: The candidate a watsonx request uses.
#:
#: **Shawn picked this on the Task 4b results.** Granite was active first
#: because it is the IBM model and this project runs on IBM's stack, and the
#: comparison existed to test that choice rather than assume it. It tested it:
#: `openai/gpt-oss-120b` wrote 33 of 33 narrations that `app/grounding.py`
#: accepted on the first attempt, with no retry and no fallback, against
#: Granite's 16 of 54 with 23 fallbacks. It is also cheaper per narration,
#: because it does not retry. `docs/narration_eval.md` holds the run and
#: `HANDOFF.md` records the decision.
#:
#: Switching candidates is still this one line, and the settings each one
#: needs travel with it on `Candidate`.
ACTIVE_CANDIDATE = GPT_OSS_120B


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

@dataclass(frozen=True)
class Decoding:
    """How a model is asked to sample, pinned so two models are comparable.

    watsonx decodes greedily unless told otherwise, and a greedy model
    returns the same narration three times, which would make three runs one
    run and say nothing about how much a model varies. So the paid comparison
    pins sampling, and pins it identically for both candidates: a difference
    in the results is then a difference between the models rather than
    between their decoding.

    The local runs in `docs/narration_eval.md` sent no decoding options at
    all and so used the Ollama server's own defaults, which this repo does
    not record. These values are not read back from those runs and are not a
    claim about them; they are what this comparison pins.
    """

    temperature: float
    top_p: float
    top_k: int


#: What the paid comparison pins both candidates to.
COMPARISON_DECODING = Decoding(temperature=0.8, top_p=0.9, top_k=40)

#: The backend `app.narration_provider.provider()` returns when it is called
#: with no name. Ollama is local and free, so development runs there and
#: watsonx is reached only by naming it.
DEFAULT_PROVIDER = "ollama"
