"""Write app/web/segment_timings.json: when each play segment is spoken in its recording.

Offline. Never run by CI, a test or the app: it needs `faster-whisper`, which
is in the dev dependency group only, and a speech model it downloads on first
use. What CI holds instead is the file it writes, through
`tests/test_segment_timings.py`.

For each of the six recordings under `app/web/assets/audio/`:

1. Transcribe it with word timestamps.
2. Align the recognised words to the slot's text word by word with
   `difflib.SequenceMatcher`, after folding both sides to lower case without
   accents or punctuation. Only words inside a matching block are matched.
   Each recognised token is one word. The one exception is `SPLITTABLE`: a
   recognised "onto" standing where the text says "on to" is read as the two
   words, both at the token's start, and every such split is printed. Any
   other merged or split word fails to match.
3. Take each segment's `start_ms` from the recognised word matched to the
   text word that starts at the segment's `start_char`.

**A time is a position in the file**, so it includes the half second of
silence `scripts/pad_hero_audio.py` put in front of every recording. The
transcription runs with no voice activity filter, so nothing is cut out of the
timeline before the words are timed.

**A segment whose first word was not matched gets no time.** The script
reports every such segment and exits 1 without writing. It never interpolates
between two words it did match: a guessed time would put a highlight on words
the voice is not saying.

The file holds, per match and slot, the recording's sha256, its duration in
ms, and per segment `{said, start_ms}` in `app/web/play_segments.json` order.
A cue sheet per slot is printed: each segment's words and its start as
m:ss.mmm.

Usage:
    .\\.venv-prelude\\Scripts\\python.exe scripts/align_segments.py
    .\\.venv-prelude\\Scripts\\python.exe scripts/align_segments.py --model small.en

Reaches huggingface.co once, to download the speech model, unless it is
already cached.
"""

import argparse
import difflib
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "app" / "web"
SEGMENTS = WEB / "play_segments.json"
NARRATIONS = WEB / "narrations.json"
MATCHES = WEB / "matches.json"
OUT = WEB / "segment_timings.json"

#: The default speech model. English only, and the size that still runs on a
#: laptop CPU in well under a minute for all six recordings.
DEFAULT_MODEL = "small.en"

_WORD = re.compile(r"[^\W_]+(?:['’][^\W_]+)*")

_NOTE = (
    "Written by scripts/align_segments.py, offline. For each recording, when "
    "each play segment starts, as a position in the file including the "
    "lead-in. A segment is timed only by a recognised word matched to its "
    "first word; nothing is interpolated."
)


def fold(word: str) -> str:
    """Lower case, no accents, no apostrophes: what the two sides share."""
    decomposed = unicodedata.normalize("NFKD", word)
    bare = "".join(c for c in decomposed if not unicodedata.combining(c))
    return re.sub(r"['’]", "", bare).lower()


def text_words(text: str) -> list[tuple[int, str]]:
    """Every word of the slot text, as (start_char, folded word)."""
    return [(m.start(), fold(m.group(0))) for m in _WORD.finditer(text)]


def heard_words(segments) -> list[tuple[int, str]]:
    """Every recognised word, as (start_ms, folded word): one per token.

    A token is folded the way the text is and never split, so a token that
    ran two words together stays one word and fails to match them. The one
    exception is made in `align`, not here.
    """
    out: list[tuple[int, str]] = []
    for segment in segments:
        for word in segment.words or ():
            folded = "".join(fold(piece) for piece in _WORD.findall(word.word))
            if folded:
                out.append((int(round(word.start * 1000)), folded))
    return out


#: The one merged word that may be split: a recognised "onto" standing where
#: the text says "on to". The two pieces both take the token's start, because
#: "on" is the start of the token that says it. Any other merged or split word
#: is left as it is and fails to match.
SPLITTABLE = {"onto": ("on", "to")}


def _match(
    text: list[tuple[int, str]], heard: list[tuple[int, str, int | None]]
) -> dict[int, tuple[int, int]]:
    """Text word index to (heard index, start_ms), for words in a block."""
    matcher = difflib.SequenceMatcher(
        None,
        [word for _at, word in text],
        [word for _ms, word, _split in heard],
        autojunk=False,
    )
    matched: dict[int, tuple[int, int]] = {}
    for block in matcher.get_matching_blocks():
        for k in range(block.size):
            matched[block.a + k] = (block.b + k, heard[block.b + k][0])
    return matched


