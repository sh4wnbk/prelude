# DESIGN

The design system as the four screens in `app/web/` actually define it. Every
value below is read out of the markup, not from any design brief.

**How to trace a value.** A citation is a screen, written `01` to `04` for
`prelude_01_picker.html` through `prelude_04_moments.html`. The anchor is the
backticked class string in the same table row or bullet: search the cited screen
for that string and you are at the element being described.

A citation can also be `js`, the manual ticket form. It is built in script
rather than markup so the event list and the scanner share one copy of it, and
`Prelude.mountManualEntry` is what puts it on a screen.

Citations used to carry line numbers. They were accurate when written and wrong
after the next markup change, three times over, and once a repair silently
pointed a citation at the wrong element. A class string moves with the element
it belongs to, so it cannot drift. `scripts/check_docs.py` verifies that every
anchor still appears in every screen cited beside it.

The token tables all cite `03`, meaning the `<script id="tailwind-config"`
block. That block is byte-identical across all four screens (sha256
`44927b9a0feedea2...`, 3210 chars), so the system is one system.

The block is data rather than code: it carries a `type` a browser does not
execute. `scripts/build_tailwind.py` reads it and compiles
`app/web/tailwind.css` from it, and that committed stylesheet is what the
screens link.

Anything a screen does not contain is absent here. There is no spec for states,
breakpoints, or components the screens do not have.

`prelude_05_scan.html`, the ticket scanner, and `prelude_06_ticket.html`, the
ticket details, are not covered. Both arrived after this document and carry the
same `<script id="tailwind-config"` block byte for byte, so they are built from
the system described here, but their own components (the viewfinder, the
reticle, the scan line, the ticket card and its perforation) are not documented
below.

## The mark

Settled on 2026-11-14 and drawn by `scripts/brand/build_svg.py`, which is the
one source: every brand file comes from the same numbers and the same two
fonts, and `--check` says whether what is committed is still what they draw.
`scripts/brand/README.md` carries the fonts, their licences and their
checksums.

| Piece | What it is |
| ----- | ---------- |
| the mark | "Prelude." in Syne ExtraBold, `#FFFFFF`, with the "u" redrawn as seven amber bars and the full stop amber |
| the icon | those seven bars alone, amber on `#101319`, centred and filling 56% of a square |
| the tagline | "Leave your seat. Stay in the game." in Hanken Grotesk 500, amber |

The two colours are the system's own: `#FFB703` is `primary-container` and
`#101319` is `surface`. The white is the mark's and is not a token: the
screens' off-white is `on-surface`, `#e1e2ea`, and nothing in the app draws
the mark in it. `tests/test_the_mark.py` holds all three copies of the two
colours to one another.

The glyphs are outlines rather than text everywhere the mark appears, because
an icon and a favicon are rendered where no font is loaded.

### Where each file lives

| File | What it is | What reads it |
| ---- | ---------- | ------------- |
| `app/web/assets/brand/prelude_mark.svg` | the wordmark, no background | inlined into the launch screen in `app/web/index.html` |
| `app/web/assets/brand/prelude_icon.svg` | the bars on a rounded square | copied to `app/web/assets/icon/favicon.svg` |
| `app/web/assets/brand/prelude_icon_square.svg` | the bars on a plain square | rasterised into the four PNGs |
| `app/web/assets/brand/prelude_launch.svg` | the launch screen's layout at 390 by 844 | nothing at runtime; it is what a designer opens |
| `app/web/assets/launch/launch-<w>x<h>.png` | the launch screen drawn for one iPhone screen, eleven of them | `app/web/index.html`, as an `apple-touch-startup-image` |
| `scripts/brand/fonts/Syne-wght.ttf`, `scripts/brand/fonts/HankenGrotesk-wght.ttf` | the variable fonts the mark is the outlines of | `scripts/brand/build_svg.py` |

### The icon set

`scripts/make_icons.py` writes it, from the two icon files above and nothing
else. Every screen and the shell link the first three; the manifest names the
last two.

