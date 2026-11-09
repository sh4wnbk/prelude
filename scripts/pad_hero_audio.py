r"""A lead-in of silence at the start of each hero recording, and the proof
that nothing else in them moved.

**The first word was lost on an iPhone.** The 2022 Storyteller began at "tina"
rather than at "Argentina". Task 24 fixed the order of the Web Audio resume and
`play()`, which was one cause, and the word was still clipped afterwards: the
audio output itself wakes a moment late, so the opening of the file plays into
hardware that is not ready. A lead-in of silence is what covers that wake, and
it is the fix this script applies.

**Nothing is re-encoded.** An MP3 is a sequence of frames, so a lead-in can be
put in front of the spoken frames rather than mixed into them: this builds half
a second of silence as its own small MP3, then concatenates it with the
original using ffmpeg's concat demuxer and `-c copy`, which copies the
original's frames through untouched. The spoken audio comes out of the decoder
sample for sample identical, and the sample rate, the channel count and the
bitrate are the original's because they are the original's own frames.

A re-encode was measured before this was chosen, and it is why the copy is
worth the trouble. On `3750191_storyteller_neutral.mp3`, libmp3lame at 80 kbps
CBR put the re-encoded speech 20.9 dB below the signal and VBR quality 2 put it
27.7 dB below; the frame copy leaves no difference to measure. The cost of the
copy is that an MP3 frame at 24000 Hz holds 576 samples, which is 24 ms, so
half a second is not a whole number of frames and the lead-in lands near 500 ms
rather than on it. The reported figure is what was measured, and `--check`
holds it to within one frame.

**No TTS call and no network.** `scripts/tts_hero.py` is the paid path that
produced these files; this one reads them off the disk. The file names do not
change, so `hero.audio` in `app/web/matches.json` and every path the player
fetches stay as they are.

**It refuses to pad a file twice.** A second run over a padded file would put a
second half second in front of the first. So each file is probed first and one
that already opens with the lead-in is reported and left alone, which makes a
re-run safe rather than destructive.

**`--check` is the evidence and it can be run again later.** It decodes the
original and the padded file to PCM and reports, per file: where the spoken
audio starts in the padded file, whether every sample from there on matches the
original, and the two decoded durations with the difference between them. The
originals come from git rather than from a copy kept beside the new files:
`--against HEAD` reads the committed version, which is the original until the
padded files are committed, and `--against <commit>~1` reads it after that.

**Durations are decoded, not read off the header.** An MP3's header duration is
an estimate and these files are VBR: `3750191_storyteller_neutral.mp3` reports
22.72 s and decodes to 24.72 s. Every duration here is a sample count divided
by the sample rate.

**Where ffmpeg comes from.** `ffmpeg` and `ffprobe` on `PATH` are used if they
are there. Otherwise set `PRELUDE_FFMPEG` to the directory holding them, or
pass `--ffmpeg`. Nothing is downloaded.

Run it:

    .\.venv-prelude\Scripts\python.exe -I scripts\pad_hero_audio.py --plan
    .\.venv-prelude\Scripts\python.exe -I scripts\pad_hero_audio.py --confirm
    .\.venv-prelude\Scripts\python.exe -I scripts\pad_hero_audio.py --check --against HEAD

Standard library only, and it exits non-zero on any finding.
"""

import argparse
import array
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parent.parent
MATCHES = ROOT / "app" / "web" / "matches.json"
AUDIO_DIR = ROOT / "app" / "web" / "assets" / "audio"
AUDIO_REL = "app/web/assets/audio"

#: The lead-in, in seconds. 500 ms is what Shawn's iPhone needed: the output
#: wakes late and the opening word was landing inside that wake.
LEAD_IN_SECONDS = 0.5

#: Samples in one MPEG-2 Layer III frame, which is the granularity a lead-in
#: can land on. At 24000 Hz it is 24 ms, and it is the tolerance `--check`
#: allows on the lead-in and on the change in duration.
FRAME_SAMPLES = 576

#: The bitrate the half second of silence is encoded at. It is only silence, so
#: the figure barely shows in the file; 80 kbps is the rate the six originals
#: average to, so the lead-in is in the same family as the frames behind it.
SILENCE_BITRATE = "80k"

#: A padded file must open quieter than this, and a file that already does is
#: one this script will not pad again. Decoded MP3 silence is not always
#: numerically zero, so the bar is a level rather than an equality.
SILENCE_DBFS = -60.0