def align(
    text: list[tuple[int, str]], heard: list[tuple[int, str]]
) -> tuple[dict[int, int], list[tuple[int, int]]]:
    """start_char of a text word to the start_ms of the word heard for it,
    and the splits that were kept, as (start_ms, start_char of "on").

    Every recognised "onto" is first split into "on" and "to". A split is
    kept only where both pieces matched, side by side, the text's own "on"
    and "to"; every other split is put back as "onto" and the words aligned
    again, until every split left stands where the text says "on to".
    """
    allowed = {index for index, (_ms, word) in enumerate(heard) if word in SPLITTABLE}
    while True:
        expanded: list[tuple[int, str, int | None]] = []
        for index, (ms, word) in enumerate(heard):
            if index in allowed:
                for piece in SPLITTABLE[word]:
                    expanded.append((ms, piece, index))
            else:
                expanded.append((ms, word, None))
        matched = _match(text, expanded)
        by_heard = {h: t for t, (h, _ms) in matched.items()}
        kept: list[tuple[int, int]] = []
        failed = set()
        for index in allowed:
            pieces = [h for h, item in enumerate(expanded) if item[2] == index]
            words = [by_heard.get(h) for h in pieces]
            whole = SPLITTABLE[heard[index][1]]
            if (
                None not in words
                and words == list(range(words[0], words[0] + len(whole)))
                and [text[t][1] for t in words] == list(whole)
            ):
                kept.append((heard[index][0], text[words[0]][0]))
            else:
                failed.add(index)
        if not failed:
            times = {text[t][0]: ms for t, (_h, ms) in matched.items()}
            return times, sorted(kept)
        allowed -= failed


def decode(path: Path):
    """The recording as 16 kHz mono float samples, from the start of the file.

    `faster_whisper.audio.decode_audio` does this, but passes
    `metadata_errors` to `av.open`, which PyAV 19 no longer accepts. This is
    the same decode without that one argument: every frame resampled to
    16 kHz mono signed 16-bit, then scaled to float. Nothing is trimmed, so
    sample 0 is the first sample of the file and a word's time is its
    position in the file.
    """
    import av
    import numpy as np

    resampler = av.audio.resampler.AudioResampler(
        format="s16", layout="mono", rate=16000
    )
    chunks = []
    with av.open(str(path), mode="r") as container:
        for frame in container.decode(audio=0):
            for out in resampler.resample(frame):
                chunks.append(out.to_ndarray().reshape(-1))
        for out in resampler.resample(None):
            chunks.append(out.to_ndarray().reshape(-1))
    return np.concatenate(chunks).astype(np.float32) / 32768.0


def cue(ms: int) -> str:
    minutes, rest = divmod(ms, 60000)
    seconds, millis = divmod(rest, 1000)
    return f"{minutes}:{seconds:02d}.{millis:03d}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    from faster_whisper import WhisperModel

    model = WhisperModel(args.model, device="cpu", compute_type="int8")
    play = json.loads(SEGMENTS.read_text(encoding="utf-8"))["matches"]
    frozen = json.loads(NARRATIONS.read_text(encoding="utf-8"))["narrations"]
    audio = {
        str(match["match_id"]): match["hero"]["audio"]
        for match in json.loads(MATCHES.read_text(encoding="utf-8"))["matches"]
    }

    document: dict = {"_note": _NOTE, "model": args.model, "matches": {}}
    unmatched: list[str] = []
    for match_id, entry in play.items():
        out_match: dict = {}
        for key, slot in entry["slots"].items():
            relative = audio[match_id][key]
            path = WEB / relative
            text = frozen[match_id]["slots"][key]["text"]
            segments_iter, info = model.transcribe(
                decode(path),
                language="en",
                word_timestamps=True,
                vad_filter=False,
                beam_size=5,
            )
            heard = heard_words(list(segments_iter))
            matched, splits = align(text_words(text), heard)

            timed = []
            print(f"{match_id} {key}  ({relative})")
            for segment in slot["segments"]:
                start_ms = matched.get(segment["start_char"])
                if start_ms is None:
                    unmatched.append(
                        f"{match_id} {key}: {segment['said']!r} at "
                        f"{segment['start_char']}"
                    )
                    print(f"  ??:??.???  {segment['said']}  (NOT MATCHED)")
                    continue
                timed.append({"said": segment["said"], "start_ms": start_ms})
                print(f"  {cue(start_ms)}  {segment['said']}")
            out_match[key] = {
                "audio": relative,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "duration_ms": int(round(info.duration * 1000)),
                "segments": timed,
            }
            for ms, at in splits:
                print(
                    f"  split: heard 'onto' at {cue(ms)} read as 'on' 'to', "
                    f"against the text's 'on to' at {at}"
                )
            if not splits:
                print("  split: none")
            print(f"  heard: {' '.join(word for _ms, word in heard)}")
            print()
        document["matches"][match_id] = out_match

    if unmatched:
        print("segments whose first word was not matched, so not timed:")
        for line in unmatched:
            print(f"  {line}")
        print(f"{OUT.relative_to(ROOT)} was not written")
        return 1

    OUT.write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