| File | Size | Where it is shown |
| ---- | ---- | ----------------- |
| `app/web/assets/icon/favicon.svg` | vector | a browser tab, as the first `icon` |
| `app/web/assets/icon/favicon-32.png` | 32 px | a browser with no SVG icon |
| `app/web/assets/icon/apple-touch-icon-180.png` | 180 px | an iPhone home screen |
| `app/web/assets/icon/icon-192.png` | 192 px | `app/web/manifest.webmanifest`, `any` |
| `app/web/assets/icon/icon-512.png` | 512 px | `app/web/manifest.webmanifest`, `any maskable` |

### The startup images

iOS shows an `apple-touch-startup-image` while a web app opened from the home
screen is starting, before any of the app's own markup has run, and it takes
one only where the file is exactly that screen's own pixel size. So there is
one per iPhone screen in portrait, eleven files in
`app/web/assets/launch/`, each named for the pixels in it and linked by
`app/web/index.html` behind a media query naming the screen's CSS size, its
pixel ratio and portrait. The ratio is part of the query because two iPhones
share 414 by 896 at two ratios, and the wrong one of those is a quarter of the
pixels. The screens are read off Apple's point sizes and cover every iPhone
running a current iOS; `IPHONES` in `scripts/brand/build_svg.py` is the list
and names the models on each line.

| Screen | Image | Models |
| ------ | ----- | ------ |
| 375 x 667 at 2x | `launch-750x1334.png` | SE, 2nd and 3rd generation |
| 375 x 812 at 3x | `launch-1125x2436.png` | 11 Pro, 12 mini, 13 mini |
| 390 x 844 at 3x | `launch-1170x2532.png` | 12, 12 Pro, 13, 13 Pro, 14, 16e |
| 393 x 852 at 3x | `launch-1179x2556.png` | 14 Pro, 15, 15 Pro, 16 |
| 402 x 874 at 3x | `launch-1206x2622.png` | 16 Pro, 17, 17 Pro |
| 414 x 896 at 2x | `launch-828x1792.png` | XR, 11 |
| 414 x 896 at 3x | `launch-1242x2688.png` | 11 Pro Max |
| 420 x 912 at 3x | `launch-1260x2736.png` | Air |
| 428 x 926 at 3x | `launch-1284x2778.png` | 12 Pro Max, 13 Pro Max, 14 Plus |
| 430 x 932 at 3x | `launch-1290x2796.png` | 14 Pro Max, 15 Plus, 15 Pro Max, 16 Plus |
| 440 x 956 at 3x | `launch-1320x2868.png` | 16 Pro Max, 17 Pro Max |

They are drawn from the layout rather than from `prelude_launch.svg`: a
screen that is not 390 by 844 is not that file stretched, because the mark
stays 300 CSS px wide on every screen and the CSS does not scale it.
`launch_layout` in `scripts/brand/build_svg.py` is those rules as numbers and
`app/web/index.html` is the same rules in CSS, which is two copies, so
`tests/browser/test_the_launch_screen.py` screenshots the shell at 390 by 844
and measures the drawing in it against `launch-1170x2532.png`. Measured on
2026-11-15 the mark agreed to within one device pixel and the tagline to
within three.

The shell also carries `apple-mobile-web-app-capable` and
`mobile-web-app-capable`, without which iOS opens the home-screen icon inside
Safari's chrome and shows no startup image at all, and an opaque black status
bar. `black-translucent` would put the page under the status bar, and the
screens read their safe-area insets inside the shell's iframe, where `env()`
is zero and nothing would move out of the way. The manifest's
`background_color` is the same `#101319` these are drawn on, which is what
Android shows in their place.

The vector rounds its own corners and the PNGs do not, because every platform
that shows a PNG rounds or crops it and a second rounding reads as a shrunken
badge. The 512 is maskable because the bars sit inside the safe circle: the
outermost corner of the widest bar is 30% of the square from the centre,
against a safe radius of 40%.

At 32 px a bar is 1.5 px wide and a gap 1.25 px, so the reduction merges some
of them: measured on 2026-11-14 the seven come back as three runs of amber
across the middle of that bitmap. It is the fallback, and a browser that can
read the vector never sees it.

`scripts/make_icons.py --check` compares the four PNGs pixel by pixel and not
byte by byte. Pillow draws the same image on Windows and on the Linux runner
CI uses and encodes it a few bytes differently, so a byte comparison is a
claim about zlib rather than about the icon.

