"""Tests for the narration config and the two provider backends.

Nothing here calls a model. Each backend is given a transport that replays a
file from `tests/golden/`, and `tests/conftest.py` fails the whole suite if
anything tries to open a connection, so "no network" is enforced rather than
promised.

The two golden files are not the same kind of thing, and the tests treat them
differently on purpose:

  * `ollama_development_model.json` is a **recording**. A real call went to a
    real local server running `granite4:micro` with `num_gpu` 0, and both sides
    of it are in the file. `scripts/record_narration_golden.py` made it and can
    make it again. So the response half is evidence: Ollama really does answer
    in that shape.

  * `watsonx_text_generation.json` is a **schema fixture**, written by hand from
    IBM's published schema. No watsonx call has been made from this repo. Its
    response half is therefore not evidence of what watsonx returns, only of
    what IBM documents it returns, and the file says so in its own provenance
    block. What the tests get out of it is still real: the request half was
    written from the schema by hand, and the code builds its request
    independently, so the two agreeing is a genuine check that the code matches
    the documented API. If IBM's schema is wrong, these tests cannot know it.

Both files are asserted to declare which kind they are, so the distinction
cannot quietly erode.
"""

import json
from pathlib import Path

import pytest

from app import narration_config as config
from app.narration_provider import (
    BACKENDS,
    IAM_GRANT_TYPE,
    IAM_TOKEN_URL,
    MissingCredentials,
    Narration,
    NarrationProvider,
    NarrationProviderError,
    OllamaProvider,
    WatsonxProvider,
    provider,
)

GOLDEN = Path(__file__).resolve().parent / "golden"
OLLAMA_GOLDEN = GOLDEN / "ollama_development_model.json"
WATSONX_GOLDEN = GOLDEN / "watsonx_text_generation.json"


def read_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


class Replay:
    """A transport that answers from a golden file and records what it was sent.

    It refuses a URL the golden does not cover, so a backend that starts
    calling somewhere new fails here rather than reaching for the real
    transport.
    """

    def __init__(self, answers: dict[str, object]):
        self._answers = answers
        self.calls: list[dict] = []

    def __call__(self, url, body, headers):
        self.calls.append({"url": url, "body": body, "headers": dict(headers)})
        if url not in self._answers:
            raise AssertionError(f"no recorded response for {url}")
        return self._answers[url]


class TestConfig:
    """The committed config. Values, not behaviour."""

    def test_the_two_comparison_candidates(self):
        assert [c.model_id for c in config.CANDIDATES] == [
            "ibm/granite-4-h-small",
            "openai/gpt-oss-120b",
        ]

    def test_exactly_one_candidate_is_active(self):
        """Which one is active is a decision, so the test does not pin it.

        Pinning it would mean a one-line comparison switch failed the suite.
        What has to hold is that the active candidate is one of the two.
        """
        assert config.ACTIVE_CANDIDATE in config.CANDIDATES

    def test_the_development_model_runs_on_the_cpu(self):
        """num_gpu 0 is not a tuning choice. This laptop's graphics chip
        produces garbage output, so the option is load-bearing and a test
        stands over it."""
        assert config.DEVELOPMENT_MODEL.model == "granite4:micro"
        assert config.DEVELOPMENT_MODEL.options["num_gpu"] == 0

    def test_the_development_model_options_cannot_be_mutated(self):
        """A shared mapping that a caller could edit would let one run change
        the next one's options."""
        with pytest.raises(TypeError):
            config.DEVELOPMENT_MODEL.options["num_gpu"] = 99

    def test_ollama_is_the_default_backend(self):
        assert config.DEFAULT_PROVIDER == "ollama"
        assert config.DEFAULT_PROVIDER in BACKENDS

    def test_the_config_holds_no_credentials(self):
        """Model ids live in the repo; secrets do not. If a key, a token or a
        project id ever appears here, this file stops being safe to commit."""
        source = (
            Path(config.__file__).read_text(encoding="utf-8").upper()
        )
        for forbidden in ("API_KEY", "APIKEY", "SECRET", "TOKEN", "PROJECT_ID"):
            assert forbidden not in source


