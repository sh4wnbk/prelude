# Task 33: the brand, and the copy that was not read

**This is a record, not a description of the repo today.** Present tense in it
means 2026-11-14, the day the task closed. `HANDOFF.md` is the only file that
describes the repo now, and `docs/history/README.md` says where each decision
below now lives.

**What Shawn asked for on 2026-11-14.** The brand was settled in the pitch
thread and had never been given to the build: the mark is "Prelude." in Syne
with the "u" drawn as seven amber elements, the icon is those elements alone,
and the tagline is "Leave your seat. Stay in the game." The source files were
outside the repo. Beside that, the moment card still carried the mockup's
broadcast quote, whose 2022 text said "Álvarez back to Mac Allister" over a ball
the feed records going 36 yards forward.

**The brand source** (`b57dc7e`). `scripts/brand/build_svg.py` draws all four
files the app serves into `app/web/assets/brand/` from one set of numbers:
the wordmark, the icon rounded and square, and the launch screen's layout at
390 by 844. Two changes from the copy in the pitch thread: it writes
`prelude_icon_square.svg` too, which that copy had produced and then lost, and
it drops a dead function that referenced an undefined name and could not have
run. The billboard panel is not written, because nothing in the app serves it.
`--check` draws everything and compares; all four committed files, the square
icon included, are byte for byte what the numbers draw. The mark is the
outlines of two fonts, so both variable fonts are committed beside the script
with their licences, both SIL Open Font License 1.1, and
`scripts/brand/README.md` records each source URL and checksum.

**The icon** (`d98d781`). Task 32's "P." was a placeholder for a brand that
had not arrived. The icon is the seven bars, which is the part of the mark
that survives being 32 px. `scripts/make_icons.py` replaces
`scripts/make_mark.py` and reaches nothing: `favicon.svg` is
`prelude_icon.svg` itself, corners rounded because a tab draws an icon as it
is given, and the four PNGs are rasterised from `prelude_icon_square.svg`,
whose corners are square because iOS, Android and a maskable install each
round or crop one themselves. The bitmaps are drawn from that file's own path,
matched whole against capsules and read back, so a file the script cannot read
is one it refuses to rasterise rather than guess at. The manifest offers the
512 as "any maskable": the outermost corner of the widest bar is 30% of the
square from the centre, against a safe radius of 40%. Every screen links the
same four paths, so no screen changed.

**The launch screen** (`6c4e515`). The mark is inlined from
`prelude_mark.svg`, so the white letters and the amber bars are the drawing
rather than a font the machine may not have, and it costs no request of its
own in the first frame. Under it is the tagline as real text in Hanken Grotesk
500 at 16 px in amber. The layout is `prelude_launch.svg`'s own and was
measured in Chromium at 390 by 844: the mark 300 by 32, the gap 20, the pair
24 px above the middle. It is announced as one image named "Prelude. Leave
your seat. Stay in the game.", and the inlined mark carries `aria-hidden` and
no title, because a name inside something already named is a second name for
one thing. It now paints on every full load of the root page; it painted once
per tab, decided in the head out of `sessionStorage`, and the shell reads no
storage at all now.

**The quote, and the lines nothing had read** (`6abc2ab`). The broadcast quote
is gone from the card, from `hero.quote` and `hero.quote_names`, from the
renderer, from the gate that checked the names in it, and from the set of
fields a grounding label may stand over, which is the narration alone now. Its
two openings and the guillemet are banned copy.

Then the search Shawn asked for, over every screen and `app/web/matches.json`.
Six lines described the play and were not held to the feed:

| Line | What was unheld |
| ---- | --------------- |
| the 1986 hero caption | "solo run from his own half, past four England players"; only the clock in front of it was checked |
| the 1986 hero share text | "solo goal"; only that it names the scorer was checked |
| the 1986 opener's title and body | "opener", "Reid's error", "nine yards"; that moment carried no grounding block at all |
| the 1986 solo goal's title and body | the same claims as the caption, and no block |
| the 2022 hero caption and share text | "a counter", "began in Argentina's own half"; the hero had no block |
| the 2022 "Di María doubles it" title | "doubles"; the block behind it said nothing about which goal of the match it was |

All six are held rather than removed, because each one is true and the feed
says so. The three rules are in Current state. Six grounding keys are new:
`solo_run`, `own_half`, `dribbled_past`, `yards_from_goal`, `recovers_error`
and `match_goal_number`.

