r"""Probe: which delivery controls actually change the audio, voice by voice.

Phase 5 task 1, step 1. Three IBM Natural voices are the candidates for the
three personas, and the delivery table is about to be written against
whichever controls work. IBM's documentation is the reason this runs before
anything is written down: it says the `<prosody>` element is not supported for
Natural voices, that `<break>` is beta for them with timing that may vary, and
that the service **silently ignores** unsupported SSML. A delivery table built
on a silently ignored element would be a page of numbers that change nothing,
and no test could catch it: the request would be well formed and the response
would be audio.

So this measures the audio instead of reading the spec back.

**Six arms, the same sentence in every one:**

| Arm | What it tests |
| --- | ------------- |
| `plain` | the baseline the other five are measured against |
| `rate_minus_20`, `rate_plus_20` | the `rate_percentage` request parameter |
| `pitch_minus_20`, `pitch_plus_20` | the `pitch_percentage` request parameter |
| `break_600ms` | `<break time="600ms"/>` in the middle of the sentence |

The two parameters go in the address rather than in the text, so they cost no
billable characters; the break is markup and costs what it is long.

**Three measures, because duration alone would lie.** A pitch change leaves
the duration exactly where it was, so a duration reading on its own would
report "no effect" for a pitch control that worked perfectly.

| Measure | What it catches | How |
| ------- | --------------- | --- |
| duration | a rate change, and a break | the data chunk over the frame rate |
| bytes identical to `plain` | a control the service ignored | SHA-256 of the response |
| median f0 | a pitch change | autocorrelation over the voiced frames |

Identical bytes for different input is the strongest evidence there is that
nothing happened: the same voice, asked for something different, returned the
same file. The audio is kept so that Shawn can hear the pitch rather than read
an estimate of it.

**Two things the first run of this probe established, and neither needs
paying for again.** They are recorded here because they are why the arms above
are the arms, and `EXTRA_ARMS` can reproduce the first one.

  * `<prosody rate>` and `<prosody pitch>` return audio **byte for byte
    identical** to the plain request on all three voices, which is IBM's
    documented "silently ignores" in measured form.
  * The WAV header's length field is a streaming placeholder. The service
    writes the header before it knows how long the audio will be, so both the
    RIFF size and the data chunk size arrive as `0xFFFFFFFF` and
    `wave.getnframes()` reports 89478.49 seconds for every file. The duration
    here comes from the bytes that actually arrived, with the format read from
    the `fmt ` chunk.

**It spends money, so it is built to be hard to run by accident**, like
`scripts/narration_compare.py`. `--plan` prints every arm and the character
count and makes no call. Nothing is sent without `--confirm`. `--from-audio`
re-measures what is already on disk and sends nothing, which is what a fix to
a reading uses rather than paying twice for the same audio.

**The cost is counted two ways.** The plan prints the submitted length of
every request, which bounds the price above, and the spoken text alone, which
bounds it below. IBM bills the SSML and not the whitespace, which is
`billed_characters` in `app/tts.py` and sits between the two.

Credentials are read through `app/credentials.py`, which loads them from
outside the repo. Nothing here prints a value, the service URL included: it
carries an instance id.

The audio is written outside the repo, next to where the hero samples go, for
the same reason the credentials are: it is not the repo's to hold.

Run it:

    .\.venv-prelude\Scripts\python.exe -I scripts\tts_probe.py --plan
    .\.venv-prelude\Scripts\python.exe -I scripts\tts_probe.py --confirm
    .\.venv-prelude\Scripts\python.exe -I scripts\tts_probe.py --from-audio

Standard library only.
"""

import argparse
import base64
import hashlib
import json
import math
import statistics
import sys
import urllib.error
import urllib.parse
import urllib.request
import wave
from array import array
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.credentials import describe  # noqa: E402
from app.credentials import load as load_credentials  # noqa: E402

#: The three candidate voices, in the order the personas are listed.
VOICES = (
    "en-AU_HeidiNatural",
    "en-US_EmmaNatural",
    "en-US_EthanNatural",
)

