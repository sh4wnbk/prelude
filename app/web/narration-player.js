(function () {
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

    // Show zero progress at once.
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

      var audio = new Audio(file);

      // The recording exists, so the button can be offered; it is not offered
      // yet. The card's words and the voice reading them are one piece of
      // writing, and the words arrive on a second fetch. Until
      // match-content.js has put the frozen narration for this match and this
      // slot on the card, there is nothing on screen for the voice to be
      // about, so the button stays disabled and whenNarrationShown is what
      // lifts it, in the same step that reveals the words and the label. A
      // narrations.json that fails never calls back, and the button stays
      // disabled for the life of the page.
      Prelude.whenNarrationShown(function () {
        playBtn.disabled = false;
      });

      // The waveform follows the voice through a Web Audio analyser. All of it
      // is optional: with no AudioContext, or if any of the wiring throws, the
      // bars keep the fixed heights the markup gives them and the amber fill
      // still shows progress, with the narration still playing.
      var REST_MIN_PX = 6;
      var REST_MAX_PX = 36;
      // Each arrow key moves the position by this many seconds.
      var ARROW_SECONDS = 5;
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
            bar.classList.add('bg-primary-container');
            bar.classList.remove('bg-secondary-container/70');
          } else {
            bar.classList.remove('bg-primary-container');
            bar.classList.add('bg-secondary-container/70');
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
        timerReadout.textContent = m + ':' + (s < 10 ? '0' : '') + s;
        scrubTrack.setAttribute('aria-valuenow', seconds.toFixed(1));
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
          scrubTrack.setAttribute('aria-valuemax', total.toFixed(1));
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
        var rect = scrubTrack.getBoundingClientRect();
        if (!rect.width) {
          return 0;
        }
        return Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
      }

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

      replayAction.addEventListener('click', function () {
        openAnalyser();
        audio.currentTime = Math.max(0, audio.currentTime - 10);
        audio.play();
        playIcon.textContent = 'pause';
      });

      scrubTrack.addEventListener('pointerdown', function (e) {
        // Pointer events are one path for touch and for mouse. The capture
        // keeps the moves coming to the track once the finger has left it, so
        // a drag that strays above or below the bars still scrubs.
        scrubPointer = e.pointerId;
        if (scrubTrack.setPointerCapture) {
          try {
            scrubTrack.setPointerCapture(e.pointerId);
          } catch (err) {
            // An engine may refuse the capture; the drag then ends at the edge.
          }
        }
        // A drag on the waveform scrubs rather than scrolling or selecting.
        e.preventDefault();
        scrubTrack.focus();
        seekToFraction(fractionAtX(e.clientX));
      });

      scrubTrack.addEventListener('pointermove', function (e) {
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
        if (scrubTrack.releasePointerCapture) {
          try {
            scrubTrack.releasePointerCapture(e.pointerId);
          } catch (err) {
            // Already released, which is the outcome either way.
          }
        }
      }

      scrubTrack.addEventListener('pointerup', function (e) {
        endScrub(e, true);
      });

      scrubTrack.addEventListener('pointercancel', function (e) {
        // The gesture was taken over rather than finished, so the position it
        // reached stands and nothing moves again.
        endScrub(e, false);
      });

      scrubTrack.addEventListener('keydown', function (e) {
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
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }
})();