class TestSelection:
    """Which backend comes back, and when."""

    def test_the_default_is_ollama(self):
        assert isinstance(provider(), OllamaProvider)

    def test_watsonx_needs_naming(self):
        """The point of the whole selector: a development run cannot reach a
        paid endpoint without someone writing its name."""
        assert provider().name != "watsonx"
        assert provider(None).name != "watsonx"

    def test_watsonx_comes_back_when_named(self):
        golden = read_json(WATSONX_GOLDEN)
        chosen = provider("watsonx", env=golden["env"])
        assert isinstance(chosen, WatsonxProvider)

    def test_an_unknown_name_is_an_error_not_a_default(self):
        """Falling back to the default on a typo would hide the typo."""
        with pytest.raises(NarrationProviderError) as raised:
            provider("granite")
        assert "granite" in str(raised.value)

    def test_both_backends_satisfy_the_interface(self):
        golden = read_json(WATSONX_GOLDEN)
        for built in (
            OllamaProvider(),
            WatsonxProvider(env=golden["env"]),
        ):
            assert isinstance(built, NarrationProvider)


class TestOllamaBackend:
    """Replayed against the recorded call."""

    def test_the_golden_is_a_recording(self):
        provenance = read_json(OLLAMA_GOLDEN)["provenance"]
        assert provenance["kind"] == "recording"
        assert provenance["recorded_by"] == "scripts/record_narration_golden.py"

    def test_the_request_matches_the_one_that_was_recorded(self):
        """The recording is only worth something if the code still sends what
        was sent when it was made."""
        golden = read_json(OLLAMA_GOLDEN)
        feed = OllamaProvider()
        assert feed.url == golden["request"]["url"]
        assert feed.payload(golden["prompt"]) == golden["request"]["payload"]

    def test_the_recorded_request_ran_on_the_cpu(self):
        """What was recorded has to be a call made the way the app makes them,
        so the recording carries the num_gpu option too."""
        payload = read_json(OLLAMA_GOLDEN)["request"]["payload"]
        assert payload["options"]["num_gpu"] == 0
        assert payload["stream"] is False

    def test_it_reads_the_text_out_of_the_recorded_response(self):
        golden = read_json(OLLAMA_GOLDEN)
        replay = Replay({golden["request"]["url"]: golden["response"]})
        feed = OllamaProvider(transport=replay)

        narration = feed.narrate(golden["prompt"])

        assert isinstance(narration, Narration)
        assert narration.text == golden["response"]["response"]
        assert narration.provider == "ollama"
        assert narration.model == golden["response"]["model"] == "granite4:micro"

    def test_it_sends_one_request_to_the_local_server(self):
        golden = read_json(OLLAMA_GOLDEN)
        replay = Replay({golden["request"]["url"]: golden["response"]})

        OllamaProvider(transport=replay).narrate(golden["prompt"])

        assert len(replay.calls) == 1
        assert replay.calls[0]["url"].startswith("http://127.0.0.1:11434")
        assert json.loads(replay.calls[0]["body"].decode("utf-8")) == (
            golden["request"]["payload"]
        )

    def test_a_response_without_the_text_field_is_an_error(self):
        """Ollama answering in some other shape is worth a readable failure,
        not a KeyError from inside the provider."""
        feed = OllamaProvider(
            transport=Replay({OllamaProvider().url: {"done": True}})
        )
        with pytest.raises(NarrationProviderError) as raised:
            feed.narrate("anything")
        assert "response" in str(raised.value)