#: One sentence, past tense, no name and no number: the probe is about the
#: delivery, and a name would make it about pronunciation too. The same words
#: in every arm, so a duration is comparable across them.
SENTENCE = "He turned, and the shot went in."

#: The sentence the pronunciation arms speak, and the same with the element
#: around the word. "lead" is the entry in `app/pronunciation.py` and the
#: reason that file exists: the metal is `lɛd` and the thing a team takes
#: is `liːd`.
LEAD_SENTENCE = "Argentina take the lead."
LEAD_PHONEME_SENTENCE = LEAD_SENTENCE.replace(
    "lead", '<phoneme alphabet="ipa" ph="liːd">lead</phoneme>'
)

#: The same sentence asking for the **wrong** pronunciation, the metal.
#:
#: This is the arm that can actually answer the question. Asking for `liːd`
#: proves nothing: if the voice already says it that way, an element
#: requesting what is already happening produces identical audio whether it
#: was honoured or ignored. Asking for `lɛd` is different from whatever the
#: voice does by default, so identical audio can only mean the element was
#: ignored. Nothing ships this; it is a measurement.
LEAD_WRONG_SENTENCE = LEAD_SENTENCE.replace(
    "lead", '<phoneme alphabet="ipa" ph="lɛd">lead</phoneme>'
)

#: How far the two parameters are moved, as a percentage, in both directions.
SHIFT = 20

#: The break the probe asks for, and where it goes. 600 ms is the length the
#: delivery table will be built out of, so it is the length worth measuring
#: rather than a round number chosen to be easy to see.
BREAK_MS = 600
BREAK = '<break time="{}ms"/>'.format(BREAK_MS)
BREAK_SENTENCE = SENTENCE.replace("and the shot", BREAK + " and the shot")

#: The synthesis endpoint and the format asked for, from IBM's published API.
SYNTHESIZE_PATH = "/v1/synthesize"
WAV_ACCEPT = "audio/wav"

#: The variables this needs. The names come from `.env.example`; the values
#: come from the credentials file outside the repo.
TTS_ENV_VARS = ("TTS_API_KEY", "TTS_URL")

#: Where the audio goes: outside the repo, beside the hero samples.
DEFAULT_OUT = Path.home() / "prelude_voice" / "probe"

#: A duration this far from the plain arm's counts as a change. The service is
#: not a metronome and two renderings of one sentence differ by a few
#: milliseconds, so the threshold is well above that and well below the shift
#: the arms ask for.
DURATION_TOLERANCE = 0.05

#: The same, for the median f0, in semitones. A 20 percent pitch shift is over
#: three semitones, and the estimator's own spread on one unchanged voice is
#: well under one.
PITCH_TOLERANCE = 0.5

#: The band the f0 estimator looks in, and how strong the autocorrelation peak
#: has to be before a frame is called voiced.
F0_LOW = 70.0
F0_HIGH = 350.0
VOICED_PEAK = 0.30

#: The estimator works on a decimated signal: 5 kHz is ample for a 350 Hz
#: ceiling and it is what makes a pure Python autocorrelation finish.
F0_TARGET_RATE = 5000

#: The length fields a streamed RIFF file carries instead of a length. The
#: service sends the header before it knows how long the audio will be, so
#: both the RIFF size and the data chunk size come back saturated.
STREAMING_PLACEHOLDER = 0xFFFFFFFF


@dataclass(frozen=True)
class Arm:
    """One request: a body to speak and the query parameters to send with it.

    `text` is what goes in the JSON body, SSML markup and all. `params` are
    the extra query parameters beside `voice`, which is the only way to reach
    `rate_percentage` and `pitch_percentage`.

    `spoken` is the sentence without the markup, so the plan can report the
    billable floor beside the conservative figure.

    `control` names what the arm tests, and `expect` says which measure should
    move if that control works. Together they are what turns a table of
    numbers into a verdict per control.
    """

    name: str
    text: str
    params: Mapping[str, str]
    control: str
    expect: str
    spoken: str = SENTENCE
    #: Which arm this one is read against. Almost every arm is read against
    #: the plain rendering of the same sentence; the pronunciation pair speaks
    #: a different sentence, so it carries its own baseline.
    baseline: str = "plain"


