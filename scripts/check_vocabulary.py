r"""Every word the app can speak, read against a pronouncing dictionary.

The pronunciation table has two entries and both arrived the same way: a
person heard a voice say a word wrong, after the audio was paid for. "lead"
came back as "led" and "minute" as "my-NEWT". Both were predictable before
anybody listened, because both are heteronyms: one spelling with more than one
pronunciation, and nothing in the sentence to tell a voice which is meant.

This looks the vocabulary up in advance. A word with more than one
pronunciation in the CMU Pronouncing Dictionary is a word that may come out
wrong, so it gets reviewed once and either gains an entry in
`app/pronunciation.py` or goes on `CHECKED_NO_ENTRY_NEEDED` there with the
reason. `tests/test_vocabulary.py` fails on a flagged word that is on neither
list, so new vocabulary cannot reach a voice unreviewed.

**It is a dictionary lookup and not a judgement about audio.** A flag means
"two pronunciations exist for this spelling", which is a reason to listen, not
evidence that a voice gets it wrong. Most flags are reduction and accent
variants of the same word: "the" as `DH AH0` or `DH IY0`, "was" as `W AA1 Z`
or `W AH0 Z`. Those are what the reviewed list is for. The ones worth acting
on are the handful where the two pronunciations are different words.

**Where the vocabulary comes from**, and none of it is a list typed out here:

| Source | What it contributes |
| ------ | ------------------- |
| `HEADER_WORDING`, `SCORE_LINE`, `HEADER_TAIL` | the header, every transition |
| `EVENT_VERBS` | how each event type is said |
| `template_narration`'s own words | "Minute", "shot and scored for" |
| `app/web/matches.json` | the team names, which the header and the narration both say |
| `tests/golden/` | the words in the recorded narrations |

**No source here enumerates player names**, and that is deliberate: a
dictionary has nothing useful to say about "Cuccittini", and the names it does
hold are in it as names rather than as English words. What a name needs is a
listener, which is what the samples in `docs/VOICE.md` are for.

A name still arrives when a recorded narration contains one. "maradona" is in
the vocabulary from the speech request in `tests/golden/tts_synthesize.json`,
and the dictionary lists one pronunciation for it, so it is not flagged. That
is the rule working as written rather than an exception to it: the words in a
recorded narration are collected, whatever kind of word they are.

**A golden fixture counts only if it is a recording.** Each one says in its
own provenance block whether it is, and
`tests/golden/watsonx_text_generation.json` says it is not: it was written by
hand from IBM's published schema, and its placeholder text is not something
this app would ever speak. Reading the flag rather than a list of filenames
means a fixture added later is included or excluded by what it says about
itself.

**The dictionary is a dependency and is never fetched.** `cmudict` is a dev
dependency in `pyproject.toml` and ships the data in the package, so this runs
offline and so does the suite. `tests/conftest.py` blocks the network for
every test, which a dictionary downloaded at test time would have tripped.

Run it:

    .\.venv-prelude\Scripts\python.exe -I scripts\check_vocabulary.py

It exits non-zero when a flagged word has not been reviewed, so it can gate a
commit; the same condition is a test, which is what makes it run every time.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Mapping, Sequence

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# The report prints IPA out of the pronunciation table, and a Windows console
# is cp1252 by default, which cannot encode "liːd".
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.narration_prompt import EVENT_VERBS  # noqa: E402
from app.orchestrator_contract import (  # noqa: E402
    HEADER_TAIL,
    HEADER_WORDING,
    SCORE_LINE,
)
from app.pronunciation import (  # noqa: E402
    CHECKED_NO_ENTRY_NEEDED,
    PRONUNCIATIONS,
    spoken_text,
)

#: Where the team names are. `scripts/write_headers.py` builds the header from
#: the same file, so these are the names the app actually speaks.
MATCHES = ROOT / "app" / "web" / "matches.json"

#: The frozen hero narrations. `scripts/tts_hero.py` sends these words to be
#: spoken, so they are vocabulary in the same way the template's are. They
#: were not collected while that script spoke `template_narration`, whose
#: words come from `EVENT_VERBS` and `TEMPLATE_WORDS` above; a model writes
#: from a wider vocabulary than the template does, which is exactly why this
#: file exists.
NARRATIONS = ROOT / "app" / "web" / "narrations.json"

#: The recorded exchanges. Each is included only if its own provenance block
#: says it is a recording.
GOLDEN = ROOT / "tests" / "golden"

#: The words `template_narration` writes itself, rather than taking from
#: `EVENT_VERBS`: the clock line and the closing sentence. They are here
#: because they are literals in that function, and a test holds this list to
#: what the function actually produces.
TEMPLATE_WORDS = ("Minute", "shot and scored for")

#: A word. Apostrophes and hyphens are inside one, so "Here's" is one word and
#: "last-minute" is one; a digit is not part of one, because "54" is a number
#: the voice reads as a number and no dictionary entry governs it.
WORD = re.compile(r"[A-Za-z][A-Za-z'’-]*")

#: The placeholders in the wording tables. They are filled with team names,
#: which are collected from `matches.json` instead, so the brace names
#: themselves are not vocabulary.
PLACEHOLDERS = re.compile(r"\{[a-z_]+\}")

#: A `<phoneme>` or `<break>` element, so a recorded speech request
#: contributes the words it says and not the markup around them.
MARKUP = re.compile(r"<[^>]+>")


def _words(text: str) -> set[str]:
    """The words in `text`, lower case, markup and placeholders removed."""
    text = MARKUP.sub(" ", PLACEHOLDERS.sub(" ", text))
    return {found.lower() for found in WORD.findall(text)}


def _is_recording(fixture: Mapping) -> bool:
    """Whether a golden fixture says of itself that it is a recording.

    The three fixtures spell the claim three ways, because each was written
    for its own backend. Reading all three is how a fixture is judged by what
    it says rather than by its filename.
    """
    provenance = fixture.get("provenance", {})
    if provenance.get("kind") == "recording":
        return True
    return bool(
        provenance.get("is_a_recording") or provenance.get("is_recording")
    )


def _golden_texts() -> dict[str, list[str]]:
    """The narration-shaped text in each golden recording, by filename."""
    found: dict[str, list[str]] = {}
    for path in sorted(GOLDEN.glob("*.json")):
        fixture = json.loads(path.read_text(encoding="utf-8"))
        if not _is_recording(fixture):
            continue
        texts = []
        # An Ollama recording: the model's answer.
        answer = fixture.get("response", {})
        if isinstance(answer, dict) and isinstance(answer.get("response"), str):
            texts.append(answer["response"])
        # A speech recording: the text that was sent to be spoken.
        request = fixture.get("request", {})
        if isinstance(request, dict) and isinstance(request.get("text"), str):
            texts.append(spoken_text(request["text"]))
        if texts:
            found[path.name] = texts
    return found


def speakable() -> dict[str, set[str]]:
    """Every word the app can speak, mapped to where it comes from."""
    sources: dict[str, list[str]] = {
        "the header": list(HEADER_WORDING.values()) + [SCORE_LINE, HEADER_TAIL],
        "the event verbs": list(EVENT_VERBS.values()),
        "the narration template": list(TEMPLATE_WORDS),
    }

    matches = json.loads(MATCHES.read_text(encoding="utf-8"))
    sources["the team names"] = sorted(
        {entry[side] for entry in matches["matches"]
         for side in ("home_team", "away_team")}
    )

    if NARRATIONS.is_file():
        frozen = json.loads(NARRATIONS.read_text(encoding="utf-8"))
        sources["the frozen narrations"] = [
            entry["text"] for entry in frozen["narrations"].values()
        ]

    for name, texts in _golden_texts().items():
        sources["tests/golden/" + name] = texts

    vocabulary: dict[str, set[str]] = {}
    for where, texts in sources.items():
        for text in texts:
            for word in _words(text):
                vocabulary.setdefault(word, set()).add(where)
    return vocabulary


def pronunciations() -> Mapping[str, list[list[str]]]:
    """The CMU Pronouncing Dictionary, from the installed package.

    Imported here rather than at module scope so that the vocabulary can be
    collected and printed without it, and so the import error names this
    function when the dependency is missing.
    """
    import cmudict

    return cmudict.dict()


def variants(word: str, dictionary: Mapping) -> list[str]:
    """The distinct pronunciations the dictionary lists for `word`.

    Stress digits are kept. Two pronunciations differing only in stress are
    still two pronunciations, and the reviewed list is a better place to
    record "this one is only stress" than a filter here would be: a filter
    would decide it silently and for every word at once.
    """
    seen: list[str] = []
    for phonemes in dictionary.get(word, []):
        said = " ".join(phonemes)
        if said not in seen:
            seen.append(said)
    return seen


def report(verbose: bool = False) -> list[str]:
    """Print the vocabulary report. Returns the unreviewed flagged words."""
    vocabulary = speakable()
    dictionary = pronunciations()

    flagged: dict[str, list[str]] = {}
    unknown: list[str] = []
    for word in sorted(vocabulary):
        said = variants(word, dictionary)
        if not said:
            unknown.append(word)
        elif len(said) > 1:
            flagged[word] = said

    entered = [word for word in flagged if word in PRONUNCIATIONS]
    reviewed = [
        word for word in flagged
        if word not in PRONUNCIATIONS and word in CHECKED_NO_ENTRY_NEEDED
    ]
    unreviewed = [
        word for word in flagged
        if word not in PRONUNCIATIONS and word not in CHECKED_NO_ENTRY_NEEDED
    ]

    print("checking every word the app can speak against the CMU dictionary")
    print("  {} words, from {} source(s)".format(
        len(vocabulary), len({s for w in vocabulary.values() for s in w})
    ))
    print("  {} with more than one listed pronunciation".format(len(flagged)))
    print()

    print("  in app/pronunciation.py ({})".format(len(entered)))
    for word in entered:
        print("    {:<14} {:<10} {}".format(
            word, PRONUNCIATIONS[word], " / ".join(flagged[word])
        ))
    print()

    print("  checked, no entry needed ({})".format(len(reviewed)))
    for word in reviewed:
        print("    {:<14} {}".format(word, CHECKED_NO_ENTRY_NEEDED[word]))
        if verbose:
            print("      {}".format(" / ".join(flagged[word])))
    print()

    if unknown:
        print("  not in the dictionary, so not checkable ({})".format(
            len(unknown)
        ))
        for word in unknown:
            print("    {:<14} {}".format(
                word, ", ".join(sorted(vocabulary[word]))
            ))
        print()

    if unreviewed:
        print("  NOT REVIEWED ({}), and each needs a decision:".format(
            len(unreviewed)
        ))
        for word in unreviewed:
            print("    {:<14} {}".format(word, " / ".join(flagged[word])))
            print("      spoken in: {}".format(
                ", ".join(sorted(vocabulary[word]))
            ))
        print()
        print("  Either add it to PRONUNCIATIONS in app/pronunciation.py or "
              "put it on")
        print("  CHECKED_NO_ENTRY_NEEDED there with the reason it needs none.")
    else:
        print("  every flagged word has been reviewed")
    return unreviewed


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="print the pronunciations of the reviewed words too",
    )
    args = parser.parse_args(argv)
    return 1 if report(verbose=args.verbose) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