class TestWatsonxBackend:
    """Replayed against the schema fixture."""

    def test_the_golden_says_it_is_not_a_recording(self):
        """The one assertion that keeps the two files honest about what they
        are. A fixture relabelled as a recording would make this suite look
        like it had proved something about watsonx that it has not."""
        provenance = read_json(WATSONX_GOLDEN)["provenance"]
        assert provenance["kind"] == "schema_fixture"
        assert provenance["is_recording"] is False
        assert provenance["citations"]

    def test_missing_credentials_are_named_and_nothing_is_sent(self):
        """Reported by name, with the file left for the user to open."""
        replay = Replay({})
        with pytest.raises(MissingCredentials) as raised:
            WatsonxProvider(env={}, transport=replay)
        message = str(raised.value)
        for name in ("WATSONX_API_KEY", "WATSONX_PROJECT_ID", "WATSONX_URL"):
            assert name in message
        assert replay.calls == []

    def test_one_blank_credential_is_enough_to_refuse(self):
        golden = read_json(WATSONX_GOLDEN)
        env = dict(golden["env"], WATSONX_API_KEY="")
        with pytest.raises(MissingCredentials) as raised:
            WatsonxProvider(env=env)
        assert "WATSONX_API_KEY" in str(raised.value)
        assert "WATSONX_URL" not in str(raised.value)

    def test_it_requests_the_active_candidate(self):
        golden = read_json(WATSONX_GOLDEN)
        feed = WatsonxProvider(env=golden["env"])
        assert feed.model == config.ACTIVE_CANDIDATE.model_id

    def test_the_request_matches_the_documented_shape(self):
        """The fixture's request half was written from IBM's schema by hand;
        the provider builds its own. The two agreeing is the check."""
        golden = read_json(WATSONX_GOLDEN)
        documented = golden["generation"]["request"]
        feed = WatsonxProvider(
            env=golden["env"], model=documented["payload"]["model_id"]
        )
        assert feed.url == documented["url"]
        assert feed.payload(golden["prompt"]) == documented["payload"]

    def test_the_iam_exchange_uses_the_apikey_grant(self):
        golden = read_json(WATSONX_GOLDEN)
        documented = golden["iam"]["request"]
        replay = Replay({IAM_TOKEN_URL: golden["iam"]["response"]})

        token = WatsonxProvider(env=golden["env"], transport=replay).access_token()

        assert token == golden["iam"]["response"]["access_token"]
        assert replay.calls[0]["url"] == documented["url"] == IAM_TOKEN_URL
        assert replay.calls[0]["headers"] == documented["headers"]
        sent = replay.calls[0]["body"].decode("utf-8")
        assert f"grant_type={IAM_GRANT_TYPE.replace(':', '%3A')}" in sent
        assert "apikey=" in sent

    def test_it_reads_the_text_out_of_the_documented_response(self):
        golden = read_json(WATSONX_GOLDEN)
        documented = golden["generation"]
        replay = Replay(
            {
                IAM_TOKEN_URL: golden["iam"]["response"],
                documented["request"]["url"]: documented["response"],
            }
        )
        feed = WatsonxProvider(
            env=golden["env"],
            transport=replay,
            model=documented["request"]["payload"]["model_id"],
        )

        narration = feed.narrate(golden["prompt"])

        assert narration.text == documented["response"]["results"][0]["generated_text"]
        assert narration.provider == "watsonx"
        assert narration.model == documented["response"]["model_id"]

    def test_it_authorises_the_generation_call_with_the_token_it_fetched(self):
        """Two requests, in order, and the second carries the first's token."""
        golden = read_json(WATSONX_GOLDEN)
        documented = golden["generation"]
        replay = Replay(
            {
                IAM_TOKEN_URL: golden["iam"]["response"],
                documented["request"]["url"]: documented["response"],
            }
        )
        feed = WatsonxProvider(
            env=golden["env"],
            transport=replay,
            model=documented["request"]["payload"]["model_id"],
        )

        feed.narrate(golden["prompt"])

        assert [call["url"] for call in replay.calls] == [
            IAM_TOKEN_URL,
            documented["request"]["url"],
        ]
        assert replay.calls[1]["headers"] == documented["request"]["headers"]

    def test_an_empty_results_array_is_an_error(self):
        golden = read_json(WATSONX_GOLDEN)
        documented = golden["generation"]
        feed = WatsonxProvider(
            env=golden["env"],
            transport=Replay(
                {
                    IAM_TOKEN_URL: golden["iam"]["response"],
                    documented["request"]["url"]: {"results": []},
                }
            ),
            model=documented["request"]["payload"]["model_id"],
        )
        with pytest.raises(NarrationProviderError) as raised:
            feed.narrate(golden["prompt"])
        assert "generated_text" in str(raised.value)


class TestNoNetwork:
    """The guard itself, checked rather than assumed."""

    def test_the_real_transport_is_blocked_inside_a_test(self, network_call_error):
        """If this ever passes a connection through, every other test in the
        suite stops being proof that it made no network call."""
        from app.narration_provider import post

        with pytest.raises(network_call_error):
            post("http://127.0.0.1:11434/api/generate", b"{}", {})

    def test_a_backend_built_with_no_transport_cannot_reach_out(
        self, network_call_error
    ):
        with pytest.raises(network_call_error):
            OllamaProvider().narrate("anything")