## Foundations

| Property | Value | Source |
| -------- | ----- | ------ |
| Mode | dark only, `darkMode: "class"`, `<html class="dark"` | `03` |
| Page background | `#101319`, set on `html,body` in `@layer base` | `03` |
| Viewport | `width=device-width, initial-scale=1.0, viewport-fit=cover` | all four, line 1 |
| Body min height | `max(884px, 100dvh)` | `01`, `03`, `04` |
| Font smoothing | `-webkit-font-smoothing: antialiased` | `03` |
| Overscroll | `overscroll-behavior: none` | `03` |
| Scrollbars | hidden, `::-webkit-scrollbar{display:none;}` | `03` |
| Safe areas | `.pt-safe` and `.pb-safe` map to `env(safe-area-inset-top,0px)` and `env(safe-area-inset-bottom,0px)` | `03` |

`prelude_02_live_seated.html` sets no body min height; the other three do.

## Color

47 color tokens are defined. 18 are referenced in markup; the remaining 29 are
declared and unused. Both lists are below, because a token that nothing uses is
not part of the working palette.

### In use

Counts are references across all four screens, in `bg-`, `text-`, `border-`,
`shadow-`, `ring-` and `fill-` utilities.

| Token | Hex | Refs |
| ----- | --- | ---: |
| `primary-container` | `#ffb703` | 134 |
| `primary` | `#ffdba0` | 52 |
| `on-surface` | `#e1e2ea` | 48 |
| `secondary` | `#bec7d2` | 42 |
| `on-surface-variant` | `#d5c4ac` | 28 |
| `surface-container-high` | `#272a30` | 28 |
| `secondary-container` | `#414a53` | 19 |
| `surface` | `#101319` | 16 |
| `surface-container` | `#1d2025` | 16 |
| `surface-container-low` | `#191c21` | 15 |
| `surface-container-highest` | `#32353b` | 14 |
| `outline-variant` | `#514532` | 13 |
| `on-primary` | `#422c00` | 12 |
| `surface-container-lowest` | `#0b0e13` | 12 |
| `outline` | `#9e8f78` | 6 |
| `on-primary-container` | `#6b4b00` | 4 |
| `surface-bright` | `#36393f` | 2 |
| `surface-variant` | `#32353b` | 2 |

All hex values come from the `tailwind-config` block in `03`.

**Surface ramp**, darkest to lightest, which is how elevation is expressed:
`surface-container-lowest #0b0e13`, `surface #101319`, `surface-container-low
#191c21`, `surface-container #1d2025`, `surface-container-high #272a30`,
`surface-container-highest #32353b`, `surface-bright #36393f`.

**Accent.** `primary-container #ffb703` is the amber action color and the single
most used token. `on-primary #422c00` is the text and icon color on top of it.
`primary #ffdba0` is the lighter amber used for text and emphasis.

`surface-variant` and `surface-container-highest` are both `#32353b`.

### Defined, not used

`background`, `error`, `error-container`, `inverse-on-surface`,
`inverse-primary`, `inverse-surface`, `on-background`, `on-error`,
`on-error-container`, `on-primary-fixed`, `on-primary-fixed-variant`,
`on-secondary`, `on-secondary-container`, `on-secondary-fixed`,
`on-secondary-fixed-variant`, `on-tertiary`, `on-tertiary-container`,
`on-tertiary-fixed`, `on-tertiary-fixed-variant`, `primary-fixed`,
`primary-fixed-dim`, `secondary-fixed`, `secondary-fixed-dim`, `surface-dim`,
`surface-tint`, `tertiary`, `tertiary-container`, `tertiary-fixed`,
`tertiary-fixed-dim`. All in the `tailwind-config` block in `03`.

The whole tertiary ramp and the whole error ramp are unused, so the screens
define no error state and no tertiary accent in practice.

## Type

Three families, served from this repo. `scripts/fetch_fonts.py` downloaded
them from Google and wrote `app/web/fonts.css`, which every screen links as
`fonts.css`; the files are in `app/web/assets/fonts/`:

