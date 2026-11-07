"""Plain spaces and plain hyphens, where a model wrote an invisible one.

Two candidate narrations of 2026-10-30 arrived carrying a character nobody
could see. One wrote "fifty-four" with a `NON-BREAKING HYPHEN` (U+2011) and
another wrote "Terry Butcher" with a `NARROW NO-BREAK SPACE` (U+202F) inside
the name. Both passed `app/grounding.py`, correctly: a narrow space is
whitespace, so the name either side of it still matched, and a hyphen is not a
name, an action, a clock or a number. Both would have been sent to the speech
service as written, and what a voice does with them is unknown.

So the narration is made plain before anything reads it: `plain` rewrites the
characters that *are* a plain space or a plain hyphen written another way, and
touches nothing else.

**It is not a way past a rule.** A dash is left exactly as written. `CLAUDE.md`
bans em dashes from copy and `app/grounding.py` refuses both the em dash and
the en dash, so turning one into a hyphen here would quietly undo a ban that
exists for a reason, and would do it in the one place nobody would look. The
same goes the other way: this fixes a character, never a word, so nothing in
`BANNED_PATTERNS` becomes sayable by passing through it.

**What is a hyphen and what is a dash** is the line this draws, and it is the
Unicode names' line rather than one invented here. `HYPHEN`, `NON-BREAKING
HYPHEN`, `MINUS SIGN` and the two compatibility forms are the ASCII
`HYPHEN-MINUS` in another costume, so they become it. `FIGURE DASH`, `EN DASH`,
`EM DASH` and `HORIZONTAL BAR` are dashes, which is a punctuation mark rather
than a spelling of the hyphen, so they are left visible: the first two of
those are refused by the check and the other two are not, which is a gap in
what may be labelled rather than something to paper over here. Extending the
check's rules is Shawn's decision.

**The zero-width characters are removed rather than replaced.** A `ZERO WIDTH
SPACE` sits inside a word, so turning it into a space would split the word in
two; it carries no sound and nothing in this pipeline writes one, so it comes
out. A line break is a space separator this does not touch either: the
narration is one sentence per line and `app/grounding.py` reads those lines.

Standard library only, like every module in `app/` but the hosted
service in `app/api.py`.
"""

import unicodedata

#: The ASCII characters everything above is normalised towards.
SPACE = " "
HYPHEN = "-"

#: Characters that are the plain hyphen written another way, by their Unicode
#: name. Written out rather than detected, because no category separates a
#: hyphen from a dash: `Pd` holds both, and normalising `Pd` would turn an em
#: dash into a hyphen.
HYPHENS: dict[str, str] = {
    "‐": "HYPHEN",
    "‑": "NON-BREAKING HYPHEN",
    "−": "MINUS SIGN",
    "﹣": "SMALL HYPHEN-MINUS",
    "－": "FULLWIDTH HYPHEN-MINUS",
}

#: Dashes, which are left exactly as written. Here so a reader can see that
#: leaving them is a decision and so a test can hold it.
#:
#: The first two are in `BANNED_PATTERNS` in `app/grounding.py` and a narration
#: carrying either is refused. The other two are not, and a candidate carrying
#: one would reach a recording: `odd_characters` in
#: `scripts/hero_candidates.py` names it in the review file, which is the
#: reporting this file deliberately does not replace with a silent rewrite.
DASHES: dict[str, str] = {
    "–": "EN DASH",
    "—": "EM DASH",
    "‒": "FIGURE DASH",
    "―": "HORIZONTAL BAR",
}

#: Invisible characters with no sound, which are removed rather than replaced.
#: A zero-width space sits inside a word, so a space in its place would split
#: the word.
REMOVED: dict[str, str] = {
    "​": "ZERO WIDTH SPACE",
    "‌": "ZERO WIDTH NON-JOINER",
    "‍": "ZERO WIDTH JOINER",
    "⁠": "WORD JOINER",
    "﻿": "ZERO WIDTH NO-BREAK SPACE",
}

#: The newline, which is a narration's sentence separator here and not a
#: character to be flattened. `\\r` and `\\t` are left alone for the same
#: reason: nothing here is reformatting a narration's layout.
_KEPT_WHITESPACE = frozenset("\n\r\t\v\f")


def is_space_to_plain(character: str) -> bool:
    """Is this a space separator that should become a plain space?

    Read off the Unicode category rather than listed, so a space form nobody
    has seen yet is covered: `Zs` is every space separator, which is where
    `NO-BREAK SPACE`, `NARROW NO-BREAK SPACE`, the quad and em spaces, `THIN
    SPACE`, `MEDIUM MATHEMATICAL SPACE` and `IDEOGRAPHIC SPACE` all live. The
    plain space is already plain, and `Zl` and `Zp` are line and paragraph
    separators rather than spaces.
    """
    if character == SPACE or character in _KEPT_WHITESPACE:
        return False
    return unicodedata.category(character) == "Zs"


#: The curly apostrophe, and the straight one it stands in for.
#:
#: **A name is read with its possessive ending stripped, and the ending has
#: two spellings.** "France's half" is a claim about a recorded team, and the
#: run of 2026-11-05 wrote it with a `RIGHT SINGLE QUOTATION MARK` in the
#: middle, which is what a model trained on prose writes and what a keyboard
#: with smart quotes produces. The reading holds either one in the patterns it
#: matches with, and holding a character in two spellings everywhere it is
#: read is how one of the two gets missed; so the curly one is written as the
#: straight one before any of it is read.
#:
#: It is a separate function from `plain` on purpose. `plain` rewrites a
#: disguised space or hyphen and says it touches no word; an apostrophe is
#: part of a word, so the two normalisations are asked for separately and a
#: caller can see which it wanted.
CURLY_APOSTROPHE = "\u2019"
APOSTROPHE = "'"


def straight_apostrophes(text: str) -> str:
    """`text` with every curly apostrophe written as a straight one.

    One character for one character, so every offset into the text is where it
    was: `app/grounding.py` reads a clause span off a position in the sentence
    it checked.
    """
    return text.replace(CURLY_APOSTROPHE, APOSTROPHE)


def plain(text: str) -> str:
    """`text` with every disguised space and hyphen written plainly.

    Nothing else changes: the length may fall (a zero-width character is
    removed) but no word, dash, accent or line break is touched, and text that
    is already plain comes back identical.
    """
    out: list[str] = []
    for character in text:
        if character in REMOVED:
            continue
        if character in HYPHENS:
            out.append(HYPHEN)
        elif is_space_to_plain(character):
            out.append(SPACE)
        else:
            out.append(character)
    return "".join(out)


def unplain(text: str) -> tuple[tuple[str, str], ...]:
    """The disguised characters in `text`, as (character, Unicode name).

    What `plain` would change, said out loud. It is for reporting: a caller
    that normalised a narration can say which characters it rewrote rather
    than only that it rewrote some.
    """
    found: dict[str, str] = {}
    for character in text:
        if character in REMOVED:
            found.setdefault(character, REMOVED[character])
        elif character in HYPHENS:
            found.setdefault(character, HYPHENS[character])
        elif is_space_to_plain(character):
            found.setdefault(
                character, unicodedata.name(character, "unnamed character")
            )
    return tuple(sorted(found.items()))
