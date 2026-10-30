"""The speech backend: a header, a narration and a persona in, WAV out.

One class, `WatsonTextToSpeech`, built against IBM's published synthesis API.
It is the only module in `app/` that turns text into audio, and the only one
that may apply the pronunciation table.

**What it is handed, and what it does with it.**

| In | What it is |
| -- | ---------- |
| `header` | the orchestrator's line, from `header` in `app/orchestrator.py` |
| `narration` | `Narrated.text`, the narration with its citation tags stripped |
| `persona_id` | which voice, from `app/personas.py` |
| `situation` | `scored`, `conceded` or `neutral`, from `app/delivery.py` |

| Out | What it is |
| --- | ---------- |
| the return value | the WAV bytes the service sent, unexamined and unmodified |

**The citation tags are refused rather than spoken.** `Narrated.text` is the
stripped text and `Narrated.tagged_text` is the audited one, and the two are
one character apart in a call site. "Open bracket fourteen comma fifteen close
bracket" read aloud over a goal is the kind of thing that ships, so
`speech_text` refuses any text `strip_citations` would change
(`tests/test_tts.py::TestItRefusesTaggedText`).

**Three things decide the request, and none of them is the text.** The voice
comes from the persona, the rate and the pitch come from the delivery row for
that persona and situation, and the situation comes from the moment and the
listener. Nothing here reads the narration to decide how to say it.

**The delivery reaches the request in two different places**, which is not a
choice made here:

  * `rate` and `pitch` are `rate_percentage` and `pitch_percentage`, query
    parameters, because `scripts/tts_probe.py` found `<prosody>` ignored on
    all three of these voices. They are per request, so one narration gets one
    rate and one pitch.
  * the two pauses are `<break>` elements inside the text, so they are per
    sentence, and they go only to a voice whose breaks work, which is the
    Caller's alone.

**Order matters when building the text**, and it is the one subtle thing in
this file. The pronunciation table escapes the text when it marks a word up;
the pauses then go in as markup of their own. Inserting the pauses first and
marking up second would escape the pause elements into `&lt;break ...`, which
the service would read out as text if it read it at all. So pronunciation goes
first, with `as_ssml` set whenever a pause is coming, and the pauses are
joined between the marked-up sentences.

**Credentials are named, never printed.** Building the backend reads
`TTS_API_KEY` and `TTS_URL` through `app/credentials.py`, which loads them
from outside the repo, and raises naming whichever is unset, so a missing
credential fails before a request rather than as a 401 later. `describe`
reports which file was read and the names in it, and no value.

**The service URL is not in the request this module reports.**
`SpeechRequest` carries the path, the query and the body, and the host is
added when the request is sent. That is what lets a recorded request be
committed: `TTS_URL` carries an instance id, so a golden holding the full URL
would be a credential in the repo. The `Authorization` header is redacted the
same way and for the same reason.

Every request goes through an `AudioTransport`, a callable taking a URL, a
body and headers and returning bytes. `post_audio` is the real one, built on
`urllib`. Tests pass a transport that replays a recorded response, so the
suite never opens a socket; `tests/conftest.py` fails the suite if anything
tries.

Standard library only, like the rest of `app/`.
"""

import base64
import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Mapping, Protocol, Sequence

from app.credentials import describe
from app.credentials import load as load_credentials
from app.delivery import Delivery, delivery
from app.grounding import strip_citations
from app.personas import persona
from app.pronunciation import for_speech, spoken_text

#: IBM's synthesis endpoint, and the format asked for. The probe found all
#: three voices answering 24000 Hz, 1 channel, 16 bit for this Accept header.
SYNTHESIZE_PATH = "/v1/synthesize"
WAV_ACCEPT = "audio/wav"

#: The variables this needs. The names come from `.env.example`, which is the
#: template in the repo; the values come from the credentials file outside it.
TTS_ENV_VARS = ("TTS_API_KEY", "TTS_URL")

#: Basic auth with this literal user name is IBM's documented example for this
#: service, and it is one request where an IAM exchange would be two.
BASIC_AUTH_USER = "apikey"

#: What stands in for the bearer token in a request that is being reported,
#: recorded or compared. Nothing is ever recorded with the real one.
REDACTED = "Basic <redacted>"

#: A generous timeout. Synthesis is quick, but a cold voice is not.
DEFAULT_TIMEOUT = 60.0

#: One sentence, the same shape `app/grounding.py` reads them in, so the
#: pauses land where the check's sentences end.
_SENTENCE = re.compile(r"[^.!?\n]+[.!?]*")

#: A pause, as IBM writes it, and the pattern that reads one back off.
BREAK = '<break time="{}ms"/>'
_BREAK_TAG = re.compile(r'\s*<break time="\d+ms"/>')