| Family | Weights loaded | Used for |
| ------ | -------------- | -------- |
| Syne | 600, 700 | `display-lg`, `display-sm`, `headline-lg`, `headline-lg-mobile` |
| Hanken Grotesk | 400, 500, 600, 700 | `body-lg`, `body-md`, `headline-sm` |
| JetBrains Mono | 400, 500, 600 | `label-lg`, `label-md`, `label-sm` |

Material Symbols Outlined is the variable icon font, used in 52 places
across the four screens. Icons that read as filled set
`font-variation-settings: 'FILL' 1` inline, in `03`.

The fonts are not fetched from Google at run time.
`scripts/fetch_fonts.py` downloaded them and wrote `app/web/fonts.css`,
which every screen links; the files are in `app/web/assets/fonts/`, one per
subset, and the icon font is the variable one at axes
`wght,FILL@100..700,0..1`.

### Scale

| Token | Size | Line height | Tracking | Weight | Family |
| ----- | ---: | ----------: | -------: | -----: | ------ |
| `display-lg` | 48px | 52px | -0.03em | 700 | Syne |
| `display-sm` | 36px | 40px | -0.02em | 700 | Syne |
| `headline-lg` | 28px | 34px | -0.015em | 600 | Syne |
| `headline-lg-mobile` | 24px | 30px | -0.01em | 600 | Syne |
| `headline-sm` | 20px | 26px | -0.01em | 600 | Hanken Grotesk |
| `body-lg` | 16px | 24px | 0 | 400 | Hanken Grotesk |
| `body-md` | 14px | 20px | 0 | 400 | Hanken Grotesk |
| `label-lg` | 16px | 22px | 0.04em | 500 | JetBrains Mono |
| `label-md` | 14px | 20px | 0.06em | 500 | JetBrains Mono |
| `label-sm` | 13px | 18px | 0.08em | 600 | JetBrains Mono |

All values come from the `tailwind-config` block in `03`.

The label sizes were 9px, 11px and 13px until an iPhone XR showed the smallest
of them reading as fine print. 12/13/15 was tried first and was still tight in
the hand, so the scale sits at 13/14/16. They move together, so the order of the
scale and the gaps in it are unchanged; `label-sm` carries most of the uses, and
leaving `label-lg` behind would have put `label-md` level with it. `label-md` is
now the same size as `body-md`, which the two tell apart by family, tracking and
weight rather than by size.

Tracking is negative on display and headline sizes and positive on label sizes,
tightening as text gets larger and opening as it gets smaller. Labels are
monospace, uppercase in use, and carry the widest tracking.

Each `fontSize` token has a `fontFamily` token of the same name, so a text
element carries both, for example `font-label-sm text-label-sm` in `03`.

## Spacing

One scale, from the `tailwind-config` block in `03`, used for padding, gap and margin:

| Token | Value | | Token | Value |
| ----- | ----: | - | ----- | ----: |
| `space-2xs` | 0.25rem | | `card-padding-md` | 1.25rem |
| `space-xs` | 0.5rem | | `screen-edge-mobile` | 1.25rem |
| `space-sm` | 0.75rem | | `space-lg` | 1.5rem |
| `space-md` | 1rem | | `card-padding-lg` | 1.75rem |
| `card-padding-sm` | 1rem | | `space-xl` | 2rem |
| `touch-target-min` | 2.75rem | | `screen-edge-tablet` | 2rem |
| `space-2xl` | 3rem | | `space-3xl` | 4rem |

`space-md` and `card-padding-sm` are both 1rem; `screen-edge-mobile` and
`card-padding-md` are both 1.25rem; `space-xl` and `screen-edge-tablet` are both
2rem. `screen-edge-tablet`, `card-padding-lg` and `space-3xl` are defined but
not used in the four screens.

### Radius

`DEFAULT` 0.25rem, `lg` 0.5rem, `xl` 0.75rem, `full` 9999px (`03`). Cards use
`rounded-xl`, inner panels `rounded-lg`, pills and buttons `rounded-full`.

## Components

### App shell

Every screen is a fixed header, a scrolling `main`, and a fixed bottom nav.