Two readings were wrong on the first pass and the tests found both. `solo_run`
as "nobody else of his team touched it" is satisfied by a one-touch finish,
which is exactly what the 2022 hero is, so it also asks the feed for a carry
or a dribble of the scorer's own. And a name was read as the last word of a
player's name, which for "Jorge Alberto Francisco Valdano Castellano" is
"Castellano": a line saying "Valdano" matched nothing, so that check had never
fired. Every part of a name long enough to be one is read now.

**The two pills** (`ed129f4`). Live's "PLAY DATA CONNECTED" and both Moments
cards' "AI AUDIO NARRATION, PLAY DATA SYNC" were Task 32's second "Found, not
fixed" line. Nothing checks a connection and nothing synchronises. Both say
"PLAY-BY-PLAY DATA" now, which is the phrase the list card and the ticket
already use, and both old phrases are banned copy.

**The docs** (`25bb4a6`). `docs/DESIGN.md` gains "The mark": what the mark,
the icon and the tagline are, the two colours as the system's own tokens,
where each of the four brand files lives and what reads it, and the icon set
with the size of each file and where it is shown. `README.md` says the app has
a mark and that the first frame of a load is it.

**What CI found, which no local run could.** `scripts/make_icons.py --check`
compared the committed PNGs byte for byte. It passed here and failed on the
runner with all four reported as DIFFERS. Pillow 12.3.0 is what both sides
install; it draws the same image and encodes it through whatever zlib its
wheel was built against. Run under Linux with the same Pillow against the same
committed files, the four come out 656, 3,085, 3,216 and 9,094 bytes where
this machine writes 654, 3,049, 3,203 and 8,967, and every pixel of all four
is identical. The check decodes both sides and compares pixels now; the SVG
and the manifest are text and are still compared as written. A byte comparison
there was a claim about zlib rather than about the icon.

**The evidence.** `pytest -q` reports `2067 passed`, up from `2012`; `pytest
tests/browser` reports `88 passed`, up from `86`; all five gates exit 0;
`git status` is clean after both. Two screenshots are committed, both taken in
headless Chromium at 390 by 844 at two device pixels per CSS pixel:
`docs/evidence/task33_launch_screen.png` is the shell with matches.json held
for three seconds, and
`docs/evidence/task33_moment_card_below_the_player.png` is the 1986 card
scrolled to the foot, where the quote block was. The icon at both sizes is
`app/web/assets/icon/favicon-32.png` and
`app/web/assets/icon/apple-touch-icon-180.png`, which every screen links.

**Found, not fixed.**

- **At 32 px the seven bars come back as three runs of amber.** A bar is
  1.5 px wide there and a gap 1.25 px, so some gaps do not survive the
  reduction. Nothing can separate them at that size; the vector is what a
  browser that can read one takes, and `tests/test_the_mark.py` records the
  measurement rather than asserting a number nobody measured.
- **A committed PNG is only reproducible to the pixel, not to the byte.**
  `scripts/make_icons.py --check` compares pixels for that reason, so a
  bitmap re-encoded by a different zlib with the same image in it passes. A
  file whose bytes changed and whose pixels did not is invisible to the
  check, which is the right trade and is not free.
- **`prelude_launch.svg` is committed and nothing at runtime serves it.** It
  is the layout the CSS was measured against, and the measurements are in the
  browser suite, so the file could go. It stays because it is what a designer
  opens.
- **A claim phrase in `CLAIMS` is a phrase and not a reading of the sentence.**
  "past" needs a `dribbled_past` key wherever it appears, so a line saying
  "walks past the bench" would be asked for one. Nothing in the copy says
  that, and the alternative is parsing.
- **Nothing holds the Moments cards' `aria-label` to the title it repeats.**
  The label is built from the title by the renderer and the inline copy
  carries both, but the check that the inline copy matches
  `app/web/matches.json` is a substring search, so a stale heading beside a
  correct label would pass.
- **The icon font is still 1.14 MB of the 1.34 MB of committed fonts**, and
  the two variable fonts add 280 KB more under `scripts/brand/fonts/`, which
  no browser loads. Task 32's finding stands; the fonts beside the generator
  are the price of the mark being reproducible.
- **The smoke subset does not open the launch screen.** It checks the moment
  card, the label, the claim count and the three endpoints against the live
  site; the first frame of a visit is checked against the working tree only.
- **The compiled stylesheet is not rebuilt by CI**, and **CI does not run on a
  schedule, and the smoke workflow cannot be made to fail by a failing
  deploy.** All three are Task 32's and Task 30's and all three still stand.