ARMS: tuple[Arm, ...] = (
    Arm("plain", SENTENCE, {}, "none", "baseline"),
    Arm(
        "rate_minus_20",
        SENTENCE,
        {"rate_percentage": "-{}".format(SHIFT)},
        "rate_percentage",
        "longer",
    ),
    Arm(
        "rate_plus_20",
        SENTENCE,
        {"rate_percentage": "{}".format(SHIFT)},
        "rate_percentage",
        "shorter",
    ),
    Arm(
        "pitch_minus_20",
        SENTENCE,
        {"pitch_percentage": "-{}".format(SHIFT)},
        "pitch_percentage",
        "lower f0",
    ),
    Arm(
        "pitch_plus_20",
        SENTENCE,
        {"pitch_percentage": "{}".format(SHIFT)},
        "pitch_percentage",
        "higher f0",
    ),
    Arm("break_600ms", BREAK_SENTENCE, {}, "break", "longer"),
    # `<phoneme>` is the one element `app/pronunciation.py` depends on, and
    # IBM documents it as supported with no voice-type restriction. Documented
    # as supported is what `<prosody>` also was, so it is measured: one
    # sentence holding "lead" plain, and the same sentence with the element
    # around that word. Different bytes mean the element reached the voice.
    Arm("lead_plain", LEAD_SENTENCE, {}, "phoneme", "baseline",
        spoken=LEAD_SENTENCE),
    Arm("lead_phoneme", LEAD_PHONEME_SENTENCE, {}, "phoneme", "different",
        spoken=LEAD_SENTENCE, baseline="lead_plain"),
    Arm("lead_phoneme_wrong", LEAD_WRONG_SENTENCE, {}, "phoneme", "different",
        spoken=LEAD_SENTENCE, baseline="lead_plain"),
)

#: Arms the first run measured and the delivery table will not be built from.
#: They are kept because they are the evidence behind the docstring's claim
#: that `<prosody>` is ignored, and because a reader who doubts it should be
#: able to run it rather than take it on trust. `--arms` is the only way to
#: reach them: they are not sent by default, since the answer is already in.
EXTRA_ARMS: tuple[Arm, ...] = (
    Arm(
        "ssml_rate_slower",
        '<prosody rate="-{}%">{}</prosody>'.format(SHIFT, SENTENCE),
        {},
        "prosody rate",
        "longer",
    ),
    Arm(
        "ssml_rate_faster",
        '<prosody rate="+{}%">{}</prosody>'.format(SHIFT, SENTENCE),
        {},
        "prosody rate",
        "shorter",
    ),
    Arm(
        "ssml_pitch_lower",
        '<prosody pitch="-{}%">{}</prosody>'.format(SHIFT, SENTENCE),
        {},
        "prosody pitch",
        "lower f0",
    ),
    Arm(
        "ssml_pitch_higher",
        '<prosody pitch="+{}%">{}</prosody>'.format(SHIFT, SENTENCE),
        {},
        "prosody pitch",
        "higher f0",
    ),
)

#: By name, which is how `--arms` reaches one.
BY_NAME = {arm.name: arm for arm in ARMS + EXTRA_ARMS}


class ProbeError(RuntimeError):
    """The probe could not run, or the service answered with something odd."""


def credentials() -> tuple[str, str]:
    """`(url, api_key)`, or a failure naming whichever variable is unset.

    Neither value is returned to anywhere that prints. `describe` reports
    which file was read and the names it defines, which is the question a
    missing credential actually raises, and no value reaches a terminal.
    """
    env = load_credentials()
    missing = [name for name in TTS_ENV_VARS if not env.get(name)]
    if missing:
        raise ProbeError(
            "Text to Speech needs " + ", ".join(missing) + ", which is not "
            "set. " + describe().summary + ". .env.example lists the variable "
            "names."
        )
    return env["TTS_URL"].rstrip("/"), env["TTS_API_KEY"]


def query_for(voice: str, arm: Arm) -> str:
    """The query string one arm sends, which holds nothing secret.

    Printed by the plan so that a parameter reported as having no effect can
    be read back as it was actually sent rather than as it was meant.
    """
    return urllib.parse.urlencode(dict({"voice": voice}, **arm.params))


