# Task 35: the launch on a phone

This is a record of what was true when Task 35 closed. Present tense here means
that day. `HANDOFF.md` is the file that describes the repo now.

**What Shawn asked for on 2026-11-15**, from an iPhone XR with Reduce Motion
on, opened from the home-screen icon. The launch was three things wrong in a
row: the startup image came up with the mark small and the page's own launch
screen then drew it slightly bigger, there was a brief white flash at the top,
and the list arrived as a hard cut. The iPad was fine. He named the three
likely causes and asked for them to be confirmed, which they were.

**The page is the whole screen** (`4f82fe7`). The status bar is
`black-translucent` and the viewport already carried `viewport-fit=cover`. An
opaque bar gives the page the area below it and leaves iOS to fit the
full-screen startup image into that smaller area, so the mark comes up smaller
in the image than the page draws it and then moves as the app takes over. That
is the first of the three, and it is why the iPad was fine: the difference is
a share of the screen the bar takes, and it is larger on a phone.

Task 34 chose the opaque bar for a reason, and the reason was real: the
screens read their safe-area insets inside the shell's iframe, where `env()`
is zero. The answer is that the insets are not theirs to read. iOS reports
them to the shell, so the shell reads the four into `--safe-top`,
`--safe-right`, `--safe-bottom` and `--safe-left` and pads `#frame` by them,
which moves all seven screens out from under the clock and the home indicator
at once and takes nothing above the 501 px breakpoint. The launch screen is
deliberately not inset: it is the drawing the startup image has to match, and
that image is drawn for the whole screen. What is asked of it instead is that
the mark and the tagline clear the insets where they sit, measured with them
forced to 64 px at the top and 48 px at the bottom on all eleven iPhone
screens and at 412 by 915.

**The startup images are now checked at every size.** Task 34 compared one,
`launch-1170x2532.png`, against a screenshot of the shell at 390 by 844. The
layout is not a share of the screen, so one screen agreeing says nothing about
the arithmetic on the other ten, and the iPhone this was found on was not the
one that was checked. All eleven are rendered at their own CSS size and pixel
ratio and measured against their own file, and all eleven agree.

**Android** was confirmed rather than changed. Chrome draws its own launch
screen from the manifest, and the three fields it reads are asserted:
`background_color` and `theme_color` are the app background, the display is
`standalone`, and the icon it centres on that background holds no white pixel
in either size. The browser suite runs the launch at 412 by 915 as well as at
the eleven iPhone sizes.

**No white** (`ef6639a`). Three things, all in markup rather than in script,
because the frames before any script has run are a state a fan can see. Every
page sets the app background on `html` and `body` in its own head in front of
every `<link>` it carries, the same bytes in all eight. Every screen says when
it has painted, with `data-painted` on its own root element two animation
frames after `DOMContentLoaded`: the first callback runs before the paint it
is scheduled for and the second after it, so the attribute means a frame has
been drawn and not that one is due. And the shell's iframe carries the same
colour on the element, because the element is painted by the shell and the
head by the screen, and stays invisible until that signal arrives. That is the
second of the three: a browser paints an empty frame white, and the launch
screen covered it only until the fade started, so the white was what the fade
uncovered.

**The crossfade** (`c5df5f6`). The mark fades out over 300 ms while the list
fades in over the same 300 ms, opacity and nothing else, and the list is
revealed in the step that starts the fade rather than before it: a list
already up behind a fading mark is a fade and not a crossfade. Ready is two
things now, `data-matches-loaded` and `data-painted`, so the list cannot be
revealed before it has painted.

**The fade is kept for a fan who asked for less motion**, which is the third
of the three and a correction to Task 34's spec rather than to its code. An
opacity fade is not motion: nothing on either screen moves, scales, slides or
spins, so the preference has nothing here to be about, and what it got instead
was a hard cut from the mark to the list, which is the one thing in the
sequence that reads as a jolt. There is no `prefers-reduced-motion` rule in
the shell and no `matchMedia` branch in its script; anything added later that
moves belongs behind that query.

**What the browser suite asks now.** The top of the screen is sampled from the
navigation to past the cap in five states, the fifth being the one the flash
was hiding in: the list's own page never answering, so nothing ever paints
inside the frame and what is left after the cap is the frame's own colour. The
sampler is itself checked against the defect forced on purpose, because a
sampler reading the wrong pixels passes everything. `data-painted` is asked of
every frame the observer recorded in which the list had any opacity at all,
not of the state it settled in. And the hold, the crossfade and the cap are
driven at all eleven iPhone screens and at an Android viewport.

**The eight failures the first full run found were the test's and not the
app's** (`cd11d33`). One assertion read the list's opacity in the frame the
mark was hidden in, and the mark is hidden by a `setTimeout` at `FADE_MS`
while the list's own transition of the same length can still be a thousandth
short of settled in that frame: 0.992923 at 412 by 915. It is waited for now,
and the crossfade itself is still asserted on the recorded timeline, which is
where that claim belongs.

**CI found what this machine could not**, and it took three runs to read it
right. The eleven comparisons screenshot the shell, and the first run failed
two of them on the Linux runner with the tagline's amber reaching 52 device
pixels further left than the generator draws it, every other edge agreeing to
within two.

