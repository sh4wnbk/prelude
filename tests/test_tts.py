"""Tests for the speech backend: the request it builds and the audio it returns.

No test here reaches the service. The exchange in `tests/golden/`
`tts_synthesize.json` is a real one, recorded by
`scripts/record_tts_golden.py`, and a transport built in the test replays it.
`tests/conftest.py` blocks the network for the whole suite, so a backend that
grew a second request would fail rather than send one.

**A recording is worth nothing if the replay sends something else**, so the
request is rebuilt from `WatsonTextToSpeech.request_for` and compared against
the recorded one, the way `tests/test_narration_provider.py` does for Ollama.

**What the golden holds is the first 128 bytes of the response.** `app/tts.py`
returns the bytes the service sent without examining them, so what a replay
has to assert is that it returns exactly what it was handed; a hundred bytes
do that as well as the ninety thousand the service actually sent, and the
fixture records the full length and SHA-256 of what it did not keep.

The delivery table ships empty, so a request built from it carries no rate,
no pitch and no pauses. The tests that need those monkeypatch the table,
which is also the only way to check the rules that fire on values nobody has
set yet.
"""

import base64
import json
import struct
from pathlib import Path

import pytest

from app.delivery import DELIVERY, Delivery
from app.orchestrator_contract import (
    CALLER,
    CONCEDED,
    MATE,
    NEUTRAL,
    SCORED,
    STORYTELLER,
)
from app.personas import persona
from app.pronunciation import PRONUNCIATIONS
from app.tts import (
    BASIC_AUTH_USER,
    REDACTED,
    MP3_ACCEPT,
    SYNTHESIZE_PATH,
    WAV_ACCEPT,
    CitationTagsInText,
    MissingCredentials,
    SpeechRequest,
    TextToSpeechError,
    WatsonTextToSpeech,
    billed_characters,
    post_audio,
    provider,
    sentences,
    speech_text,
    without_markup,
)

GOLDEN = Path(__file__).resolve().parent / "golden" / "tts_synthesize.json"

#: Credentials that are not credentials. Every test that builds a backend
#: passes these, so none of them reads a file: `tests/conftest.py` already
#: points the loader at an absent path, and this makes the values explicit at
#: the call site too.
FAKE_ENV = {
    "TTS_API_KEY": "not-a-key",
    "TTS_URL": "https://example.invalid/instances/not-an-instance",
}

HEADER = "Argentina take the lead. Argentina 2, England 0. Here's how it happened."
NARRATION = "Maradona dribbled past Terry Butcher. Maradona shot."


@pytest.fixture(scope="module")
def golden():
    return json.loads(GOLDEN.read_text(encoding="utf-8"))


@pytest.fixture
def recorded_audio(golden):
    return base64.b64decode(golden["response"]["head_base64"])


def backend(transport=None, env=None):
    return WatsonTextToSpeech(
        env=FAKE_ENV if env is None else env,
        transport=transport if transport is not None else (
            lambda url, body, headers: b""
        ),
    )


class Recorder:
    """A transport that keeps what it was sent and returns fixed audio."""

    def __init__(self, audio=b""):
        self.audio = audio
        self.calls = []

    def __call__(self, url, body, headers):
        self.calls.append((url, body, dict(headers)))
        return self.audio


class TestTheGoldenIsARecording:
    """It says what it is, and what it is not, in its own provenance block."""

    def test_it_says_it_is_a_recording(self, golden):
        assert golden["provenance"]["is_a_recording"] is True

    def test_it_says_the_body_is_only_the_head_of_the_response(self, golden):
        assert "first 128 bytes" in golden["provenance"]["response_body_is"]
        assert golden["response"]["head_bytes"] == 128

    def test_it_records_the_length_it_did_not_keep(self, golden):
        """The whole response is identified without being stored."""
        assert golden["response"]["bytes"] > golden["response"]["head_bytes"]
        assert len(golden["response"]["sha256"]) == 64

    def test_it_holds_no_credential(self, golden):
        """The host is a credential and so is the token, so neither is here."""
        assert golden["request"]["headers"]["Authorization"] == REDACTED
        text = json.dumps(golden)
        assert "https://" not in text
        assert "apikey:" not in text

    def test_the_recorded_audio_is_a_wav_header_the_service_sent(
        self, recorded_audio
    ):
        """24000 Hz, 1 channel, 16 bit, which is what the probe measured."""
        assert recorded_audio[:4] == b"RIFF"
        assert recorded_audio[8:12] == b"WAVE"
        assert recorded_audio[12:16] == b"fmt "
        channels, frame_rate = struct.unpack("<HI", recorded_audio[22:28])
        bits = struct.unpack("<H", recorded_audio[34:36])[0]
        assert (channels, frame_rate, bits) == (1, 24000, 16)