#: How much of the opening has to be that quiet before the file counts as
#: padded. Under the 500 ms asked for, so a lead-in that lands a frame short
#: still reads as a lead-in.
SILENCE_WINDOW_SECONDS = 0.4


def fail(message: str) -> None:
    print("  {}".format(message), file=sys.stderr)


def tool(name: str, override: str | None) -> str:
    """Where `ffmpeg` or `ffprobe` is, or a refusal saying how to say so."""
    candidates = []
    if override:
        given = Path(override)
        candidates.append(given if given.suffix else given / (name + ".exe"))
        candidates.append(given / name)
    from_env = os.environ.get("PRELUDE_FFMPEG")
    if from_env:
        here = Path(from_env)
        candidates.append(here if here.suffix else here / (name + ".exe"))
        candidates.append(here / name)
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    found = shutil.which(name)
    if found:
        return found
    raise SystemExit(
        "{} is not on PATH. Set PRELUDE_FFMPEG to the directory holding "
        "ffmpeg and ffprobe, or pass --ffmpeg. Nothing is downloaded by this "
        "script.".format(name)
    )


def recordings() -> tuple[str, ...]:
    """The six file names, read out of `hero.audio` rather than listed here.

    `scripts/tts_hero.py --map` is what writes that field, from the files that
    are actually on disk, so reading it means this script pads exactly what
    the player fetches.
    """
    doc = json.loads(MATCHES.read_text(encoding="utf-8"))
    names = set()
    for match in doc["matches"]:
        for href in match["hero"]["audio"].values():
            names.add(href.rsplit("/", 1)[-1])
    return tuple(sorted(names))


def probe(ffprobe: str, path: Path) -> dict:
    """The stream's own description of itself: codec, rate, channels, bitrate."""
    out = subprocess.run(
        [ffprobe, "-v", "error", "-select_streams", "a:0",
         "-show_entries", "stream=codec_name,sample_rate,channels,bit_rate",
         "-show_entries", "format=bit_rate,duration",
         "-of", "json", str(path)],
        stdout=subprocess.PIPE, check=True).stdout
    doc = json.loads(out)
    stream = doc["streams"][0]
    return {
        "codec_name": stream["codec_name"],
        "sample_rate": int(stream["sample_rate"]),
        "channels": int(stream["channels"]),
        "bit_rate": int(stream.get("bit_rate") or doc["format"]["bit_rate"]),
        "header_duration": float(doc["format"]["duration"]),
    }