- **Header**: `fixed top-0 w-full z-50 pt-safe bg-surface/85 backdrop-blur-xl
  shadow-[0_1px_8px_rgba(0,0,0,0.35)]`, inner row `h-16 px-screen-edge-mobile`.
  `01`, `02`, `03`, `04`.
- **Bottom nav**: `fixed bottom-0 w-full z-50 pb-safe bg-surface/90
  backdrop-blur-xl shadow-[0_-1px_12px_rgba(0,0,0,0.4)]`, inner row `h-16`.
  `01`, `02`, `03`, `04`.
- **Main**: `pt-16 pb-24` clears both bars. `03`, `04`.
- **Nav items**: three per screen (`LIVE`, `MOMENTS`, `PROFILE`), each
  `min-w-[44px] min-h-[44px]`, active item `text-primary-container` with
  `aria-current="page"`, inactive `text-on-surface-variant`. Same four lines.

The header is translucent at 85% and the nav at 90%, both over `backdrop-blur-xl`.

### Live status pill

`rounded-full bg-surface-container-high/80 backdrop-blur-md` with a
`w-1.5 h-1.5 rounded-full bg-primary-container pulse-live` dot and a `label-sm`
uppercase caption. Present in all four headers: `01`, `02`, `03`, `04`.

The caption names the match and says it is live, so on `01` the pill ships
with `style="display:none"` and an empty caption: the list is reached before
the fan has chosen a match, and there is none to name.

renderChip in app/web/match-content.js fills the caption and clears that
inline display once a match is chosen. The scanner screen has a header with no
pill at all, so a header without one is a shape the system already carries.

### Pulse animation

```
@keyframes pulse-amber { 0%,100% { opacity:1; transform:scale(1) }
                         50%     { opacity:0.35; transform:scale(0.85) } }
.pulse-live { animation: pulse-amber 2s cubic-bezier(0.4,0,0.6,1) infinite; }
```

`@keyframes pulse-amber` is defined in `03` and applied at 11 sites across
`01`, `02` and `03`. It is the only animation in the system; everything else is
a CSS transition.

### Card

`rounded-xl` on a surface one or two steps up from the page, with a hairline
border at low opacity and a shadow:

- `rounded-xl bg-surface-container overflow-hidden shadow-xl` with a
  `border border-surface-container-highest/30` hairline, in `03`.
- `bg-surface-container-low rounded-xl border border-surface-container-high/60`,
  three times in `04`.
- Inner panel: `rounded-xl bg-surface-container-high p-card-padding-md` with a
  `border border-surface-container-highest/40` hairline, in `03`.

Borders are always a surface token at 20 to 60 percent opacity, never a solid line.

### Buttons

| Role | Spec | Source |
| ---- | ---- | ------ |
| Primary CTA | `w-full h-touch-target-min rounded-full bg-primary-container text-on-primary-container font-label-lg text-label-lg font-bold`, `active:scale-[0.99]` | `01` |
| Primary play | `w-14 h-14 rounded-full bg-primary-container text-on-primary` with `shadow-lg shadow-primary-container/20`, `hover:scale-105 active:scale-95` | `03` |
| Primary play, waiting for the words | the same, plus `disabled:opacity-40 disabled:cursor-not-allowed` and `disabled:hover:scale-100`; it ships disabled and `match-content.js` releases it with the narration | `03` |
| Secondary play, active | `w-11 h-11 shrink-0 rounded-full bg-primary-container text-on-primary`, `active:scale-95` | `04` |
| Secondary play, idle | `w-11 h-11 shrink-0 rounded-full bg-surface-container-highest text-primary`, `hover:bg-primary-container hover:text-on-primary` | `04` |
| Secondary play, no recording | the same shapes plus `disabled:opacity-40 disabled:cursor-not-allowed`, and the idle one drops its hover with `disabled:hover:bg-surface-container-highest` | `04` |
| Tertiary action | `h-16 rounded-xl bg-surface-container hover:bg-surface-container-high`, `active:scale-98`, icon over `label-sm` caption | `03` |

Press feedback is a scale transform in every case: 0.99, 0.95 or 0.98. The
minimum touch target is 2.75rem (44px), which `touch-target-min` and the
`min-w-[44px] min-h-[44px]` nav items both honor.