class TestTheReplaySendsWhatWasRecorded:
    def test_the_request_matches_the_one_that_was_recorded(self, golden):
        """Rebuilt from the backend, compared against the fixture."""
        rebuilt = backend().request_for(
            golden["provenance"]["header"],
            golden["provenance"]["narration"],
            golden["provenance"]["persona"],
            golden["provenance"]["situation"],
        )
        assert rebuilt.as_recorded() == golden["request"]

    def test_it_returns_exactly_the_bytes_the_service_sent(
        self, golden, recorded_audio
    ):
        transport = Recorder(recorded_audio)
        audio = backend(transport).speak(
            golden["provenance"]["header"],
            golden["provenance"]["narration"],
            golden["provenance"]["persona"],
            golden["provenance"]["situation"],
        )
        assert audio == recorded_audio

    def test_it_sends_one_request(self, golden, recorded_audio):
        """One call, unlike the watsonx backend's first narration, which is
        two: this service takes the API key directly, so there is no token to
        exchange first.
        """
        transport = Recorder(recorded_audio)
        backend(transport).speak(
            golden["provenance"]["header"],
            golden["provenance"]["narration"],
            golden["provenance"]["persona"],
            golden["provenance"]["situation"],
        )
        assert len(transport.calls) == 1

    def test_the_recorded_request_carries_the_pronunciation_markup(self, golden):
        """The golden is the shipped path, and the shipped path marks "lead" up."""
        assert "<phoneme" in golden["request"]["text"]
        assert PRONUNCIATIONS["lead"] in golden["request"]["text"]


class TestTheRequestShape:
    def test_it_posts_to_the_documented_path(self):
        assert backend().request_for(
            HEADER, NARRATION, STORYTELLER, NEUTRAL
        ).path == SYNTHESIZE_PATH

    def test_it_asks_for_wav(self):
        request = backend().request_for(HEADER, NARRATION, STORYTELLER, NEUTRAL)
        assert request.headers["Accept"] == WAV_ACCEPT

    def test_the_format_is_the_callers_to_pick(self):
        """`scripts/tts_hero.py` asks for MP3, because the files are committed."""
        backend_mp3 = WatsonTextToSpeech(
            env=FAKE_ENV,
            transport=lambda url, body, headers: b"",
            accept=MP3_ACCEPT,
        )
        request = backend_mp3.request_for(
            HEADER, NARRATION, STORYTELLER, NEUTRAL
        )
        assert request.headers["Accept"] == MP3_ACCEPT

    def test_the_format_changes_nothing_else_in_the_request(self):
        """Only the Accept header moves, so an MP3 run is the same text."""
        wav = backend().request_for(HEADER, NARRATION, STORYTELLER, NEUTRAL)
        mp3 = WatsonTextToSpeech(
            env=FAKE_ENV,
            transport=lambda url, body, headers: b"",
            accept=MP3_ACCEPT,
        ).request_for(HEADER, NARRATION, STORYTELLER, NEUTRAL)
        assert (mp3.path, mp3.query, mp3.text) == (wav.path, wav.query, wav.text)

    def test_the_voice_is_the_personas(self):
        for persona_id in (CALLER, STORYTELLER):
            request = backend().request_for(
                HEADER, NARRATION, persona_id, NEUTRAL
            )
            assert "voice=" + persona(persona_id).voice in request.query

    def test_an_unset_parameter_is_not_sent_and_a_zero_one_is(self):
        """`None` is the parameter not being sent; zero is sending it at the
        voice's own value. They are different requests, and the Storyteller's
        shipped row is one of each: rate 0, pitch unset.
        """
        request = backend().request_for(HEADER, NARRATION, STORYTELLER, NEUTRAL)
        assert "rate_percentage=0" in request.query
        assert "pitch_percentage" not in request.query

    def test_a_row_with_nothing_set_sends_neither(self, monkeypatch):
        monkeypatch.setitem(DELIVERY, (STORYTELLER, NEUTRAL), Delivery())
        request = backend().request_for(HEADER, NARRATION, STORYTELLER, NEUTRAL)
        assert "rate_percentage" not in request.query
        assert "pitch_percentage" not in request.query

    def test_the_callers_pauses_reach_the_shipped_request(self):
        """The shipped table gives the Caller pauses, so the shipped request
        carries them: this is the one persona whose voice honours `<break>`.
        """
        request = backend().request_for(HEADER, NARRATION, CALLER, NEUTRAL)
        assert '<break time="200ms"/>' in request.text
        assert '<break time="400ms"/>' in request.text

    def test_the_mate_sends_a_different_request_for_each_side(self):
        """Now that the table is filled in, the two sides really do differ."""
        built = backend()
        assert built.request_for(
            HEADER, NARRATION, MATE, SCORED
        ).query != built.request_for(HEADER, NARRATION, MATE, CONCEDED).query

    def test_a_set_rate_and_pitch_are_sent(self, monkeypatch):
        monkeypatch.setitem(
            DELIVERY, (STORYTELLER, NEUTRAL), Delivery(rate=-10, pitch=15)
        )
        request = backend().request_for(HEADER, NARRATION, STORYTELLER, NEUTRAL)
        assert "rate_percentage=-10" in request.query
        assert "pitch_percentage=15" in request.query

    def test_the_two_situations_can_differ(self, monkeypatch):
        """One voice, two deliveries, which is what the table is keyed for."""
        monkeypatch.setitem(DELIVERY, (MATE, SCORED), Delivery(rate=10))
        monkeypatch.setitem(DELIVERY, (MATE, CONCEDED), Delivery(rate=-10))
        built = backend()
        assert built.request_for(
            HEADER, NARRATION, MATE, SCORED
        ).query != built.request_for(HEADER, NARRATION, MATE, CONCEDED).query

    def test_the_body_is_the_documented_json(self):
        request = backend().request_for(HEADER, NARRATION, STORYTELLER, NEUTRAL)
        assert json.loads(request.body.decode("utf-8")) == {
            "text": request.text
        }

    def test_the_mates_neutral_row_cannot_be_asked_for(self):
        with pytest.raises(KeyError):
            backend().request_for(HEADER, NARRATION, MATE, NEUTRAL)

    def test_an_unknown_persona_is_refused(self):
        with pytest.raises(KeyError):
            backend().request_for(HEADER, NARRATION, "commentator", NEUTRAL)