The first reading was a race: the tagline is real text in a web font that
arrives after the screen does, because the markup ships visible and the mark
is inline, so a screenshot can catch the tagline before it has any ink. That
reading was right about the race and wrong about the cause. Waiting for the
font failed ten of the eleven rather than none: the wait did not create the
difference, it stopped hiding it behind a tagline that had not been drawn yet.
The weight is part of that wait, too, and the first attempt at it failed all
eleven here: `document.fonts.check` is asked whether a font matching the whole
shorthand is ready, and the 400 faces of this family stay unloaded because
nothing on this screen is set in them, so asking without the 500 waits for a
face that never arrives.

**What it is.** The browser shapes the string and the generator adds up the
font's own advances, and those agree on Windows and not on the Linux runner,
which draws the tagline about 35 CSS px wider. How wide a platform shapes a
string is not this repo's to fix and is not what a startup image has to match.
So the comparison is in two bands now, split at the top of the tagline's line
box. The mark is outlines on both sides and is compared whole in both colours.
The tagline is compared on where it sits: its top, its bottom and its centre,
each to within four device pixels, because a tagline on the wrong baseline or
off to one side is the mark moving as the app takes over, and that is what the
check exists for.

**`scripts/check_docs.py` collects `tests/browser` too**, in a second pass, so
a doc may cite a browser test by name. The two collections stay apart: the
count claims are read against the unit suite, which is what `pytest` with no
path runs.

**`scripts/smoke_live.py` opens the launch screen on the deployed site**,
which closes an open item Task 32 raised and Tasks 33 and 34 carried. The mark
is drawn, the shell says it is a web app with a translucent status bar, it
links eleven startup images, no sampled frame of the top of the screen is
white, and the list is up and holds both events once the mark is gone.

**The timing, measured in headless Chromium at 390 by 844**, as the moment the
fade began, the moment the list was revealed and the moment the screen left
the page:

| matches.json | Fade starts | List revealed | Gone |
| ------------ | ----------- | ------------- | ---- |
| answered at once | 1,502 ms | 1,502 ms | 1,815 ms |
| answered after 1.5 s | 1,588 ms | 1,588 ms | 1,902 ms |
| refused 503 | 2,214 ms | 2,214 ms | 2,514 ms |
| never answered | 2,211 ms | 2,211 ms | 2,518 ms |
| answered at once, reduced motion | 1,511 ms | 1,511 ms | 1,825 ms |

The fade and the reveal are the same number in every row, which is the
crossfade. The worst near-white share of the top band in any sampled frame was
0.0201, which is the light text in the list's own header once the list is up;
the check fails above 0.10, and the forced defect measures above 0.9.

**The evidence.** `pytest -q` reports `2106 passed`, up from `2085`; `pytest
tests/browser` reports `146 passed`, up from `100`; all five gates exit 0;
`git status` is clean after both. CI is green on the last commit of this task:
`2106 passed`, the five gates one step each, `146 passed`, and the step that
fails on a tracked file the run changed.

The smoke workflow ran against <https://sh4wnbk.github.io/prelude/> at
`061e2ee` and every check held, the launch screen's eight among them: the mark
drawn in it, the announcement, the web-app meta tags, the translucent status
bar, eleven startup images linked, the list not yet visible behind it, the
list visible and holding both events once the mark had gone, and **no white
frame in the top of the screen, worst 0.0177 of the band over 44 samples**.
That is the deployed site rather than the working tree, and it is the first
time the first frame of a visit has been checked there.

**Found, not fixed.**

- **Nothing here has run on an iPhone.** Every claim about the startup images,
  the translucent status bar and the insets is about the files, the links, the
  media queries and what Chromium does with them. Whether iOS picks the right
  one of the eleven, and whether the three things Shawn saw are gone, is a
  thing only the device shows. This is Task 34's entry, unchanged, and it is
  what he is checking next.
- **The insets are measured against a bound, not against a device.** Chromium
  reports zero for all four, so the browser suite forces 64 px and 48 px and
  measures the layout against those. They are more room than a status bar and
  a home indicator take, which makes the check conservative rather than exact:
  what it proves is that the padding is applied and that the launch block
  clears a generous inset, not that it clears any particular iPhone's.
- **The white-frame check samples, it does not watch every frame.** A sample
  is a screenshot, and `CLAUDE.md` asks the rules of every frame a
  `MutationObserver` recorded; an observer records attributes rather than
  pixels. Thirty to thirty-eight samples cover the hold, the crossfade and the
  frames after it in each state, and the frames between two samples are not
  looked at. The three things that make the claim true are in markup, which is
  why the sampling is a check on them rather than the whole of the argument.
- **The white flash was never reproduced here.** Every state the suite drives
  measures 0.0201 of the band at worst, and it measured that before this task
  as well: headless Chromium on this machine paints the empty frame the
  colour the element carries, and the iPhone did not. So the check guards the
  fix rather than having caught the defect, and the negative control is what
  says the check can see one at all.
- **Every icon in the app is still inside its control's accessible name**, and
  **the startup images are 560 KB**, and **a launch screen that is interrupted
  is not covered**, and **`prelude_launch.svg` is committed and nothing at
  runtime serves it**, and **the icon font is still 1.14 MB of the committed
  fonts**, and **the compiled stylesheet is not rebuilt by CI**, and **CI does
  not run on a schedule**, and **the smoke workflow cannot be made to fail by
  a failing deploy**. All eight are Task 34's, Task 33's and Task 32's, and
  all eight still stand.
