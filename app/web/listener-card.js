/* "Who are you with" card, shown once per match on the Live screen.
 *
 * If the fan has not yet chosen an allegiance for this match, a full-screen
 * overlay appears with one card: the question, three choice buttons, an
 * optional name field, and a Continue button. The answer stays in
 * sessionStorage only; nothing is sent anywhere.
 *
 * docs/bob_brief.md carries the brief as Task 9.
 */
(function () {
  "use strict";

  function asked() {
    return window.location.search.indexOf("ask") >= 0;
  }

  // One unbroken literal on purpose. docs/DESIGN.md quotes this class string
  // and scripts/check_docs.py looks for it in manual-entry.js.
  var FIELD = "w-full bg-surface-container px-3 py-1.5 rounded text-[16px] text-on-surface border border-outline-variant/30 focus:outline-none focus:border-primary-container";
  var LABEL = "font-label-sm text-label-sm text-outline uppercase";

  function markup(match) {
    var greeting = (match.hero && match.hero.opening && match.hero.opening.greeting) || "";
    var home = match.home_team;
    var away = match.away_team;
    return '<div class="flex flex-col gap-space-md">' +
             '<p class="font-headline-sm text-headline-sm text-on-surface font-bold">' +
               'Who are you with ' + greeting + '?' +
             '</p>' +
             '<div class="flex flex-col gap-2" id="listener-choices">' +
               '<button aria-pressed="false" class="w-full py-3 px-4 rounded-xl bg-surface-container-highest ' +
                 'text-on-surface font-label-lg text-label-lg text-left transition-colors" ' +
                 'data-value="team_a" type="button">' + home + '</button>' +
               '<button aria-pressed="false" class="w-full py-3 px-4 rounded-xl bg-surface-container-highest ' +
                 'text-on-surface font-label-lg text-label-lg text-left transition-colors" ' +
                 'data-value="team_b" type="button">' + away + '</button>' +
               '<button aria-pressed="false" class="w-full py-3 px-4 rounded-xl bg-surface-container-highest ' +
                 'text-on-surface font-label-lg text-label-lg text-left transition-colors" ' +
                 'data-value="neutral" type="button">Just here for the game</button>' +
             '</div>' +
             '<div class="flex flex-col gap-1">' +
               '<label class="' + LABEL + '" for="listener-call">What should we call you?</label>' +
               '<input autocomplete="off" class="' + FIELD + '" id="listener-call" ' +
                 'placeholder="Optional" type="text">' +
             '</div>' +
             '<button class="mt-1 w-full h-touch-target-min rounded-full bg-primary-container ' +
               'text-on-primary-container font-label-lg text-label-lg font-bold tracking-wider ' +
               'uppercase flex items-center justify-center transition-opacity ' +
               'disabled:opacity-40 disabled:cursor-not-allowed" disabled id="listener-continue" ' +
               'type="button">Continue</button>' +
           '</div>';
  }

  function mount(match) {
    var overlay = document.createElement("div");
    overlay.className = "fixed inset-0 z-50 bg-surface flex items-center justify-center px-screen-edge-mobile";

    var card = document.createElement("div");
    card.className = "w-full bg-surface-container rounded-xl p-card-padding-md flex flex-col gap-space-md shadow-lg";
    card.innerHTML = markup(match);

    overlay.appendChild(card);
    document.body.appendChild(overlay);

    var choices = card.querySelectorAll("#listener-choices button");
    var callField = card.querySelector("#listener-call");
    var continueBtn = card.querySelector("#listener-continue");

    callField.value = Prelude.nameFor() || "";

    function pickChoice(chosen) {
      for (var i = 0; i < choices.length; i++) {
        var selected = choices[i] === chosen;
        choices[i].setAttribute("aria-pressed", String(selected));
        // Selected is amber with the dark text the Continue button uses, so
        // the name stays readable; unselected sits one step above the card.
        if (selected) {
          choices[i].classList.remove("bg-surface-container-highest", "text-on-surface");
          choices[i].classList.add("bg-primary-container", "text-on-primary-container");
        } else {
          choices[i].classList.remove("bg-primary-container", "text-on-primary-container");
          choices[i].classList.add("bg-surface-container-highest", "text-on-surface");
        }
      }
      continueBtn.disabled = false;
    }

    for (var j = 0; j < choices.length; j++) {
      choices[j].addEventListener("click", (function (btn) {
        return function () { pickChoice(btn); };
      })(choices[j]));
    }

    // If the card is reopened with an existing answer, pre-select that choice
    // so Continue is immediately enabled, and keep the name in the field.
    var stored = Prelude.listenerFor(Prelude.matchId);
    if (stored) {
      for (var k = 0; k < choices.length; k++) {
        if (choices[k].getAttribute("data-value") === stored) {
          pickChoice(choices[k]);
          break;
        }
      }
    }

    continueBtn.addEventListener("click", function () {
      var chosen = card.querySelector('#listener-choices button[aria-pressed="true"]');
      if (!chosen) return;
      Prelude.setListener(Prelude.matchId, chosen.getAttribute("data-value"));
      Prelude.setName(callField.value);
      overlay.parentNode.removeChild(overlay);
      if (asked()) {
        window.history.replaceState(null, "", Prelude.url("prelude_02_live_seated.html"));
      }
    });
  }

  Prelude.whenMatches(function (doc) {
    if (!doc) return;
    var match = null;
    for (var i = 0; i < doc.matches.length; i++) {
      if (doc.matches[i].match_id === Prelude.matchId) { match = doc.matches[i]; break; }
    }
    if (!match) return;
    if (Prelude.listenerFor(Prelude.matchId) !== null && !asked()) return;
    mount(match);
  });
})();