class TestNothingSecretIsInTheRequest:
    """`SpeechRequest` is safe to print, to record and to commit."""

    def test_the_host_is_not_in_it(self):
        request = backend().request_for(HEADER, NARRATION, STORYTELLER, NEUTRAL)
        assert FAKE_ENV["TTS_URL"] not in json.dumps(request.as_recorded())

    def test_the_token_is_not_in_it(self):
        request = backend().request_for(HEADER, NARRATION, STORYTELLER, NEUTRAL)
        assert request.headers["Authorization"] == REDACTED
        assert FAKE_ENV["TTS_API_KEY"] not in json.dumps(request.as_recorded())

    def test_the_host_and_token_reach_the_transport(self):
        """They have to arrive somewhere, and that somewhere is one call."""
        transport = Recorder()
        built = backend(transport)
        built.speak(HEADER, NARRATION, STORYTELLER, NEUTRAL)
        url, _, headers = transport.calls[0]
        assert url.startswith(FAKE_ENV["TTS_URL"])
        token = base64.b64encode(
            "{}:{}".format(
                BASIC_AUTH_USER, FAKE_ENV["TTS_API_KEY"]
            ).encode("utf-8")
        ).decode("ascii")
        assert headers["Authorization"] == "Basic " + token


class TestItRefusesTaggedText:
    """`Narrated.text` is for speaking and `Narrated.tagged_text` is not."""

    def test_a_tagged_narration_is_refused(self):
        with pytest.raises(CitationTagsInText) as failure:
            speech_text(HEADER, "[14, 15] Maradona shot.", STORYTELLER, NEUTRAL)
        assert "narration" in str(failure.value)

    def test_a_tagged_header_is_refused(self):
        with pytest.raises(CitationTagsInText) as failure:
            speech_text("[1] Argentina take the lead.", NARRATION,
                        STORYTELLER, NEUTRAL)
        assert "header" in str(failure.value)

    def test_the_stripped_narration_is_accepted(self):
        assert speech_text(HEADER, NARRATION, STORYTELLER, NEUTRAL)