class TextToSpeechError(RuntimeError):
    """The backend could not be built, or was handed something it must refuse."""


class MissingCredentials(TextToSpeechError):
    """The backend needs credentials that are not set.

    The message names the variables and says which file was looked in, and
    stops there. `CLAUDE.md` forbids putting a credential anywhere it could be
    read, so this reports the symptom and leaves the file to the user.
    """


class CitationTagsInText(TextToSpeechError):
    """The text still carries the citation tags, which are not for speaking.

    `Narrated.text` is the stripped narration and `Narrated.tagged_text` is
    the one kept for the audit trail. Passing the second is a one character
    mistake at a call site and an unmistakable one in the audio, so it is
    refused here rather than read out.
    """


@dataclass(frozen=True)
class SpeechRequest:
    """One synthesis request, with nothing secret in it.

    `path` and `query` are what goes after the host, and the host is added by
    `url_for` when the request is sent. `text` is the body's text field, SSML
    markup and all, and `body` is that encoded.

    `headers` carries `REDACTED` in place of the bearer token. The real header
    is built in `send` and exists for the length of one call. That is what
    makes this shape safe to print, to record and to commit: `TTS_URL` carries
    an instance id and the key is a key.
    """

    path: str
    query: str
    text: str
    headers: Mapping[str, str] = field(default_factory=dict)

    @property
    def body(self) -> bytes:
        return json.dumps({"text": self.text}).encode("utf-8")

    @property
    def billable_characters(self) -> int:
        """The submitted length of the text, which is the conservative count.

        IBM does not publish whether SSML markup is billable, so this counts
        it. `spoken_characters` is the floor.
        """
        return len(self.text)

    def as_recorded(self) -> dict:
        """The request as a golden fixture holds it."""
        return {
            "path": self.path,
            "query": self.query,
            "text": self.text,
            "headers": dict(self.headers),
        }


class AudioTransport(Protocol):
    """Sends one POST and returns the response body as bytes."""

    def __call__(
        self, url: str, body: bytes, headers: Mapping[str, str]
    ) -> bytes:
        ...


