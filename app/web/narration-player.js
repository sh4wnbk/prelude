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
      playBtn.disabled = false;

      // The waveform follows the voice through a Web Audio analyser. All of it
      // is optional: with no AudioContext, or if any of the wiring throws, the
      // bars keep the fixed heights the markup gives them and the amber fill
      // still shows progress, with the narration still playing.
      var REST_MIN_PX = 6;
      var REST_MAX_PX = 36;
      var audioCtx = null;
      var analyser = null;
      var sourceNode = null;
      var levels = null;
      var frame = 0;
      var webAudioOff = false;

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
        // resumes one only on a user gesture. One context and one source node
        // per element for the life of the page, so replay reuses them; a
        // second createMediaElementSource on the same element throws and takes
        // the sound with it.
        claimPlaybackSession();
        if (audioCtx || webAudioOff) {
          if (audioCtx && audioCtx.state === 'suspended') {
            audioCtx.resume();
          }
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
          if (ctx.state === 'suspended') {
            ctx.resume();
          }
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

      playBtn.addEventListener('click', function () {
        if (audio.paused) {
          openAnalyser();
          audio.play();
          playIcon.textContent = 'pause';
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

      audio.addEventListener('timeupdate', function () {
        var duration = audio.duration;
        var current = audio.currentTime;
        if (!duration || duration === 0) {
          return;
        }
        var fraction = current / duration;
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
        var elapsed = Math.floor(current);
        var m = Math.floor(elapsed / 60);
        var s = elapsed % 60;
        timerReadout.textContent = m + ':' + (s < 10 ? '0' : '') + s;
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

      scrubTrack.addEventListener('click', function (e) {
        var rect = scrubTrack.getBoundingClientRect();
        var fraction = (e.clientX - rect.left) / rect.width;
        fraction = Math.max(0, Math.min(1, fraction));
        if (audio.duration) {
          audio.currentTime = fraction * audio.duration;
        }
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }
})();