A tertiary action's icon is a Material Symbol span and carries
`aria-hidden="true"`, so the name a reader hears is the caption under it. The
span holds a ligature rather than a word: without that attribute the two
buttons in the moment card's deck were named "ios_share SHARE" and "replay_10
REPLAY 10S", measured on 2026-11-15. `03`.

### Filter chips

Single row, horizontally scrollable: `overflow-x-auto pb-1 select-none no-scrollbar`.
Selected chip `rounded-full bg-surface-container-high text-primary`, unselected
`rounded-full bg-surface-container-low text-secondary`, each closing with
`border border-outline-variant/40` or `border border-transparent`. Five chips in `04`.

### Waveform

Bars, no canvas. Two variants:

- Moment card: `w-[3px]` bars, heights `h-2` to `h-9`, played bars
  `bg-primary-container`, unplayed `bg-secondary-container/70`, on a
  `bg-surface-container-lowest/60 rounded-lg` track. 24 bars, in `03`.
  Those heights are where the bars rest. While the narration plays,
  `narration-player.js` sets an inline height on each bar from a Web Audio
  analyser and clears it again on pause and at the end, so the heights are the
  voice; the two colors still follow the clock, so the amber fill is progress.
  A playhead in `03` is `w-1.5 h-7 bg-primary rounded-full` with
  `shadow-[0_0_8px_rgba(255,219,160,0.8)]`, positioned `left-[78%]` in the
  markup and from the position in the recording once the player runs.
  That track is also the scrubber, so in `03` it carries `role="slider"`,
  `tabindex="0"`, an `aria-label`, `aria-valuemin`, `aria-valuemax`,
  `aria-valuenow` and `style="touch-action: none;"`. The touch rule is written
  inline rather than as a class, and it is on this element alone: a drag on the
  bars has to reach the handlers, and nothing else may stop a scroll. No focus
  style is defined on it,
  which is the keyboard focus gap this file already records.
- Moments cards: `w-1` bars on a `rounded bg-surface-container-highest` track,
  same played and unplayed colors. `04`.

Card headers also carry a decorative bar field at `opacity-25` with
`pointer-events-none`, in `04`.

### Launch screen

The first frame of every load of the shell, in `app/web/index.html` and on no
screen. The mark, inlined from `app/web/assets/brand/prelude_mark.svg` at
300 px wide, over the tagline "Leave your seat. Stay in the game." at 16px /
20px in Hanken Grotesk 500, `primary-container`, with 20 px between them and
the pair 24 px above the middle of `surface`. Those are
`app/web/assets/brand/prelude_launch.svg`'s own numbers, read in CSS rather
than served as that file. It is one `role="img"` named "Prelude. Leave your
seat. Stay in the game.", so the mark and the tagline are one thing seen; the
inlined mark carries `aria-hidden` and no title of its own.

**The timing**, settled on 2026-11-15 and three numbers in `app/web/index.html`:

| Number | Value | What it is |
| ------ | ----- | ---------- |
| `MIN_HOLD_MS` | 1,500 ms | the hold. The mark is on screen at least this long on every full load of the root page, measured from the start of the navigation, even where matches.json was answered before the first frame |
| `FADE_MS` | 300 ms | the fade, and the `transition` on `#launch`. The two are one number |
| `CAP_MS` | 2,500 ms | the last moment a fan can see it, whatever matches.json did. The fade therefore starts a fade's length before it, at 2,200 ms |

The hold is why the numbers are three rather than two. Without one the same
screen is a flicker on a fast load and a launch screen on a slow one, which
reads as a fault rather than as the app opening. The cap is what a failed or
unanswered matches.json runs into: the list behind has its own inline copy, so
a fan who waits past the cap is waiting on a wordmark for nothing.

Under `prefers-reduced-motion: reduce` the hold is the same and there is no
fade: the screen is shown, and then it is not. A fan who asked for less motion
did not ask for less of the app's name.

Measured in headless Chromium at 390 by 844 on 2026-11-15, as the moment the
fade began and the moment the screen left the page:

| matches.json | Fade starts | Gone |
| ------------ | ----------- | ---- |
| answered at once | 1,507 ms | 1,809 ms |
| answered after 1.5 s | 1,589 ms | 1,891 ms |
| refused 503 | 2,209 ms | 2,510 ms |
| answered at once, reduced motion | no fade | 1,507 ms |

The 2,510 ms is the cap plus the browser's own timer slack: a `setTimeout` is
a floor and not a ceiling, so 10 ms is what nothing in the page can take off.
`tests/browser/test_the_launch_screen.py` asks these of every frame a
`MutationObserver` recorded rather than of the state the screen settled in.

The mark is inline rather than fetched because the first frame is before any
request of its own could have been answered. `tests/test_screen_copy.py` holds
the inlined paths to the brand file character for character, so the two cannot
drift.

### Verified marker

`rounded-lg bg-surface-container-lowest` holding a filled `verified` Material
Symbol at `text-[16px] text-primary-container` and a `label-sm text-secondary`
caption reading "Verified from play data". `03`.

It ships with `display:none`, as does the narration paragraph above it and the
claim count below it: a `label-sm text-outline` line reading "<n> claims
checked against the play data", where the number is the one the grounding
check recorded for this slot. `match-content.js` shows the three together once
the frozen narration for the match and the slot on screen is in the paragraph.
Their block keeps `min-height:19.5rem` meanwhile, so the player below does not
move.

### Text input

`w-full bg-surface-container px-3 py-1.5 rounded text-[16px] text-on-surface
border border-outline-variant/30`, with the only real focus treatment in the
system: `focus:outline-none focus:border-primary-container`, so the border
changes color rather than gaining a ring. The size is the one literal value in
the system rather than a token: iOS zooms the page when a field under 16px takes
focus, and the screens no longer block zooming, so 16px is what stops that. Three instances, built by `js`: the
section, row and seat of a ticket entered by hand. Each carries a `placeholder`
and a `<label>` bound to it by `for`. They are mounted on the event list and on
the scanner, from that one definition.

### Select

The same field classes as the text input, `bg-surface-container px-3 py-1.5
rounded`, on the match select built by `js`. It is the only select in the system
and takes the forms plugin's own chevron rather than a drawn one.

### Toggle switch

`h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent bg-primary-container` with
`role="switch"`, `aria-checked="true"`, `aria-label`, and an `sr-only` caption.
The knob is `translate-x-5 inline-block h-5 w-5 transform rounded-full bg-on-primary`, moved by
`transition duration-200 ease-in-out`. `04`. Only the checked
appearance exists; the unchecked colors are not defined anywhere.

### Credit footer

Text credit plus the reversed Hudl StatsBomb logo:

- Picker: `Powered by StatsBomb play-by-play data` in `body-md text-secondary`,
  logo at `h-4 w-auto ml-auto` (105px by 16px). `01`.
- Moments: `Data: StatsBomb` in `text-label-sm text-secondary tracking-wider uppercase`, logo at
  `h-3 w-auto` (79px by 12px). `04`.

Both sit on a `bg-surface-container-lowest` panel with a
`border-outline-variant/20` hairline, which is the quietest surface in the ramp
and the reason the two credits read as the same component. The Moments footer
reached that shape late: it was on `surface-container-high` with the credit
nested in a column that also held the callout and competed with the auto-save
control, so at 390px the callout broke to three lines and the credit wrapped
mid-word. It is now two rows, the callout across the full width and the credit
beside the control on a line of their own.

Logo file `app/web/assets/hudl-statsbomb-logo-reversed.png`, 2258 by 344, so
6.56:1.

## Phone frame, wide viewports

The four screens are laid out for a 390 by 844 phone and use no breakpoint
utilities, so on a desktop window they stretch and misread. `app/web/phone-frame.css`
puts a screen inside a generic bezel at its real size above a breakpoint. It is
presentation only: no app layout, copy or component is involved, and it is
built entirely from `body` and `body > main`, which every screen already has.

| Property | Value | Token? |
| -------- | ----- | ------ |
| Breakpoint | `min-width: 501px` | no, chrome only |
| Screen area | 390 by 844 | the viewport the screens are built for |
| Bezel thickness | 16px | no |
| Bezel radius | 48px | no |
| Bezel colour | `#32353b` | yes, `surface-container-highest` |
| Page behind the frame | `#0b0e13` | yes, `surface-container-lowest` |
| Drop shadow | `0 24px 64px rgba(0,0,0,0.55)` | no |