class TestTheTextItBuilds:
    def test_the_header_comes_first(self):
        text = speech_text(HEADER, NARRATION, STORYTELLER, NEUTRAL)
        assert without_markup(text).startswith("Argentina take the lead.")

    def test_it_says_the_header_and_the_narration_and_nothing_else(self):
        """Every bit of markup changes how it is said, never what it says."""
        text = speech_text(HEADER, NARRATION, STORYTELLER, NEUTRAL)
        assert without_markup(text) == HEADER + " " + NARRATION

    def test_the_pronunciation_markup_is_in_it(self):
        text = speech_text(HEADER, NARRATION, STORYTELLER, NEUTRAL)
        assert "<phoneme" in text

    def test_sentences_keep_their_punctuation(self):
        assert sentences("One. Two! Three?") == ("One.", "Two!", "Three?")


class TestOnlyTheCallerGetsPauses:
    """`<break>` moves the Caller's voice and neither of the other two."""

    def test_the_caller_gets_them(self, monkeypatch):
        monkeypatch.setitem(
            DELIVERY,
            (CALLER, NEUTRAL),
            Delivery(sentence_break=300, goal_break=600),
        )
        text = speech_text(HEADER, NARRATION, CALLER, NEUTRAL)
        assert '<break time="300ms"/>' in text
        assert '<break time="600ms"/>' in text

    def test_the_longer_pause_goes_before_the_last_sentence(self, monkeypatch):
        """The narration ends on the goal and nothing follows it."""
        monkeypatch.setitem(
            DELIVERY,
            (CALLER, NEUTRAL),
            Delivery(sentence_break=300, goal_break=600),
        )
        text = speech_text(HEADER, NARRATION, CALLER, NEUTRAL)
        assert text.rindex('<break time="600ms"/>') > text.rindex(
            '<break time="300ms"/>'
        )
        assert text.endswith("Maradona shot.")

    def test_a_voice_that_ignores_breaks_gets_none(self, monkeypatch):
        """The table refuses this at import, so this is the second layer: the
        check sits where the markup is written, not only where it is stored.
        """
        monkeypatch.setitem(
            DELIVERY, (STORYTELLER, NEUTRAL), Delivery(sentence_break=300)
        )
        assert "<break" not in speech_text(
            HEADER, NARRATION, STORYTELLER, NEUTRAL
        )

    def test_the_pauses_say_nothing(self, monkeypatch):
        monkeypatch.setitem(
            DELIVERY,
            (CALLER, NEUTRAL),
            Delivery(sentence_break=300, goal_break=600),
        )
        text = speech_text(HEADER, NARRATION, CALLER, NEUTRAL)
        assert without_markup(text) == HEADER + " " + NARRATION

    def test_the_pause_markup_is_not_escaped(self, monkeypatch):
        """The order of the two markups is the one subtle thing in `app/tts.py`.

        Pronunciation escapes the text it marks up. Inserting the pauses first
        and marking up second would turn them into `&lt;break ...`, which the
        service would read out rather than honour.
        """
        monkeypatch.setitem(
            DELIVERY, (CALLER, NEUTRAL), Delivery(sentence_break=300)
        )
        text = speech_text(HEADER, NARRATION, CALLER, NEUTRAL)
        assert "&lt;break" not in text

    def test_an_ampersand_is_escaped_once_there_are_pauses(self, monkeypatch):
        monkeypatch.setitem(
            DELIVERY, (CALLER, NEUTRAL), Delivery(sentence_break=300)
        )
        text = speech_text("Hearts & Hibs drew.", "Nobody shot.", CALLER,
                           NEUTRAL)
        assert "&amp;" in text
        assert "<break" in text

    def test_an_ordinary_gap_does_not_inherit_the_goal_pause(self, monkeypatch):
        monkeypatch.setitem(
            DELIVERY, (CALLER, NEUTRAL), Delivery(goal_break=600)
        )
        text = speech_text(HEADER, NARRATION, CALLER, NEUTRAL)
        assert text.count('<break time="600ms"/>') == 1

    def test_the_goal_falls_back_to_the_sentence_pause(self, monkeypatch):
        """A row may set one and not the other, and the goal still pauses."""
        monkeypatch.setitem(
            DELIVERY, (CALLER, NEUTRAL), Delivery(sentence_break=300)
        )
        text = speech_text(HEADER, NARRATION, CALLER, NEUTRAL)
        assert text.count('<break time="300ms"/>') == 4