def post_audio(
    url: str,
    body: bytes,
    headers: Mapping[str, str],
    timeout: float = DEFAULT_TIMEOUT,
) -> bytes:
    """POST `body` to `url` and return the response body.

    The only function in this module that opens a connection. It returns bytes
    rather than parsed JSON, which is the one way this transport differs from
    the narration one: the response is audio.
    """
    request = urllib.request.Request(
        url, data=body, headers=dict(headers), method="POST"
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def sentences(text: str) -> tuple[str, ...]:
    """`text` split into sentences, each keeping its own punctuation."""
    return tuple(
        found.strip() for found in _SENTENCE.findall(text) if found.strip()
    )


def with_pauses(text: str, row: Delivery) -> str:
    """`text` as marked-up sentences joined by this row's pauses.

    The longer pause goes before the last sentence, because the narration ends
    on the goal and nothing follows it: `docs/VOICE.md` is where that is
    settled. Every other gap gets the sentence pause.

    Pronunciation is applied per sentence and before the pauses go in, with
    `as_ssml` set, so that the escaping happens once and the pause elements
    are not themselves escaped.
    """
    parts = sentences(text)
    if len(parts) < 2:
        return for_speech(text, as_ssml=True)

    spoken = [for_speech(part, as_ssml=True) for part in parts]
    out = [spoken[0]]
    for index, part in enumerate(spoken[1:], start=1):
        last = index == len(spoken) - 1
        pause = row.goal_break if last else row.sentence_break
        # A row may set the sentence pause and not the goal one, and then the
        # goal still gets a pause. The other way round it does not: an
        # ordinary gap does not inherit the long pause meant for the goal.
        if pause is None and last:
            pause = row.sentence_break
        if pause is not None:
            out.append(BREAK.format(pause))
        out.append(part)
    return " ".join(out)


def speech_text(
    header: str, narration: str, persona_id: str, situation: str
) -> str:
    """The text that goes in the request body, markup and all.

    The header and the narration, in that order and separated by a space: the
    header is the line spoken to the fan and the narration is what follows it.
    Then the pronunciation table, and then the pauses if this persona's voice
    honours them.

    Raises `CitationTagsInText` if either part still carries its tags.
    """
    for name, part in (("header", header), ("narration", narration)):
        if strip_citations(part) != part:
            raise CitationTagsInText(
                "the {} still carries its citation tags, which are for the "
                "audit trail and not for speaking: pass Narrated.text rather "
                "than Narrated.tagged_text".format(name)
            )

    one = persona(persona_id)
    row = delivery(persona_id, situation)
    text = "{} {}".format(header.strip(), narration.strip()).strip()

    pauses_wanted = row.sentence_break is not None or row.goal_break is not None
    if pauses_wanted and one.breaks_work:
        return with_pauses(text, row)
    # A row that wants a pause on a voice that ignores them cannot happen:
    # `validate` in `app/delivery.py` refuses that table at import. This still
    # reads `breaks_work` rather than assuming, because the check belongs
    # where the markup is written.
    return for_speech(text)


class WatsonTextToSpeech:
    """IBM Watson Text to Speech, reached with a persona and a situation.

    Construction reads `TTS_ENV_VARS` through `app/credentials.py` and raises
    `MissingCredentials` naming whichever is unset, so a missing credential
    fails before any request is sent.

    `speak` is one request and returns the bytes the service sent, unexamined.
    This module does not parse the audio: `scripts/tts_probe.py` is what reads
    a WAV header, and a backend that inspected its own output would be
    deciding whether the service had done its job.
    """

    name = "watson_tts"

    def __init__(
        self,
        env: Mapping[str, str] | None = None,
        transport: AudioTransport = post_audio,
        accept: str = WAV_ACCEPT,
    ) -> None:
        env = load_credentials() if env is None else env
        missing = [name for name in TTS_ENV_VARS if not env.get(name)]
        if missing:
            # describe() reports variable names and no values, so this is safe
            # to print. It says which file was read, which is the question a
            # missing credential actually raises.
            raise MissingCredentials(
                "Text to Speech needs " + ", ".join(missing) + ", which is "
                "not set. " + describe().summary + ". .env.example lists the "
                "variable names."
            )
        self.host = env["TTS_URL"].rstrip("/")
        self.accept = accept
        self._api_key = env["TTS_API_KEY"]
        self._transport = transport

    def request_for(
        self, header: str, narration: str, persona_id: str, situation: str
    ) -> SpeechRequest:
        """The request this would send, with the token and the host left out.

        Public because the golden recorder and the replaying test both need
        the exact request, and a recording is worth nothing if the replay
        sends something else.
        """
        one = persona(persona_id)
        row = delivery(persona_id, situation)
        if not one.voice:
            raise TextToSpeechError(
                "{} has no voice, so there is nothing to speak it".format(
                    persona_id
                )
            )

        params = {"voice": one.voice}
        # Only a parameter that was decided is sent. Sending rate_percentage=0
        # would be a decision to use the voice's own rate, which is a
        # different statement from not having decided yet.
        if row.rate is not None:
            params["rate_percentage"] = str(row.rate)
        if row.pitch is not None:
            params["pitch_percentage"] = str(row.pitch)

        return SpeechRequest(
            path=SYNTHESIZE_PATH,
            query=urllib.parse.urlencode(params),
            text=speech_text(header, narration, persona_id, situation),
            headers={
                "Content-Type": "application/json",
                "Accept": self.accept,
                "Authorization": REDACTED,
            },
        )

    def url_for(self, request: SpeechRequest) -> str:
        return "{}{}?{}".format(self.host, request.path, request.query)

    def send(self, request: SpeechRequest) -> bytes:
        """Send one prepared request and return the audio.

        The real `Authorization` header is built here and nowhere else, so it
        exists for the length of this call and never reaches a dataclass, a
        log or a fixture.
        """
        token = base64.b64encode(
            "{}:{}".format(BASIC_AUTH_USER, self._api_key).encode("utf-8")
        ).decode("ascii")
        headers = dict(request.headers)
        headers["Authorization"] = "Basic {}".format(token)
        return self._transport(self.url_for(request), request.body, headers)

    def speak(
        self, header: str, narration: str, persona_id: str, situation: str
    ) -> bytes:
        """The WAV for this narration, in this persona, in this situation."""
        return self.send(
            self.request_for(header, narration, persona_id, situation)
        )


def provider(
    env: Mapping[str, str] | None = None,
    transport: AudioTransport = post_audio,
) -> WatsonTextToSpeech:
    """The speech backend.

    There is one, so this takes no name. It exists so that a caller reaches
    the backend the same way it reaches a narration provider, and so that a
    second one later is a change here rather than at every call site.
    """
    return WatsonTextToSpeech(env=env, transport=transport)


def without_markup(text: str) -> str:
    """`text` with every element this module can add taken back off.

    The pronunciation elements and the pauses, so what is left is the words.
    It is the floor of what a request can be billed for, and it is also how a
    test asserts that all this markup changed how a narration is said and not
    what it says.
    """
    return spoken_text(_BREAK_TAG.sub("", text))


def spoken_characters(requests: Sequence[SpeechRequest]) -> int:
    """The billable floor for a run: the text with its markup taken off.

    Paired with `billable_characters` on each request, which counts the markup
    too. Both are printed before a paid run, because IBM does not publish
    which of the two it charges for.
    """
    return sum(len(without_markup(request.text)) for request in requests)