The bezel thickness and radius are not in the token scale and could not be: the
largest non-pill radius token is `xl` at 0.75rem, which is a card corner, not a
device corner. They are frame chrome and are deliberately outside the system.
The two colours are tokens.

**Why `body` carries a transform.** The header and the bottom nav are
`position: fixed`, so by default they pin to the window and would sit outside
the bezel. A transformed ancestor becomes the containing block for fixed
descendants, so `transform: translateZ(0)` on `body` lands both bars inside the
frame. That has a consequence: `body` must stop scrolling (`overflow: hidden`)
and `main` must start (`overflow-y: auto`), otherwise the bars scroll away with
the content. `body` also switches to `box-sizing: content-box` so its width and
height describe the screen area rather than the screen plus bezel.

**At 500px and narrower nothing applies.** The rules live entirely inside the
media query, so the app fills the window exactly as it did before.

**`app/web/index.html` draws the same bezel itself.** It is the entry point and
holds every screen in one iframe, so the frame is built once and navigating
does not rebuild it. Inside that shell the iframe is 390px wide, below the
501px breakpoint, so `phone-frame.css` stays inert and the two never both
apply. The stylesheet still matters when a screen is opened directly.

**Above the breakpoint the page carries a stadium photograph**,
`assets/stadium-bg.jpg`, a match night seen from behind one goal: four
floodlight towers, a full crowd and players on the pitch. It is at `cover` and
centred, blurred 8px on `html::before` and dimmed by `html::after` at `#101319`
50%. The blur sits on a pseudo-element so the phone itself stays sharp, and the
dim keeps the phone the brightest thing on screen. Measure that by peak and not
by mean: the backdrop tops out at 131 at every width while the phone's amber
button reaches 227. Their mean luminances are a wash, close enough that which
one comes out ahead depends on where the crop is drawn, so the mean says
nothing. The phone is a dark panel with bright accents, and it is the only sharp
thing on a blurred page. Both rules live inside the media query, so a phone
never applies them and never downloads the image, which was measured as zero
requests at 390px against one at 1920px. The file is 1920px wide at JPEG quality
75, 122KB, which is what a backdrop that is blurred and dimmed needs.

Because the shell draws its own bezel it also carries its own copy of these
rules. `body` there is a full-viewport flex container, and the base layer paints
it `#101319`, which covered the backdrop entirely until `body` was made
transparent above the breakpoint. Anything added to one of the two frames has to
be added to the other.

Measured in both states, on all four screens:

| | 390px viewport | 1440px viewport |
| --- | --- | --- |
| Bezel | none, `border: 0px` | `16px`, radius `48px` |
| Screen area | fills the window, 390 wide | 390 by 844 |
| Frame position | n/a | `left: 509`, centered |
| Header | 390 wide at x=0 | 390 wide at x=525, inside the bezel |
| Bottom nav | at the window bottom | inside the frame, bottom 892 of a 900 window |
| Scrolling | the window scrolls | `main` scrolls, `overflow-y: auto` |
| Horizontal overflow | none | none |

## What the screens do not define

Not present anywhere in the four files, so not specified: light mode, disabled
states, error or empty states, toasts, modals, form validation, and the
unchecked state of the toggle switch.

Focus is defined only on the text input and the select (`js`). Every button in
the system relies on `active:` scale and `hover:` color, with no focus style at all, and
the toggle at `04` sets `focus:outline-none` without a replacement, so it
has no visible keyboard focus.

No breakpoint utilities are used: zero occurrences of `sm:`, `md:`, `lg:`,
`xl:` or `2xl:` across the four screens, and `screen-edge-tablet` is defined but
never applied. The layouts are mobile width only. The only media queries in
the repo are the phone frame above and the matching one in `index.html`, which
wrap the app rather than reflow it.

`pulse-amber` is the only `@keyframes` block, declared once per screen.
Everything else that moves is a CSS transition or a transform on `:hover` and
`:active`.