class TestTheCharacterCount:
    """Counted three ways, and IBM charges for one of them."""

    def test_the_submitted_count_includes_the_markup(self):
        request = backend().request_for(HEADER, NARRATION, STORYTELLER, NEUTRAL)
        assert request.billable_characters == len(request.text)

    def test_the_spoken_count_is_the_words_alone(self):
        request = backend().request_for(HEADER, NARRATION, STORYTELLER, NEUTRAL)
        assert len(without_markup(request.text)) == len(
            HEADER + " " + NARRATION
        )

    def test_the_markup_costs_something(self):
        request = backend().request_for(HEADER, NARRATION, STORYTELLER, NEUTRAL)
        assert request.billable_characters > len(
            without_markup(request.text)
        )

    def test_the_billed_count_pays_for_the_markup_and_not_the_spaces(self):
        """IBM counts SSML toward the character count and not whitespace."""
        request = backend().request_for(HEADER, NARRATION, STORYTELLER, NEUTRAL)
        assert request.billed_characters == len(request.text) - sum(
            character.isspace() for character in request.text
        )
        assert "<phoneme" in request.text

    def test_the_billed_count_sits_between_the_other_two(self):
        request = backend().request_for(HEADER, NARRATION, STORYTELLER, NEUTRAL)
        assert (
            len(without_markup(request.text))
            < request.billed_characters
            < request.billable_characters
        )

    def test_a_run_is_billed_request_by_request(self):
        requests = [
            backend().request_for(HEADER, NARRATION, persona_id, NEUTRAL)
            for persona_id in (CALLER, STORYTELLER)
        ]
        assert billed_characters(requests) == sum(
            request.billed_characters for request in requests
        )


class TestCredentials:
    def test_a_missing_credential_is_named_and_nothing_is_sent(self):
        transport = Recorder()
        with pytest.raises(MissingCredentials) as failure:
            WatsonTextToSpeech(env={}, transport=transport)
        message = str(failure.value)
        for name in ("TTS_API_KEY", "TTS_URL"):
            assert name in message
        assert transport.calls == []

    def test_it_says_which_file_it_looked_in(self):
        with pytest.raises(MissingCredentials) as failure:
            WatsonTextToSpeech(env={})
        assert ".env.example" in str(failure.value)

    def test_one_blank_credential_is_enough_to_refuse(self):
        with pytest.raises(MissingCredentials) as failure:
            WatsonTextToSpeech(env=dict(FAKE_ENV, TTS_API_KEY=""))
        assert "TTS_API_KEY" in str(failure.value)

    def test_no_value_is_in_the_message(self):
        with pytest.raises(MissingCredentials) as failure:
            WatsonTextToSpeech(env={"TTS_URL": FAKE_ENV["TTS_URL"]})
        assert FAKE_ENV["TTS_URL"] not in str(failure.value)

    def test_a_trailing_slash_on_the_url_is_dropped(self):
        built = WatsonTextToSpeech(
            env=dict(FAKE_ENV, TTS_URL=FAKE_ENV["TTS_URL"] + "/"),
            transport=Recorder(),
        )
        assert built.host == FAKE_ENV["TTS_URL"]


class TestNoNetwork:
    def test_the_real_transport_is_blocked_inside_a_test(
        self, network_call_error
    ):
        with pytest.raises(network_call_error):
            post_audio("https://example.invalid/", b"{}", {})

    def test_the_default_backend_would_use_the_real_transport(self):
        """`provider()` returns a backend that reaches the service, so a test
        that forgets its transport fails on the network guard rather than
        passing against a stub.
        """
        built = provider(env=FAKE_ENV)
        assert built._transport is post_audio


class TestVoicelessPersona:
    def test_a_persona_with_no_voice_has_nothing_to_speak_it(self, monkeypatch):
        import app.personas as personas

        voiceless = personas.Persona(
            id=STORYTELLER, name="The Storyteller",
            profile="Calm documentary, unhurried and even.", fans_only=False,
        )
        monkeypatch.setitem(personas.BY_ID, STORYTELLER, voiceless)
        with pytest.raises(TextToSpeechError) as failure:
            backend().request_for(HEADER, NARRATION, STORYTELLER, NEUTRAL)
        assert "no voice" in str(failure.value)


class TestSpeechRequestIsJustData:
    def test_it_can_be_built_and_read_without_a_backend(self):
        request = SpeechRequest(
            path=SYNTHESIZE_PATH, query="voice=x", text="Hello."
        )
        assert request.body == b'{"text": "Hello."}'
        assert request.billable_characters == len("Hello.")