def synthesize(
    url: str, api_key: str, voice: str, arm: Arm, timeout: float = 60.0
) -> bytes:
    """One synthesis, returned as the WAV bytes the service sent.

    Basic auth with the literal user name `apikey` is what IBM's published
    curl example for this service uses, and it is one request rather than the
    two an IAM exchange would be. The header is built here and the key is
    never written anywhere else.
    """
    token = base64.b64encode(
        "apikey:{}".format(api_key).encode("utf-8")
    ).decode("ascii")
    request = urllib.request.Request(
        "{}{}?{}".format(url, SYNTHESIZE_PATH, query_for(voice, arm)),
        data=json.dumps({"text": arm.text}).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": WAV_ACCEPT,
            "Authorization": "Basic {}".format(token),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    except urllib.error.HTTPError as failure:
        # The service reports a rejected element or attribute as a 400 with a
        # JSON body saying which. That body is worth reading; the URL it came
        # from is not worth printing.
        detail = failure.read().decode("utf-8", "replace").strip()
        raise ProbeError(
            "{} {}: HTTP {} {}: {}".format(
                voice, arm.name, failure.code, failure.reason, detail
            )
        ) from None


@dataclass(frozen=True)
class Wav:
    """One WAV file, read the long way round, and why that is necessary.

    **The header's length field cannot be trusted here and `wave` believes
    it.** IBM streams the audio, so it writes the header before it knows how
    much audio there will be, and both the RIFF size and the data chunk size
    arrive as `STREAMING_PLACEHOLDER`. `wave.getnframes()` reports that
    number, which came out of the first run of this probe as 89478.49 seconds
    for every file on every voice: one placeholder, printed six times a voice,
    and every delta exactly zero.

    So the format comes from the `fmt ` chunk, which is correct, and the
    length comes from the bytes that are actually there. `declared_frames` and
    `declared_data_bytes` are kept beside `frames` so a reader can see the
    placeholder for what it is.
    """

    channels: int
    sample_width: int
    frame_rate: int
    declared_frames: int
    declared_data_bytes: int
    frames: int
    data: bytes

    @property
    def duration(self) -> float:
        return self.frames / float(self.frame_rate)

    @property
    def streamed(self) -> bool:
        """Whether the length field is the placeholder rather than a length.

        Read off the data chunk's own size field rather than off
        `declared_frames`, which is that size divided by the block alignment
        and so is one short of the placeholder for 16 bit mono audio.
        """
        return self.declared_data_bytes >= STREAMING_PLACEHOLDER

    def reading(self) -> dict:
        """The header fields, for the report and the JSON."""
        return {
            "channels": self.channels,
            "sample_width": self.sample_width,
            "frame_rate": self.frame_rate,
            "declared_frames": self.declared_frames,
            "declared_data_bytes": self.declared_data_bytes,
            "frames": self.frames,
            "streamed": self.streamed,
        }


def read_wav(path: Path) -> Wav:
    """Parse the chunks by hand, taking the format from the header.

    `wave` is still what reads the format: it knows the `fmt ` chunk and there
    is no reason to re-implement it. What it cannot do is report a length the
    file does not state, so the data chunk is found again here and the bytes
    that arrived are counted.
    """
    with wave.open(str(path), "rb") as audio:
        channels = audio.getnchannels()
        sample_width = audio.getsampwidth()
        frame_rate = audio.getframerate()
        declared_frames = audio.getnframes()

    raw = path.read_bytes()
    if raw[:4] != b"RIFF" or raw[8:12] != b"WAVE":
        raise ProbeError("{} is not a RIFF WAVE file".format(path.name))
    offset = 12
    data = b""
    declared_data_bytes = 0
    while offset + 8 <= len(raw):
        chunk_id = raw[offset : offset + 4]
        size = int.from_bytes(raw[offset + 4 : offset + 8], "little")
        body = offset + 8
        if chunk_id == b"data":
            declared_data_bytes = size
            end = len(raw) if size >= STREAMING_PLACEHOLDER else body + size
            data = raw[body : min(end, len(raw))]
            break
        offset = body + size + (size % 2)
    if not data:
        raise ProbeError("{} holds no data chunk".format(path.name))

    block = channels * sample_width
    return Wav(
        channels=channels,
        sample_width=sample_width,
        frame_rate=frame_rate,
        declared_frames=declared_frames,
        declared_data_bytes=declared_data_bytes,
        frames=len(data) // block,
        data=data[: (len(data) // block) * block],
    )


def _samples(audio: Wav) -> tuple[list[float], int]:
    """The first channel as floats, decimated towards `F0_TARGET_RATE`.

    A box filter the width of the decimation factor runs first, because
    throwing away three samples in four without one would fold everything
    above the new Nyquist back into the band the estimator searches.
    """
    if audio.sample_width != 2:
        raise ProbeError(
            "the audio is {} bit; the estimator reads 16 bit PCM".format(
                audio.sample_width * 8
            )
        )
    raw = array("h")
    raw.frombytes(audio.data)
    channels, rate = audio.channels, audio.frame_rate
    mono = list(raw[::channels]) if channels > 1 else list(raw)

    factor = max(1, rate // F0_TARGET_RATE)
    if factor == 1:
        return [float(v) for v in mono], rate
    smoothed = []
    for start in range(0, len(mono) - factor + 1, factor):
        smoothed.append(sum(mono[start : start + factor]) / factor)
    return smoothed, rate // factor


def median_f0(audio: Wav) -> float | None:
    """The median fundamental frequency over the loud half of the frames.

    Autocorrelation, 40 ms frames at a 20 ms hop, searching the lags that
    `F0_LOW` and `F0_HIGH` bracket. Only the louder half of the frames vote,
    so silence and breath do not, and a frame whose peak is weaker than
    `VOICED_PEAK` is unvoiced and does not vote either.

    `None` when no frame was voiced, which is a measurement that failed rather
    than a pitch of zero.
    """
    signal, rate = _samples(audio)
    frame = int(0.040 * rate)
    hop = int(0.020 * rate)
    if len(signal) < frame:
        return None
    low_lag = max(2, int(rate / F0_HIGH))
    high_lag = min(int(rate / F0_LOW), frame - 1)

    frames = [signal[s : s + frame] for s in range(0, len(signal) - frame, hop)]
    if not frames:
        return None
    energies = [sum(v * v for v in w) for w in frames]
    floor = statistics.median(energies)

    estimates = []
    for window, energy in zip(frames, energies):
        if energy <= 0 or energy < floor:
            continue
        mean = sum(window) / len(window)
        centred = [v - mean for v in window]
        zero = sum(v * v for v in centred)
        if zero <= 0:
            continue
        best_lag, best_score = 0, 0.0
        for lag in range(low_lag, high_lag + 1):
            total = 0.0
            for i in range(len(centred) - lag):
                total += centred[i] * centred[i + lag]
            score = total / zero
            if score > best_score:
                best_score, best_lag = score, lag
        if best_lag and best_score >= VOICED_PEAK:
            estimates.append(rate / best_lag)
    if not estimates:
        return None
    return statistics.median(estimates)


def semitones(f0: float, reference: float) -> float:
    """How far `f0` sits from `reference`, in semitones."""
    return 12.0 * math.log2(f0 / reference)


def measure(path: Path) -> dict:
    """Every reading for one file on disk, and no request.

    Separate from `run` so the measurement can be redone over audio that is
    already paid for. The first run measured the duration out of the header's
    frame count, which is a streaming placeholder, and rerunning the synthesis
    to fix a reading would have been paying twice for the same audio.
    """
    raw = path.read_bytes()
    audio = read_wav(path)
    return {
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "duration": audio.duration,
        "f0": median_f0(audio),
        "header": audio.reading(),
        "path": str(path),
    }


def plan(arms: Sequence[Arm]) -> tuple[int, int, int]:
    """Print every arm and what it will cost, and send nothing.

    Returns `(calls, submitted characters, spoken characters)`. The submitted
    figure bounds the price above: IBM bills the SSML and not the whitespace,
    which `billed_characters` in `app/tts.py` counts.
    """
    submitted = spoken = 0
    print("{} voices x {} arms, the same sentence in each".format(
        len(VOICES), len(arms)
    ))
    print('  sentence: "{}" ({} characters)'.format(SENTENCE, len(SENTENCE)))
    print()
    print("  arm                  submitted  spoken  control          query")
    for arm in arms:
        submitted += len(arm.text) * len(VOICES)
        spoken += len(arm.spoken) * len(VOICES)
        print("  {:<20} {:>9} {:>7}  {:<16} {}".format(
            arm.name, len(arm.text), len(arm.spoken), arm.control,
            query_for(VOICES[0], arm),
        ))
    calls = len(VOICES) * len(arms)
    print()
    print("  {} calls".format(calls))
    print("  {} characters submitted, across all three voices".format(submitted))
    print("  {} characters spoken, markup not counted".format(spoken))
    return calls, submitted, spoken


def run(out: Path, arms: Sequence[Arm]) -> dict[str, dict[str, dict]]:
    """Synthesize every arm on every voice, measure each, return the readings."""
    url, api_key = credentials()
    out.mkdir(parents=True, exist_ok=True)
    readings: dict[str, dict[str, dict]] = {}
    for voice in VOICES:
        readings[voice] = {}
        for arm in arms:
            audio = synthesize(url, api_key, voice, arm)
            path = out / "{}_{}.wav".format(voice, arm.name)
            path.write_bytes(audio)
            readings[voice][arm.name] = measure(path)
            print("  {} {}: {} bytes".format(voice, arm.name, len(audio)),
                  flush=True)
    return readings


def remeasure(out: Path, arms: Sequence[Arm]) -> dict[str, dict[str, dict]]:
    """The readings for the audio already in `out`, sending nothing."""
    readings: dict[str, dict[str, dict]] = {}
    for voice in VOICES:
        readings[voice] = {}
        for arm in arms:
            path = out / "{}_{}.wav".format(voice, arm.name)
            if not path.is_file():
                raise ProbeError("no audio at {}".format(path))
            readings[voice][arm.name] = measure(path)
    return readings


def verdicts(
    voice_readings: Mapping[str, dict], arms: Sequence[Arm]
) -> dict[str, str]:
    """What each control did on one voice: "changes it" or "NO EFFECT".

    A control is read through the measure its arms were built to move, and
    only through that one: a rate arm is judged on duration and a pitch arm on
    f0. Identical bytes to the plain arm are reported beside it, because they
    say more than either measure.
    """
    results: dict[str, str] = {}
    controls = dict.fromkeys(a.control for a in arms if a.control != "none")
    for control in controls:
        notes = []
        moved = 0
        total = 0
        for arm in (a for a in arms if a.control == control):
            if arm.expect == "baseline":
                continue
            base = voice_readings[arm.baseline]
            total += 1
            reading = voice_readings[arm.name]
            if arm.expect == "different":
                moved_here = reading["sha256"] != base["sha256"]
                notes.append("{} {} {}".format(
                    arm.name,
                    "differs from" if moved_here else "is identical to",
                    arm.baseline,
                ))
                moved += 1 if moved_here else 0
                continue
            if arm.expect in ("longer", "shorter"):
                delta = reading["duration"] - base["duration"]
                moved_here = abs(delta) > DURATION_TOLERANCE and (
                    delta > 0 if arm.expect == "longer" else delta < 0
                )
                notes.append("{} {:+.2f}s".format(arm.name, delta))
            elif reading["f0"] is None or base["f0"] is None:
                notes.append("{} f0 unmeasured".format(arm.name))
                continue
            else:
                delta = semitones(reading["f0"], base["f0"])
                moved_here = abs(delta) > PITCH_TOLERANCE and (
                    delta < 0 if arm.expect == "lower f0" else delta > 0
                )
                notes.append("{} {:+.2f} semitones".format(arm.name, delta))
            if reading["sha256"] == base["sha256"]:
                notes[-1] += " (identical bytes)"
            moved += 1 if moved_here else 0
        # Three labels and not two. A parameter that moves the audio one way
        # and is ignored the other way is neither working nor broken, and
        # calling it either would mislead the delivery table: the usable half
        # is usable, and the other half is not there to be set. Which arms
        # moved is in the notes, so `PARTIAL` is never the whole answer.
        results[control] = "{}: {}".format(
            "changes it" if moved == total
            else "NO EFFECT" if moved == 0
            else "PARTIAL, {} of {} arms".format(moved, total),
            ", ".join(notes),
        )
    return results


def report(readings: Mapping[str, dict], arms: Sequence[Arm]) -> None:
    """Print the readings per voice, then the verdict per control."""
    for voice, voice_readings in readings.items():
        base = voice_readings["plain"]
        header = base["header"]
        print()
        print(voice)
        print("  {} Hz, {} channel, {} bit, length field {}".format(
            header["frame_rate"], header["channels"],
            header["sample_width"] * 8,
            "streamed placeholder" if header["streamed"] else "stated",
        ))
        print("  arm                  duration    delta      f0  bytes")
        for arm in arms:
            reading = voice_readings[arm.name]
            f0 = reading["f0"]
            print("  {:<20} {:>7.2f}s {:>+8.2f}s {:>7} {:>6}".format(
                arm.name,
                reading["duration"],
                reading["duration"] - base["duration"],
                "{:.1f}".format(f0) if f0 else "n/a",
                reading["bytes"],
            ))
        print("  verdicts:")
        for control, verdict in verdicts(voice_readings, arms).items():
            print("    {}: {}".format(control, verdict))


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--plan",
        action="store_true",
        help="print the arms and the character count, and make no call",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="send the requests; this is the paid path",
    )
    parser.add_argument(
        "--from-audio",
        action="store_true",
        help="measure the audio already in --out and send nothing",
    )
    parser.add_argument(
        "--arms", help="send only these arms, by name, comma separated"
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--json", type=Path, help="write the readings here")
    args = parser.parse_args(argv)

    selected = ARMS
    if args.arms:
        names = args.arms.split(",")
        unknown = [name for name in names if name not in BY_NAME]
        if unknown:
            print("no such arm: {}; the arms are {}".format(
                ", ".join(unknown), ", ".join(BY_NAME)
            ), file=sys.stderr)
            return 2
        selected = tuple(BY_NAME[name] for name in names)

    try:
        if args.from_audio:
            # Every arm whose audio is on disk for every voice, so a report
            # built this way covers whatever has been paid for so far.
            present = tuple(
                arm for arm in ARMS + EXTRA_ARMS
                if all(
                    (args.out / "{}_{}.wav".format(voice, arm.name)).is_file()
                    for voice in VOICES
                )
            )
            if not present:
                print("no audio in {}".format(args.out), file=sys.stderr)
                return 1
            print("measuring {} arm(s) already in {}, sending nothing".format(
                len(present), args.out
            ))
            readings = remeasure(args.out, present)
            report(readings, present)
            reported = present
        else:
            calls, submitted, _ = plan(selected)
            if args.plan or not args.confirm:
                print()
                print("nothing was sent. --confirm is what sends it.")
                return 0

            print()
            print("sending {} calls, {} characters:".format(calls, submitted))
            readings = run(args.out, selected)
            reported = selected
            # A subset run is still measured against the plain arm, which is
            # the only thing a delta means anything against. If it was not
            # sent this time, the one on disk is read rather than paid for
            # again.
            if BY_NAME["plain"] not in selected:
                for voice in VOICES:
                    baseline = args.out / "{}_plain.wav".format(voice)
                    if not baseline.is_file():
                        raise ProbeError(
                            "a subset run needs the plain arm to compare "
                            "against; there is none at {}".format(baseline)
                        )
                    readings[voice]["plain"] = measure(baseline)
                reported = (BY_NAME["plain"],) + tuple(selected)
            report(readings, reported)
    except ProbeError as failure:
        print("\n{}".format(failure), file=sys.stderr)
        return 1

    if args.json:
        args.json.write_text(
            json.dumps(readings, indent=2) + "\n", encoding="utf-8"
        )
        print("\nreadings written to {}".format(args.json))
    print("\naudio in {}".format(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
