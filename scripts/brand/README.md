# The brand source

`scripts/brand/build_svg.py` draws every brand file the app serves, from one
set of numbers, into `app/web/assets/brand/`. The mark is "Prelude." in Syne
ExtraBold with the "u" redrawn as seven amber bars; the icon is those bars
alone; the tagline is "Leave your seat. Not the game."

    .\.venv-prelude\Scripts\python.exe -I scripts\brand\build_svg.py --plan
    .\.venv-prelude\Scripts\python.exe -I scripts\brand\build_svg.py --check
    .\.venv-prelude\Scripts\python.exe -I scripts\brand\build_svg.py --confirm

`--check` compares what the numbers draw with what is committed and writes
nothing, so a brand file edited by hand, or a number changed without a redraw,
can be found without rewriting anything.

## The two fonts, committed beside the script

The mark is these fonts' outlines, so a redraw from another copy of a font is
a different mark. Both are the variable fonts rather than static instances:
the script instantiates the one weight it uses.

| File | Family | Weight used | Version |
| ---- | ------ | ----------- | ------- |
| `scripts/brand/fonts/Syne-wght.ttf` | Syne, variable (`wght` 400 to 800) | 800 | 2.200 |
| `scripts/brand/fonts/HankenGrotesk-wght.ttf` | Hanken Grotesk, variable (`wght` 100 to 900) | 500 | 3.013 |

**Both are under the SIL Open Font License, Version 1.1**, and each licence is
committed beside the font it covers: `scripts/brand/fonts/OFL-Syne.txt` and
`scripts/brand/fonts/OFL-HankenGrotesk.txt`. Syne is copyright 2017 The Syne
Project Authors; Hanken Grotesk is copyright 2021 The Hanken Grotesk Project
Authors.

Where each one came from, and its SHA-256 as committed:

| File | Source | SHA-256 |
| ---- | ------ | ------- |
| `scripts/brand/fonts/Syne-wght.ttf` | `https://raw.githubusercontent.com/google/fonts/main/ofl/syne/Syne[wght].ttf` | `ce5ac77142a65cab2248a1a2ebb740b1d4d9c20b52488877d3ff664d1356104a` |
| `scripts/brand/fonts/HankenGrotesk-wght.ttf` | `https://raw.githubusercontent.com/google/fonts/main/ofl/hankengrotesk/HankenGrotesk[wght].ttf` | `813b3f8fa0965405669a89b38e51bbefd95eef6b8e20d1cb2d8c10cce062662f` |

The upstream filenames carry the axis in square brackets, which several of
this repo's own path checks do not accept in a name, so each file is committed
under the same name with the brackets dropped. Nothing else about them is
changed.

These two are not the files a browser loads. `app/web/assets/fonts/` holds the
`woff2` subsets the screens read, written by `scripts/fetch_fonts.py`, and
`woff2` needs a Brotli decoder to open, which is why the generator reads
TrueType.