def decode(ffmpeg: str, source, rate: int, channels: int) -> bytes:
    """Signed 16-bit PCM for a file on disk or for bytes in hand.

    Bytes are fed on stdin, which is how an original read out of git is
    decoded without being written anywhere first.
    """
    if isinstance(source, (bytes, bytearray)):
        where, data = "pipe:0", bytes(source)
    else:
        where, data = str(source), None
    done = subprocess.run(
        [ffmpeg, "-hide_banner", "-loglevel", "error", "-i", where,
         "-ar", str(rate), "-ac", str(channels), "-f", "s16le", "-"],
        input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if done.returncode != 0:
        raise SystemExit("ffmpeg could not decode {}: {}".format(
            where, done.stderr.decode("utf-8", errors="replace").strip()))
    return done.stdout


def dbfs(value: float) -> float:
    if value <= 0:
        return float("-inf")
    return 20 * math.log10(value / 32768.0)


def peak_dbfs(pcm: bytes, first_samples: int | None = None) -> float:
    """The loudest sample, in dBFS, over the whole run or its opening."""
    samples = array.array("h")
    samples.frombytes(pcm if first_samples is None else pcm[: first_samples * 2])
    if not samples:
        return float("-inf")
    return dbfs(max(abs(v) for v in samples))


def rms_dbfs(samples: Sequence[int]) -> float:
    if not samples:
        return float("-inf")
    total = sum(float(v) * v for v in samples)
    return dbfs(math.sqrt(total / len(samples)))


def opens_with_silence(ffmpeg: str, path: Path, spec: dict) -> tuple[bool, float]:
    """Whether the file already carries the lead-in, and how loud its opening is."""
    pcm = decode(ffmpeg, path, spec["sample_rate"], spec["channels"])
    window = int(SILENCE_WINDOW_SECONDS * spec["sample_rate"]) * spec["channels"]
    loudest = peak_dbfs(pcm, window)
    return loudest < SILENCE_DBFS, loudest


def silence_file(ffmpeg: str, into: Path, spec: dict) -> Path:
    """Half a second of silence as its own MP3, at the original's rate."""
    out = into / "lead_in.mp3"
    layout = "mono" if spec["channels"] == 1 else "stereo"
    done = subprocess.run(
        [ffmpeg, "-hide_banner", "-loglevel", "error",
         "-f", "lavfi", "-i", "anullsrc=r={}:cl={}".format(
             spec["sample_rate"], layout),
         "-t", str(LEAD_IN_SECONDS),
         "-c:a", "libmp3lame", "-b:a", SILENCE_BITRATE, str(out), "-y"],
        stderr=subprocess.PIPE)
    if done.returncode != 0:
        raise SystemExit("ffmpeg could not build the lead-in: {}".format(
            done.stderr.decode("utf-8", errors="replace").strip()))
    return out


def pad(ffmpeg: str, path: Path, spec: dict) -> bytes:
    """The padded file's bytes: silence, then the original's frames copied.

    `-c copy` is the whole point. The concat demuxer hands the original's
    frames through without decoding them, so the spoken audio is not re-encoded
    and its rate, channels and bitrate are unchanged because they are the same
    frames.
    """
    with tempfile.TemporaryDirectory() as temporary:
        workspace = Path(temporary)
        lead_in = silence_file(ffmpeg, workspace, spec)
        listing = workspace / "parts.txt"
        listing.write_text(
            "file '{}'\nfile '{}'\n".format(
                str(lead_in).replace("\\", "/"), str(path).replace("\\", "/")),
            encoding="utf-8")
        out = workspace / "padded.mp3"
        done = subprocess.run(
            [ffmpeg, "-hide_banner", "-loglevel", "error",
             "-f", "concat", "-safe", "0", "-i", str(listing),
             "-c", "copy", str(out), "-y"],
            stderr=subprocess.PIPE)
        if done.returncode != 0:
            raise SystemExit("ffmpeg could not concatenate {}: {}".format(
                path.name, done.stderr.decode("utf-8", errors="replace").strip()))
        return out.read_bytes()


def lead_in_at(new_pcm: bytes, old_pcm: bytes, rate: int) -> int | None:
    """Where the original's audio starts inside the padded one, in samples.

    The original's frames were copied rather than re-encoded, so a window of
    the original's own samples occurs in the padded file verbatim and can
    simply be searched for. A window a second in is used because the opening of
    a narration can be quiet enough to match in more than one place.
    """
    probe_at = min(rate, max(0, len(old_pcm) // 2 - 4096))
    pattern = old_pcm[probe_at * 2: (probe_at + 4096) * 2]
    if not pattern:
        return None
    found = new_pcm.find(pattern)
    if found == -1 or found % 2:
        return None
    return found // 2 - probe_at


def align(new_pcm: bytes, old_pcm: bytes, rate: int, centre: int) -> int:
    """A fallback offset for audio that was not copied, by least squares.

    Nothing in this script re-encodes, so this is only reached if a file was
    produced some other way. It is here so that `--check` reports a real
    difference rather than no alignment at all.
    """
    new = array.array("h")
    new.frombytes(new_pcm)
    old = array.array("h")
    old.frombytes(old_pcm)
    span = min(len(old), rate * 4)
    best = None
    for offset in range(max(0, centre - rate), centre + rate + 1):
        if offset + span > len(new):
            continue
        error = 0.0
        for i in range(0, span, 7):
            delta = new[offset + i] - old[i]
            error += float(delta) * delta
        if best is None or error < best[1]:
            best = (offset, error)
    return 0 if best is None else best[0]


def compare(ffmpeg: str, name: str, old_bytes: bytes, new_path: Path,
            spec: dict) -> dict:
    """One file's evidence: the lead-in, the samples and the two durations."""
    rate, channels = spec["sample_rate"], spec["channels"]
    old_pcm = decode(ffmpeg, old_bytes, rate, channels)
    new_pcm = decode(ffmpeg, new_path, rate, channels)
    old_samples = len(old_pcm) // 2
    new_samples = len(new_pcm) // 2

    offset = lead_in_at(new_pcm, old_pcm, rate)
    copied = offset is not None and offset >= 0
    if not copied:
        offset = align(new_pcm, old_pcm, rate, int(LEAD_IN_SECONDS * rate))

    tail = new_pcm[offset * 2:]
    identical = tail == old_pcm
    if identical:
        worst, error_db = 0, float("-inf")
    else:
        new = array.array("h")
        new.frombytes(tail[: old_samples * 2])
        old = array.array("h")
        old.frombytes(old_pcm[: len(new) * 2])
        differences = [new[i] - old[i] for i in range(len(new))]
        worst = max(abs(d) for d in differences) if differences else 0
        error_db = rms_dbfs(differences)

    lead_in = offset / (rate * channels)
    old_duration = old_samples / (rate * channels)
    new_duration = new_samples / (rate * channels)
    tolerance = FRAME_SAMPLES / rate
    window = int(SILENCE_WINDOW_SECONDS * rate) * channels

    return {
        "name": name,
        "sample_rate": rate,
        "channels": channels,
        "old_bitrate": spec["bit_rate"],
        "old_bytes": len(old_bytes),
        "new_bytes": new_path.stat().st_size,
        "lead_in_seconds": lead_in,
        "lead_in_samples": offset,
        "lead_in_within_a_frame": abs(lead_in - LEAD_IN_SECONDS) <= tolerance,
        "frames_copied": copied,
        "samples_identical": identical,
        "worst_sample_difference": worst,
        "difference_dbfs": error_db,
        "signal_dbfs": rms_dbfs(array.array("h", old_pcm[: old_samples * 2])),
        "old_duration": old_duration,
        "new_duration": new_duration,
        "duration_added": new_duration - old_duration,
        "duration_within_a_frame":
            abs((new_duration - old_duration) - LEAD_IN_SECONDS) <= tolerance,
        "opening_peak_dbfs": peak_dbfs(new_pcm, window),
        "opening_is_quiet": peak_dbfs(new_pcm, window) < SILENCE_DBFS,
        "tolerance_seconds": tolerance,
    }


def report(rows: Sequence[dict]) -> int:
    """Print the per-file evidence and return the number of findings."""
    findings = 0
    for row in rows:
        print()
        print("  {}".format(row["name"]))
        print("    {} Hz, {} channel, {} bps, {} bytes in, {} bytes out".format(
            row["sample_rate"], row["channels"], row["old_bitrate"],
            row["old_bytes"], row["new_bytes"]))
        print("    lead-in: {:.1f} ms, {} samples{}".format(
            row["lead_in_seconds"] * 1000, row["lead_in_samples"],
            "" if row["lead_in_within_a_frame"] else
            " (outside one frame of {:.0f} ms)".format(
                LEAD_IN_SECONDS * 1000)))
        if not row["lead_in_within_a_frame"]:
            findings += 1
            fail("{}: the lead-in is more than one frame ({:.0f} ms) from "
                 "{:.0f} ms".format(row["name"], row["tolerance_seconds"] * 1000,
                                    LEAD_IN_SECONDS * 1000))
        if row["samples_identical"]:
            print("    samples after the lead-in: identical to the original, "
                  "all {} of them".format(
                      int(row["old_duration"] * row["sample_rate"]
                          * row["channels"])))
        else:
            print("    samples after the lead-in: worst difference {}, "
                  "{:.1f} dBFS against a {:.1f} dBFS signal".format(
                      row["worst_sample_difference"], row["difference_dbfs"],
                      row["signal_dbfs"]))
        print("    frames copied rather than re-encoded: {}".format(
            "yes" if row["frames_copied"] else "no"))
        if not row["frames_copied"]:
            findings += 1
            fail("{}: the original's frames are not in the padded file, so it "
                 "was re-encoded".format(row["name"]))
        print("    duration: {:.3f} s to {:.3f} s, {:+.3f} s{}".format(
            row["old_duration"], row["new_duration"], row["duration_added"],
            "" if row["duration_within_a_frame"] else " (outside one frame)"))
        if not row["duration_within_a_frame"]:
            findings += 1
            fail("{}: the duration grew by {:.3f} s, not {:.1f} s within one "
                 "frame".format(row["name"], row["duration_added"],
                                LEAD_IN_SECONDS))
        print("    opening {:.0f} ms peak: {:.1f} dBFS{}".format(
            SILENCE_WINDOW_SECONDS * 1000, row["opening_peak_dbfs"],
            "" if row["opening_is_quiet"] else
            " (above the {:.0f} dBFS bar)".format(SILENCE_DBFS)))
        if not row["opening_is_quiet"]:
            findings += 1
            fail("{}: the opening {:.0f} ms is not below {:.0f} dBFS".format(
                row["name"], SILENCE_WINDOW_SECONDS * 1000, SILENCE_DBFS))
    return findings


def committed(name: str, ref: str) -> bytes:
    """One recording as a git ref holds it, which is the unpadded original."""
    done = subprocess.run(
        ["git", "show", "{}:{}/{}".format(ref, AUDIO_REL, name)],
        cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if done.returncode != 0:
        raise SystemExit("git could not read {} at {}: {}".format(
            name, ref, done.stderr.decode("utf-8", errors="replace").strip()))
    return done.stdout


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--plan", action="store_true",
        help="probe the six and say what would change, and write nothing")
    parser.add_argument(
        "--confirm", action="store_true",
        help="pad the files that are not padded yet, in place")
    parser.add_argument(
        "--check", action="store_true",
        help="compare the files on disk against the originals in git")
    parser.add_argument(
        "--against", default="HEAD",
        help="the git ref holding the unpadded originals (default HEAD, which "
             "is the original until the padded files are committed)")
    parser.add_argument(
        "--ffmpeg",
        help="the directory holding ffmpeg and ffprobe, or the ffmpeg binary")
    args = parser.parse_args(argv)

    ffmpeg = tool("ffmpeg", args.ffmpeg)
    ffprobe = tool("ffprobe", args.ffmpeg)
    names = recordings()
    print("{}, from hero.audio in {}".format(
        "{} recordings".format(len(names)), MATCHES.relative_to(ROOT)))
    print("  ffmpeg: {}".format(ffmpeg))

    if args.check:
        print()
        print("comparing {} against {}, decoded to PCM both sides".format(
            AUDIO_REL, args.against))
        rows = []
        for name in names:
            path = AUDIO_DIR / name
            spec = probe(ffprobe, path)
            rows.append(compare(
                ffmpeg, name, committed(name, args.against), path, spec))
        findings = report(rows)
        print()
        if findings:
            print("{} findings".format(findings), file=sys.stderr)
            return 1
        print("every file: the lead-in is within one frame of {:.0f} ms, the "
              "samples after it are the original's, and the duration grew by "
              "that lead-in and nothing more".format(LEAD_IN_SECONDS * 1000))
        return 0

    state = []
    for name in names:
        path = AUDIO_DIR / name
        if not path.is_file():
            raise SystemExit("{} is not on disk; scripts/tts_hero.py is what "
                             "writes it, and it is the paid path".format(name))
        spec = probe(ffprobe, path)
        padded, loudest = opens_with_silence(ffmpeg, path, spec)
        state.append((name, path, spec, padded, loudest))

    print()
    for name, _path, spec, padded, loudest in state:
        print("  {}: {} Hz, {} channel, {} bps, opening peak {:.1f} dBFS, "
              "{}".format(name, spec["sample_rate"], spec["channels"],
                          spec["bit_rate"], loudest,
                          "already padded" if padded else "to pad"))
    todo = [one for one in state if not one[3]]
    print()
    print("{} of {} to pad, {:.0f} ms of silence each, frames copied and not "
          "re-encoded".format(len(todo), len(state), LEAD_IN_SECONDS * 1000))

    if not args.confirm:
        print()
        print("nothing was written. --confirm is what writes it.")
        return 0
    if not todo:
        print()
        print("nothing to do: every file already opens below {:.0f} dBFS for "
              "its first {:.0f} ms".format(SILENCE_DBFS,
                                           SILENCE_WINDOW_SECONDS * 1000))
        return 0

    print()
    rows = []
    for name, path, spec, _padded, _loudest in todo:
        original = path.read_bytes()
        path.write_bytes(pad(ffmpeg, path, spec))
        print("  {}: {} bytes to {} bytes".format(
            name, len(original), path.stat().st_size), flush=True)
        rows.append(compare(ffmpeg, name, original, path, spec))

    print()
    print("and the same comparison --check makes, on what was just written:")
    findings = report(rows)
    print()
    if findings:
        print("{} findings".format(findings), file=sys.stderr)
        return 1
    print("every file padded: the lead-in is within one frame of {:.0f} ms, "
          "the samples after it are the original's, and the duration grew by "
          "that lead-in and nothing more".format(LEAD_IN_SECONDS * 1000))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
