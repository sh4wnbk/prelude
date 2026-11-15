# Task 34: the share button and the launch screen

**This is a record, not a description of the repo today.** Present tense in it
means 2026-11-15, the day the task closed. `HANDOFF.md` is the only file that
describes the repo now, and `docs/history/README.md` says where each decision
below now lives.

**Task 35 changed three of the things below**, on the same day: the status bar
is translucent rather than opaque, the launch screen crossfades with the event
list, and the crossfade is kept for a fan who asked for less motion. The
record stands as it was written.

**What Shawn asked for on 2026-11-15.** Four things, two about the moment
card's share button and two about the launch screen. The button said "SHARE
CLIP" (`removed`) and shared a link and a line of text; where the browser had
no share sheet it flashed a confirmation for 1.5 seconds and did nothing. The launch
screen had no hold, so a fast load painted the mark and took it away inside a
couple of hundred milliseconds. And a home-screen icon opened on a white
screen, because nothing told iOS the app was one.

**The share button** (`84dcbeb`). It reads "SHARE", which is what it does.
With a share sheet, `navigator.share` is handed the title, the match's own
line out of `hero.share_text` and the card's URL, unchanged. Without one the
link goes to the clipboard and the button says "LINK COPIED" only once that
write has resolved. There are two ways for nothing to have been copied, and
the old branch announced success in both: `navigator.clipboard` is undefined
outside a secure context, so reaching `writeText` throws, and `writeText`
itself can be refused, so it rejects. Neither says anything now. "SHARE CLIP"
is a banned string in `scripts/scan_copy.py`, which caught the comment that
explained the change and is why that comment does not quote it.

`tests/browser/test_sharing.py` drives both paths on both matches: the sheet
stubbed and recording what it was given, the sheet absent and the clipboard
read back with `readText`, the clipboard refusing, and the clipboard gone
altogether. The line is read out of `app/web/matches.json` rather than written
down. The confirmation is asked of every frame a `MutationObserver` recorded,
because a line that flashed for 80 ms is a line a fan can read.

**The accessible name, found while writing that test** (`84dcbeb`). A Material
Symbol span holds a ligature, not a word, and it was inside the button's name:
Chromium computed "ios_share SHARE" for this button and "replay_10 REPLAY 10S"
for the one beside it, measured through the role selector rather than read off
the markup. Both icons carry `aria-hidden="true"` now. Every other icon in the
app is still inside its control's name, which is one attribute each over seven
screens and is under Open items rather than done here.

**The launch screen's timing** (`84dcbeb`). Three numbers instead of two, in
`app/web/index.html` and in `docs/DESIGN.md`: a 1,500 ms hold on every full
load, a 300 ms fade, and 2,500 ms as the last moment a fan can see it. The cap
bounds the screen rather than the start of the fade, so the fade begins at
2,200 ms. The clock is `performance.now()`, which counts from the start of the
navigation, so both bounds are about the load the fan started rather than
about whenever the script ran. Reduced motion gets the same hold and no fade.
What is left of the hold is rounded up before it is asked for, because
`setTimeout` truncates a fractional delay: CI caught the fade starting at
1,499.7 ms against a 1,500 ms hold, which is the truncation and nothing else.

Measured in headless Chromium at 390 by 844, as the moment the fade began and
the moment the screen left the page: 1,507 and 1,809 ms with matches.json
answered at once, 1,589 and 1,891 ms with it delayed 1.5 s, 2,209 and 2,510 ms
with it refused, and no fade and 1,507 ms with reduced motion.

**The startup images** (`71dbc4c`). iOS shows an `apple-touch-startup-image`
while a web app opened from the home screen is starting, and it takes one only
where the file is exactly that screen's own pixel size. `IPHONES` in
`scripts/brand/build_svg.py` is eleven screens in portrait, read off Apple's
point sizes, covering every iPhone on a current iOS; the script draws one PNG
each into `app/web/assets/launch/`, 560 KB in all, and the shell links each
behind a media query naming the CSS size, the pixel ratio and portrait. The
ratio is in the query because two iPhones share 414 by 896 at two ratios and
the wrong one of those is a quarter of the pixels. The shell also carries
`apple-mobile-web-app-capable` and `mobile-web-app-capable`, without which iOS
opens the icon in Safari's chrome and shows no startup image, and an opaque
black status bar rather than a translucent one: translucent puts the page
under the bar, and the screens read their safe-area insets inside the shell's
iframe, where `env()` is zero. The manifest's `background_color` was already
`#101319`, which is the colour these are drawn on, and a test now reads the
corner pixel of one against it rather than taking both from the same constant.

