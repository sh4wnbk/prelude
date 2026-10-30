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

      var allegiance = Prelude.listenerFor(Prelude.matchId) || 'neutral';
      var voiceFor = match.hero && match.hero.voice_for;
      if (!voiceFor) {
        return;
      }
      var key = voiceFor[allegiance];
      var audio_map = match.hero && match.hero.audio;
      var file = audio_map && key && audio_map[key];
      if (!file) {
        return;
      }

      var audio = new Audio(file);
      playBtn.disabled = false;

      playBtn.addEventListener('click', function () {
        if (audio.paused) {
          audio.play();
          playIcon.textContent = 'pause';
        } else {
          audio.pause();
          playIcon.textContent = 'play_arrow';
        }
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
      });

      replayAction.addEventListener('click', function () {
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
