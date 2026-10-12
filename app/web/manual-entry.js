/* The one manual ticket entry, mounted on the event list and on the scanner.
 *
 * Both screens need the same thing: pick the match from matches.json so the
 * stadium is filled in rather than typed, and enter the section, row and seat,
 * which are the only parts of a ticket a fan can tell us. Continue hands the
 * seat to the ticket screen, which is where entering the match happens.
 *
 * The markup lives here rather than in either screen, so there is one copy of
 * it. The scanner used to ask for a ticket code instead, which meant typing
 * `prelude:3750191:108:14:8`: a string printed nowhere a fan can read.
 *
 * Mount it with Prelude.mountManualEntry(container, options). `onPrefill` is
 * called when the panel arrives already filled, which is how the list knows to
 * open its details element.
 */
(function () {
  "use strict";

  // One unbroken literal on purpose. docs/DESIGN.md quotes this class string
  // and scripts/check_docs.py looks for it here, and a string split across a
  // concatenation would no longer match what the doc shows.
  var FIELD = "w-full bg-surface-container px-3 py-1.5 rounded text-body-md text-on-surface border border-outline-variant/30 focus:outline-none focus:border-primary-container";
  var LABEL = "font-label-sm text-label-sm text-outline uppercase";

  function seatField(name, caption, example) {
    return '<div class="flex-1 flex flex-col gap-1">' +
             '<label class="' + LABEL + '" for="manual-' + name + '">' + caption + '</label>' +
             '<input autocomplete="off" class="' + FIELD + '" id="manual-' + name + '" ' +
               'inputmode="numeric" placeholder="' + example + '" required type="text">' +
           '</div>';
  }

  function markup() {
    return '<div class="flex flex-col gap-2">' +
             '<div class="flex flex-col gap-1">' +
               '<label class="' + LABEL + '" for="manual-match">Match</label>' +
               '<select class="' + FIELD + '" id="manual-match">' +
                 '<option value="">Choose a match</option>' +
               '</select>' +
             '</div>' +
             '<div class="flex flex-col gap-1">' +
               '<span class="' + LABEL + '">Stadium</span>' +
               '<span class="font-body-md text-body-md text-on-surface-variant" ' +
                 'id="manual-venue">Pick a match first</span>' +
             '</div>' +
             '<div class="flex gap-2">' +
               seatField("section", "Section", "108") +
               seatField("row", "Row", "14") +
               seatField("seat", "Seat", "8") +
             '</div>' +
             '<button class="mt-1 w-full h-touch-target-min rounded-full bg-primary-container ' +
               'text-on-primary-container font-label-lg text-label-lg font-bold tracking-wider ' +
               'uppercase flex items-center justify-center transition-opacity ' +
               'disabled:opacity-40 disabled:cursor-not-allowed" disabled id="manual-continue" ' +
               'type="button">Continue</button>' +
           '</div>';
  }

  function mount(container, options) {
    if (!container) return null;
    options = options || {};
    container.innerHTML = markup();

    var pick = container.querySelector("#manual-match");
    var venue = container.querySelector("#manual-venue");
    var section = container.querySelector("#manual-section");
    var row = container.querySelector("#manual-row");
    var seat = container.querySelector("#manual-seat");
    var go = container.querySelector("#manual-continue");
    var byId = {};

    function chosen() {
      return byId[pick.value] || null;
    }

    function update() {
      var match = chosen();
      venue.textContent = match ? match.live_seated.venue : "Pick a match first";
      go.disabled = !(match && section.value.trim() && row.value.trim() && seat.value.trim());
    }

    // Edit details comes back with manual=1, so the panel arrives open and
    // already filled and correcting one field is not a retype.
    function prefill() {
      if (!/[?&]manual=1(&|$)/.test(window.location.search)) return;
      pick.value = String(Prelude.matchId);
      var held = Prelude.ticketFor(Prelude.matchId);
      if (held) {
        section.value = held.section || "";
        row.value = held.row || "";
        seat.value = held.seat || "";
      }
      update();
      if (options.onPrefill) options.onPrefill();
    }

    Prelude.whenMatches(function (doc) {
      if (!doc) {
        venue.textContent = "The match list could not be loaded.";
        return;
      }
      for (var i = 0; i < doc.matches.length; i++) {
        var match = doc.matches[i];
        byId[String(match.match_id)] = match;
        var option = document.createElement("option");
        option.value = String(match.match_id);
        option.textContent = match.home_team + " vs " + match.away_team;
        pick.appendChild(option);
      }
      update();
      prefill();
      container.setAttribute("data-manual-ready", String(doc.matches.length));
    });

    [pick, section, row, seat].forEach(function (el) {
      el.addEventListener("input", update);
      el.addEventListener("change", update);
    });

    go.addEventListener("click", function () {
      var match = chosen();
      if (go.disabled || !match) return;
      // The seat travels to the ticket screen, which is where entering the
      // match actually happens, so nothing is reset here.
      Prelude.setTicket(match.match_id, {
        section: section.value.trim(), row: row.value.trim(), seat: seat.value.trim(),
        source: "manual"
      });
      window.location.href = Prelude.url("prelude_06_ticket.html", match.match_id);
    });

    update();
    return { update: update };
  }

  window.Prelude = window.Prelude || {};
  window.Prelude.mountManualEntry = mount;
})();