**They are drawn from the layout, not from `prelude_launch.svg`.** A screen
that is not 390 by 844 is not that file stretched: the mark stays 300 CSS px
wide on every screen because the CSS does not scale it. `launch_layout` is
those rules as numbers and `app/web/index.html` is the same rules in CSS,
which is two copies of one thing, so
`tests/browser/test_the_launch_screen.py` screenshots the shell at 390 by 844
at three device pixels to the CSS pixel and measures the drawing in it against
`launch-1170x2532.png`.

**That comparison found the one real difference.** The block was being centred
on the tagline's 16 px type where the CSS centres its 20 px line box, which
put the mark 2 CSS px below where the shell paints it. `prelude_launch.svg`
moves by those 2 px and the three renderings are one layout now. Measured
after the fix: the white box agreed to within 1 device pixel and the amber box
to within 3, the amber being the tagline, whose outermost column and lowest
descender row the browser leaves fainter than the threshold.

**The glyphs are rasterised from their own outlines.** No font is loaded to
draw a startup image: `fontTools` gives the contours, a pen flattens the
curves, and Pillow fills each shape even-odd so a counter in a letter is a
hole, oversampled four times and reduced. The seven bars are capsules, as the
icon's are. `--check` compares a PNG pixel by pixel and not byte by byte, for
the reason `scripts/make_icons.py` measured in Task 33, and the Linux runner
agreed with this machine on all eleven.

**The evidence.** `pytest -q` reports `2085 passed`, up from `2067`; `pytest
tests/browser` reports `100 passed`, up from `88`; all five gates exit 0;
`git status` is clean after both. `scripts/brand/build_svg.py --check` reports
every committed brand file is what the numbers draw, the eleven startup images
included, and the Linux runner agreed with this machine on all eleven. CI is
green on the last commit of this task.

**Found, not fixed.**

- **Every icon in the app is still inside its control's accessible name.**
  Measured on 2026-11-15: the Live nav link is named "sensors LIVE" and the
  Moments one "auto_awesome_motion MOMENTS". The two in the deck Task 34
  changed are fixed and the rest are a sweep over seven screens plus the
  markup `app/web/match-content.js` builds. It is under Open items with what
  it would take.
- **The startup images are 560 KB.** Each is a flat background and a band of
  anti-aliased drawing, and it is the band that costs: measured on
  2026-11-15, quantising one to a 256-colour palette took it from 51,633
  bytes to 24,665, which would halve the set. It was not taken, because it
  puts a quantiser between the drawing and the check that says the committed
  file is what the numbers draw, and the whole set is reproducible to the
  pixel as it stands.
- **Nothing here has run on an iPhone.** Every claim about the startup images
  is about the files, the links and the media queries: that each file is the
  pixel size its query names, that the drawing in it is the drawing the shell
  paints, and that the shell says it is a web app. Whether iOS picks the
  right one of the eleven is a thing only a device shows, and no device was
  used. The eleven screens and the query form are read from Apple's point
  sizes rather than measured here.
- **The cap is 2,500 ms and the screen left the page at 2,510.** A
  `setTimeout` is a floor and not a ceiling, so 10 ms is what nothing in the
  page can take off; the browser suite allows the runner's own scheduling on
  top of that and the measurement is in `docs/DESIGN.md`.
- **A launch screen that is interrupted is not covered.** The suite drives a
  load, a reload, a new tab, a slow list, a refused list and a list that
  never answers. A fan who navigates away inside the hold, or whose tab is
  backgrounded so the timers are throttled, is not among them.
- **`prelude_launch.svg` is committed and nothing at runtime serves it**, and
  **the icon font is still 1.14 MB of the committed fonts**, and **the smoke
  subset does not open the launch screen**, and **the compiled stylesheet is
  not rebuilt by CI**, and **CI does not run on a schedule**, and **the smoke
  workflow cannot be made to fail by a failing deploy**. All six are Task
  33's, Task 32's and Task 30's, and all six still stand.
