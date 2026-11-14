/* The narration recordings, on the two screens that play one.
 *
 * There is one player, `wirePlayer` below, and both screens use it. It owns
 * everything about playing a recording: the tap, the Web Audio analyser the
 * bars follow, the amber fill, the clock, the scrubber and the arrow keys.
 * What the two screens differ in is the markup it is handed and when the
 * button may be pressed, and both of those are arguments.
 *
 * The moment card is the whole of it: a play button, a clock, a waveform with
 * a playhead and Replay 10s. `start()` finds that markup, works out which
 * recording this fan hears, and hands it over. Its button waits for the words
 * it reads, so the reveal in `app/web/match-content.js` is what releases it.
 *
 * The Moments list is one card with a recording and the rest without. Those
 * cards are built by `match-content.js`, which owns that markup and holds the
 * one slot lookup, so it works out which card has a recording and hands that
 * card's button, bars and clock over through `Prelude.onMomentPlay`. Only the
 * hero goal has one, and it is the file the moment card plays for this fan, so
 * the two screens play the same recording and there is one lookup and one
 * player between them. A card with no recording is left exactly as the markup
 * ships it: the button disabled, the bars at their fixed heights, no slider
 * and nothing to focus.
 */
(function () {
  //: Each arrow key moves the position by this many seconds.
  var ARROW_SECONDS = 5;

  /* One recording, and every control that reads or moves it.
   *
   * opts:
   *   file         the recording to play
   *   playBtn      the play and pause button
   *   playIcon     the element whose text is the icon ligature
   *   bars         the waveform bars, in order
   *   track        the element a drag scrubs on, and the bars' own box
   *   playedClass  the class a bar behind the playhead carries
   *   restClass    the class a bar ahead of it carries
   *   restMinPx    the bar height at silence, and at the loudest moment
   *   restMaxPx
   *   whenReady    called with a function to run when the button may be
   *                pressed; the two screens answer this differently
   *   clock        optional, the elapsed time readout
   *   playhead     optional, the line that follows the position
   *   replay       optional, the Replay 10s button
   */
  function wirePlayer(opts) {
    var playBtn = opts.playBtn;
    var playIcon = opts.playIcon;
    var bars = opts.bars;
    var track = opts.track;
    var clock = opts.clock || null;
    var playhead = opts.playhead || null;
    var replay = opts.replay || null;
    var PLAYED = opts.playedClass;
    var REST = opts.restClass;
    var REST_MIN_PX = opts.restMinPx;
    var REST_MAX_PX = opts.restMaxPx;

    var audio = new Audio(opts.file);

    // The waveform follows the voice through a Web Audio analyser. All of it
    // is optional: with no AudioContext, or if any of the wiring throws, the
    // bars keep the fixed heights the markup gives them and the amber fill
    // still shows progress, with the narration still playing.
    var audioCtx = null;
    var analyser = null;
    var sourceNode = null;
    var levels = null;
    var frame = 0;
    var webAudioOff = false;
    // The first play starts at the opening word, unless the fan has moved
    // the playhead themselves before taking it.
    var firstPlay = true;
    var playheadMoved = false;
    // The pointer that owns the drag, or null when nothing is dragging.
    var scrubPointer = null;

    function claimPlaybackSession() {
      // iOS silences a page under the silent switch unless the page says its
      // audio is playback rather than ambient.
      try {
        if (navigator.audioSession) {
          navigator.audioSession.type = 'playback';
        }
      } catch (err) {
        // An engine may expose the object and refuse the write.
      }
    }

    function openAnalyser() {
      // Called from inside the tap: iOS starts every context suspended and
      // resumes one only on a user gesture, which resumeContext asks for
      // straight after this. One context and one source node per element
      // for the life of the page, so replay reuses them; a second
      // createMediaElementSource on the same element throws and takes the
      // sound with it.
      claimPlaybackSession();
      if (audioCtx || webAudioOff) {
        return;
      }
      var Ctx = window.AudioContext || window.webkitAudioContext;
      if (!Ctx) {
        webAudioOff = true;
        return;
      }
      var ctx = null;
      var src = null;
      try {
        ctx = new Ctx();
        src = ctx.createMediaElementSource(audio);
        var node = ctx.createAnalyser();
        node.fftSize = 128;
        node.smoothingTimeConstant = 0.6;
        // Through the analyser and on to the speakers. Without the second
        // connect the element's sound stops inside the graph.
        src.connect(node);
        node.connect(ctx.destination);
        audioCtx = ctx;
        sourceNode = src;
        analyser = node;
        levels = new Uint8Array(node.frequencyBinCount);
      } catch (err) {
        webAudioOff = true;
        analyser = null;
        levels = null;
        if (src) {
          // The element is already inside the graph, so send it straight to
          // the speakers or the narration would be silent.
          try {
            src.connect(ctx.destination);
          } catch (err2) {
            // Nothing further to try; the element keeps its own output.
          }
          audioCtx = ctx;
          sourceNode = src;
        }
      }
    }

    function resumeContext() {
      // Answers with a promise that settles once the context is running.
      // The tap waits for it before play(), because the element's clock
      // starts whether or not the graph is running: a suspended context is
      // what iOS hands back, and the opening word goes into it and is lost.
      // resume() answers with a promise in a current engine and with
      // nothing in an older one, and both are waited on the same way.
      if (!audioCtx || audioCtx.state !== 'suspended') {
        return Promise.resolve();
      }
      try {
        var resuming = audioCtx.resume();
        return resuming && typeof resuming.then === 'function'
          ? resuming
          : Promise.resolve();
      } catch (err) {
        return Promise.resolve();
      }
    }

    function drawLevels() {
      if (!analyser || audio.paused) {
        frame = 0;
        return;
      }
      analyser.getByteFrequencyData(levels);
      // A voice puts its energy in the low bins, so the bars read the bottom
      // half of the spectrum spread across them.
      var span = Math.max(1, Math.floor(levels.length / 2));
      var per = span / bars.length;
      for (var i = 0; i < bars.length; i++) {
        var from = Math.floor(i * per);
        var to = Math.max(from + 1, Math.floor((i + 1) * per));
        var total = 0;
        for (var b = from; b < to; b++) {
          total += levels[b];
        }
        var level = total / (to - from) / 255;
        bars[i].style.height =
          (REST_MIN_PX + (REST_MAX_PX - REST_MIN_PX) * level).toFixed(1) + 'px';
      }
      frame = window.requestAnimationFrame(drawLevels);
    }

    function restBars() {
      if (frame) {
        window.cancelAnimationFrame(frame);
        frame = 0;
      }
      // Clearing the override hands each bar back to the height its class
      // sets, which is where it rests.
      bars.forEach(function (bar) {
        bar.style.height = '';
      });
    }

    function paintProgress(fraction) {
      // The amber fill and the playhead, from a position rather than from
      // the clock, so a drag shows where the finger is whether the recording
      // is playing or paused. Classes and `left` only: the bar heights are
      // inline styles and belong to the analyser, so progress and voice
      // still do not meet.
      var filled = Math.round(bars.length * fraction);
      bars.forEach(function (bar, idx) {
        if (idx < filled) {
          bar.classList.add(PLAYED);
          bar.classList.remove(REST);
        } else {
          bar.classList.remove(PLAYED);
          bar.classList.add(REST);
        }
      });
      if (playhead) {
        playhead.style.left = (fraction * 100) + '%';
      }
    }

    function paintClock(seconds) {
      var elapsed = Math.floor(seconds);
      var m = Math.floor(elapsed / 60);
      var s = elapsed % 60;
      if (clock) {
        clock.textContent = m + ':' + (s < 10 ? '0' : '') + s;
      }
      track.setAttribute('aria-valuenow', seconds.toFixed(1));
    }

    function playLength() {
      // 0 while the length is unknown, which covers every state a scrub has
      // nothing to seek within: no metadata yet, or no length at all.
      var total = audio.duration;
      return total && isFinite(total) && total > 0 ? total : 0;
    }

    function paintRange() {
      var total = playLength();
      if (total) {
        track.setAttribute('aria-valuemax', total.toFixed(1));
      }
    }

    function seekToFraction(fraction) {
      // The position under the finger, as a fraction of the track's width,
      // is the position in the recording, clamped to the start and the end.
      // Playing stays playing and paused stays paused: nothing here calls
      // play() or pause().
      var total = playLength();
      if (!total) {
        return;
      }
      var at = Math.max(0, Math.min(1, fraction));
      playheadMoved = true;
      audio.currentTime = at * total;
      paintProgress(at);
      paintClock(audio.currentTime);
    }

    function fractionAtX(clientX) {
      var rect = track.getBoundingClientRect();
      if (!rect.width) {
        return 0;
      }
      return Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
    }

    // Zero progress before anything is pressed, and the button offered only
    // when the caller says so: the moment card's words arrive on a second
    // fetch and the button waits for them, and a Moments card is ready as
    // soon as it has been handed a file.
    paintProgress(0);
    opts.whenReady(function () {
      playBtn.disabled = false;
    });

    playBtn.addEventListener('click', async function () {
      if (audio.paused) {
        openAnalyser();
        // The context has to be running before play(), or the opening word
        // is lost. resume() is asked for inside the tap and waited on here,
        // and play() is the first thing after it.
        await resumeContext();
        if (firstPlay && !playheadMoved) {
          audio.currentTime = 0;
        }
        firstPlay = false;
        playIcon.textContent = 'pause';
        var playing = audio.play();
        if (playing && playing.catch) {
          playing.catch(function () {
            // Refused, so the icon must not claim it is playing.
            playIcon.textContent = 'play_arrow';
          });
        }
      } else {
        audio.pause();
        playIcon.textContent = 'play_arrow';
      }
    });

    audio.addEventListener('play', function () {
      if (analyser && !frame) {
        frame = window.requestAnimationFrame(drawLevels);
      }
    });

    audio.addEventListener('pause', function () {
      restBars();
    });

    audio.addEventListener('loadedmetadata', paintRange);
    audio.addEventListener('durationchange', paintRange);
    paintRange();

    audio.addEventListener('timeupdate', function () {
      var total = playLength();
      if (!total) {
        return;
      }
      paintProgress(audio.currentTime / total);
      paintClock(audio.currentTime);
    });

    audio.addEventListener('ended', function () {
      playIcon.textContent = 'play_arrow';
      restBars();
    });

    if (replay) {
      replay.addEventListener('click', function () {
        openAnalyser();
        audio.currentTime = Math.max(0, audio.currentTime - 10);
        audio.play();
        playIcon.textContent = 'pause';
      });
    }

    track.addEventListener('pointerdown', function (e) {
      // Pointer events are one path for touch and for mouse. The capture
      // keeps the moves coming to the track once the finger has left it, so
      // a drag that strays above or below the bars still scrubs.
      scrubPointer = e.pointerId;
      if (track.setPointerCapture) {
        try {
          track.setPointerCapture(e.pointerId);
        } catch (err) {
          // An engine may refuse the capture; the drag then ends at the edge.
        }
      }
      // A drag on the waveform scrubs rather than scrolling or selecting.
      e.preventDefault();
      track.focus();
      seekToFraction(fractionAtX(e.clientX));
    });

    track.addEventListener('pointermove', function (e) {
      if (scrubPointer === null || e.pointerId !== scrubPointer) {
        return;
      }
      e.preventDefault();
      seekToFraction(fractionAtX(e.clientX));
    });

    function endScrub(e, seek) {
      if (scrubPointer === null || e.pointerId !== scrubPointer) {
        return;
      }
      if (seek) {
        seekToFraction(fractionAtX(e.clientX));
      }
      scrubPointer = null;
      if (track.releasePointerCapture) {
        try {
          track.releasePointerCapture(e.pointerId);
        } catch (err) {
          // Already released, which is the outcome either way.
        }
      }
    }

    track.addEventListener('pointerup', function (e) {
      endScrub(e, true);
    });

    track.addEventListener('pointercancel', function (e) {
      // The gesture was taken over rather than finished, so the position it
      // reached stands and nothing moves again.
      endScrub(e, false);
    });

    track.addEventListener('keydown', function (e) {
      var step = 0;
      if (e.key === 'ArrowRight') {
        step = ARROW_SECONDS;
      } else if (e.key === 'ArrowLeft') {
        step = -ARROW_SECONDS;
      } else {
        return;
      }
      var total = playLength();
      if (!total) {
        return;
      }
      e.preventDefault();
      seekToFraction((audio.currentTime + step) / total);
    });
  }

  // --- the Moments list ----------------------------------------------------

  // One Moments card, handed over with the file it plays and the markup it
  // plays it through. `match-content.js` leaves every one of those buttons
  // disabled and only a button something takes is offered, so a card with no
  // recording keeps its fixed bars and a screen the player is not loaded on
  // offers nothing.
  //
  // The bars are a scrubber here as well as on the moment card, so the track
  // becomes a slider when it is taken. It is not one in the markup: a card
  // with no recording would then be focusable and announced as a control with
  // nothing to control.
  function playOnly(button, icon, file, track, clock) {
    button.disabled = true;
    if (!track) {
      return;
    }
    track.setAttribute('role', 'slider');
    track.setAttribute('tabindex', '0');
    track.setAttribute('aria-label', 'Narration position in seconds');
    track.setAttribute('aria-valuemin', '0');
    track.setAttribute('aria-valuemax', '0');
    track.setAttribute('aria-valuenow', '0');
    track.classList.add('cursor-pointer', 'select-none');
    track.style.touchAction = 'none';
    wirePlayer({
      file: file,
      playBtn: button,
      playIcon: icon,
      bars: Array.prototype.slice.call(track.querySelectorAll('div.w-1')),
      track: track,
      clock: clock || null,
      playedClass: 'bg-primary-container',
      restClass: 'bg-secondary-container',
      // The track is h-6 with py-1, so sixteen pixels of room.
      restMinPx: 3,
      restMaxPx: 16,
      // The card is ready as soon as it has a file: the words it is about are
      // the card's own title and body, which are already on screen.
      whenReady: function (release) { release(); }
    });
  }

  if (window.Prelude && Prelude.onMomentPlay) {
    // Registered now, in the head, because match-content.js hands the cards
    // over as it builds them and that happens as soon as matches.json lands.
    Prelude.onMomentPlay(playOnly);
  }

  // --- the moment card -----------------------------------------------------

  function start() {
    var playBtn = document.getElementById('playBtn');
    var playIcon = document.getElementById('playIcon');
    var timerReadout = document.getElementById('timerReadout');
    var scrubTrack = document.getElementById('scrubTrack');
    var replayAction = document.getElementById('replayAction');

    if (!playBtn || !playIcon || !timerReadout || !scrubTrack || !replayAction) {
      return;
    }

    var bars = Array.from(scrubTrack.querySelectorAll('div.w-\\[3px\\]'));
    var playhead = scrubTrack.querySelector('.absolute');

    // Show zero progress at once, before matches.json has been answered.
    bars.forEach(function (bar) {
      bar.classList.remove('bg-primary-container');
      bar.classList.add('bg-secondary-container/70');
    });
    if (playhead) {
      playhead.style.left = '0%';
    }
    playBtn.disabled = true;

    // whenMatches hands over the whole matches.json document, or null when it
    // could not be fetched; the list is its `matches` field.
    Prelude.whenMatches(function (doc) {
      if (!doc) {
        return;
      }
      var matches = doc.matches;
      var match = null;
      for (var i = 0; i < matches.length; i++) {
        if (matches[i].match_id === Prelude.matchId) {
          match = matches[i];
          break;
        }
      }
      if (!match) {
        return;
      }

      var key = Prelude.slotFor(match);
      var audio_map = match.hero && match.hero.audio;
      var file = audio_map && key && audio_map[key];
      if (!file) {
        return;
      }

      wirePlayer({
        file: file,
        playBtn: playBtn,
        playIcon: playIcon,
        bars: bars,
        track: scrubTrack,
        clock: timerReadout,
        playhead: playhead,
        replay: replayAction,
        playedClass: 'bg-primary-container',
        restClass: 'bg-secondary-container/70',
        restMinPx: 6,
        restMaxPx: 36,
        // The recording exists, so the button can be offered; it is not
        // offered yet. The card's words and the voice reading them are one
        // piece of writing, and the words arrive on a second fetch. Until
        // match-content.js has put the frozen narration for this match and
        // this slot on the card, there is nothing on screen for the voice to
        // be about, so the button stays disabled and whenNarrationShown is
        // what lifts it, in the same step that reveals the words and the
        // label. A narrations.json that fails never calls back, and the
        // button stays disabled for the life of the page.
        whenReady: Prelude.whenNarrationShown
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }
})();
