/* Renders a screen from matches.json for the selected match.
 *
 * The match travels in the query string, for example ?match=3869685, and
 * nowhere else. With no match in the URL the fan has chosen none, and nothing
 * here chooses one for them: a screen that is about one match sends them to
 * the list instead, and the list and the scanner render no match at all.
 *
 * The copy sitting inline in the markup is match 3750191 on every screen but
 * the list. That is the fallback for a failed fetch, not a default choice;
 * scripts/check_match_copy.py is what holds it to matches.json.
 *
 * Fields are addressed by data-field, so the markup keeps its classes and
 * structure and this only replaces text. The Moments list is the exception: it
 * has a different number of cards per match, so the inline cards are reused as
 * templates and the list is rebuilt from them.
 *
 * If matches.json cannot be fetched, which is what happens when a screen is
 * opened straight off the filesystem, the inline 1986 copy stays as it is.
 * That is a correct screen rather than a broken one, so the fallback is quiet.
 * On success documentElement carries data-match-rendered, which is how a test
 * can tell rendering apart from the fallback.
 *
 * The moment card's narration is the one field with no inline copy and so no
 * fallback. It arrives from narrations.json, and it carries the grounding
 * label with it, so the 1986 words sitting under a 2022 header would be a
 * false claim rather than a stale one. renderNarration says the rest.
 */
(function () {
  "use strict";

  function queryValue(name) {
    var m = new RegExp("[?&]" + name + "=([^&#]*)").exec(window.location.search);
    return m ? decodeURIComponent(m[1]) : null;
  }

  // This script is loaded as match-content.js?v=<deploy>, so it knows the
  // version without anything having to tell it.
  function deployVersion() {
    var src = (document.currentScript && document.currentScript.src) || "";
    var m = /[?&]v=([^&]*)/.exec(src);
    return m ? m[1] : null;
  }

  var VERSION = deployVersion();

  // The match the fan has chosen, and null when they have not. A choice
  // travels in the query string and nowhere else: the list writes it when a
  // card is confirmed, the scanner and manual entry write it from a ticket,
  // and every link a screen carries passes it on. Nothing here invents one.
  var CHOSEN_MATCH = Number(queryValue("match")) || null;

  // The screens that are about one match. Reached with no match chosen, each
  // of them would have to pick one to have anything to say, so the fan goes
  // back to the list instead. The list and the scanner are not here, because
  // neither is about a match yet.
  var MATCH_REQUIRED = {
    "prelude_02_live_seated.html": true,
    "prelude_03_moment_card.html": true,
    "prelude_04_moments.html": true,
    "prelude_06_ticket.html": true,
    "prelude_07_profile.html": true
  };

  function screenFile() {
    var path = window.location.pathname;
    return path.slice(path.lastIndexOf("/") + 1);
  }

  function needsMatch() {
    return MATCH_REQUIRED[screenFile()] === true;
  }

  // replace() rather than assign(): a screen the fan never chose a match for
  // is not a step in the history that Back should return to.
  function goToPicker() {
    window.location.replace(
      VERSION ? "prelude_01_picker.html?v=" + VERSION : "prelude_01_picker.html"
    );
  }

  // Read in the head, before the markup is parsed, so a screen that is about
  // one match never paints its inline copy on the way past.
  var SENT_TO_PICKER = !CHOSEN_MATCH && needsMatch();
  if (SENT_TO_PICKER) goToPicker();

  // A link carries the match only when there is one. With none chosen the
  // links leave the list bare, and whichever screen they reach sends the fan
  // straight back to it rather than opening on a match nobody picked.
  function url(path, matchId) {
    var parts = [];
    if (VERSION) parts.push("v=" + VERSION);
    var id = matchId || CHOSEN_MATCH;
    if (id) parts.push("match=" + id);
    return parts.length ? path + "?" + parts.join("&") : path;
  }

  // Whether the session clock has reached the hero moment, for this match. It
  // is per session rather than per URL, so returning to Live keeps the updated
  // score without the state having to travel in the query string.
  function seenKey(matchId) {
    return "prelude.moment." + (matchId || CHOSEN_MATCH);
  }

  function momentSeen() {
    try {
      return window.sessionStorage.getItem(seenKey()) === "1";
    } catch (e) {
      return false;   // private mode, blocked storage: treat as not yet seen
    }
  }

  function markMomentSeen() {
    try {
      window.sessionStorage.setItem(seenKey(), "1");
    } catch (e) {
      /* nothing to do; the screens still work, they just do not advance */
    }
  }

  // Picking a match from the list starts it over, so Heading out is there to
  // press again. Without this the second visit to a match in the same session
  // would open already past its moment. It takes the match explicitly, because
  // the list is not itself on the match being picked.
  function resetMoment(matchId) {
    try {
      window.sessionStorage.removeItem(seenKey(matchId));
    } catch (e) {
      /* nothing stored, nothing to clear */
    }
  }

  // Who the fan is with, per match. The value is "team_a", "team_b" or
  // "neutral"; anything else is treated as if nothing was stored.
  function listenerKey(matchId) {
    return "prelude.listener." + matchId;
  }

  function listenerFor(matchId) {
    try {
      var raw = window.sessionStorage.getItem(listenerKey(matchId));
      if (raw === "team_a" || raw === "team_b" || raw === "neutral") return raw;
      return null;
    } catch (e) {
      return null;
    }
  }

  function setListener(matchId, allegiance) {
    try {
      window.sessionStorage.setItem(listenerKey(matchId), allegiance);
    } catch (e) {
      /* nothing to do */
    }
  }

  // The name the fan wants to be called, shared across all matches in the
  // session. Trimmed, collapsed, capped at 40 characters; key removed when
  // the result is empty.
  function nameFor() {
    try {
      return window.sessionStorage.getItem("prelude.name") || null;
    } catch (e) {
      return null;
    }
  }

  function setName(name) {
    try {
      var trimmed = (name || "").trim().replace(/\s+/g, " ").slice(0, 40);
      if (trimmed) {
        window.sessionStorage.setItem("prelude.name", trimmed);
      } else {
        window.sessionStorage.removeItem("prelude.name");
      }
    } catch (e) {
      /* nothing to do */
    }
  }

  // The narrator the fan chose. Unlike "Who are you with" and the name, this
  // is a standing preference rather than an answer about tonight: a fan sets
  // it before a match, at home or in transit, and it is still theirs when they
  // open the app at the ground. So it lives in localStorage, which survives a
  // closed tab, while the allegiance and the name stay per session. One value
  // across all matches, every read and write inside a try, key removed when
  // the id is empty.
  var NARRATOR_KEY = "prelude.narrator";

  // It was a session value under this same name until it became a standing
  // preference. A fan who had already chosen one would lose it on the switch,
  // so the old session key is read once per page, carried over to localStorage
  // and cleared. Once localStorage holds a choice the old key is never
  // consulted again, so a stale session value cannot outrank a later choice.
  var narratorCarried = false;

  function carryNarratorOver() {
    if (narratorCarried) return;
    narratorCarried = true;
    try {
      if (window.localStorage.getItem(NARRATOR_KEY)) return;
      var held = window.sessionStorage.getItem(NARRATOR_KEY);
      if (held) {
        window.localStorage.setItem(NARRATOR_KEY, held);
        window.sessionStorage.removeItem(NARRATOR_KEY);
      }
    } catch (e) {
      /* blocked storage: there is nothing to carry over */
    }
  }

  function narratorFor() {
    try {
      carryNarratorOver();
      return window.localStorage.getItem(NARRATOR_KEY) || null;
    } catch (e) {
      return null;
    }
  }

  function setNarrator(id) {
    try {
      narratorCarried = true;   // a choice made now outranks any old one
      if (id) {
        window.localStorage.setItem(NARRATOR_KEY, id);
      } else {
        window.localStorage.removeItem(NARRATOR_KEY);
      }
      window.sessionStorage.removeItem(NARRATOR_KEY);
    } catch (e) {
      /* nothing to do */
    }
  }

  // The one lookup: the slot a fan is about to hear, given the match, an
  // optional narrator id (defaults to the stored choice) and an optional side
  // (defaults to the stored answer for this match). Only this function reads
  // hero.voice_for.
  function slotFor(match, narratorId, side) {
    var voiceFor = match && match.hero && match.hero.voice_for;
    if (!voiceFor) return null;
    var answer = side || listenerFor(match.match_id) || "neutral";
    var fallback = voiceFor[answer] || voiceFor.neutral || null;
    var chosen = narratorId === undefined ? narratorFor() : narratorId;
    if (!chosen) return fallback;
    var keys = [voiceFor[answer], voiceFor.neutral];
    for (var i = 0; i < keys.length; i++) {
      if (keys[i] && keys[i].indexOf(chosen + "_") === 0) return keys[i];
    }
    return fallback;
  }

  // Append the fan's name to the last sentence of a header, replacing the
  // final period with ", name.". The name is joined as a plain string and
  // never passed to replace(): a replacement string reads "$&" and "$1" as
  // patterns, so a name holding them would come out changed.
  function headerWithName(header, name) {
    if (!name) return header;
    if (!header) return header;
    return header.replace(/\.$/, "") + ", " + name + ".";
  }

  // The seat a fan entered by hand, for this match, in this session. It is the
  // fan's own ticket rather than anything read from the feed, so it overrides
  // the seat in matches.json when it is there and changes nothing else.
  function ticketKey(matchId) {
    return "prelude.ticket." + (matchId || CHOSEN_MATCH);
  }

  function ticketFor(matchId) {
    try {
      var raw = window.sessionStorage.getItem(ticketKey(matchId));
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;   // blocked storage or something that is not JSON
    }
  }

  function setTicket(matchId, seat) {
    try {
      window.sessionStorage.setItem(ticketKey(matchId), JSON.stringify(seat));
    } catch (e) {
      /* the screens still work, they just show the seat from matches.json */
    }
  }

  function ticketLine(seat) {
    if (!seat || !seat.section || !seat.row || !seat.seat) return null;
    return "Sec " + seat.section + " \u00b7 Row " + seat.row +
           " \u00b7 Seat " + seat.seat;
  }

  // matches.json, once, for screens that need the list rather than one match.
  // Callers that arrive before the fetch resolves are held and then called; a
  // failed fetch calls them with null so they can degrade rather than hang.
  var loaded = null;
  var settled = false;
  var waiting = [];

  function whenMatches(callback) {
    if (settled) { callback(loaded); return; }
    waiting.push(callback);
  }

  function publishMatches(doc) {
    loaded = doc;
    settled = true;
    window.Prelude.matches = doc;
    while (waiting.length) waiting.shift()(doc);
  }

  // Available to the screens' own scripts before the fetch resolves, because
  // the match id comes from the URL and not from the file.
  window.Prelude = {
    matchId: CHOSEN_MATCH, chosenMatch: CHOSEN_MATCH, url: url,
    momentSeen: momentSeen, markMomentSeen: markMomentSeen,
    resetMoment: resetMoment, ticketFor: ticketFor, setTicket: setTicket,
    ticketLine: ticketLine, whenMatches: whenMatches, matches: null,
    listenerFor: listenerFor, setListener: setListener,
    nameFor: nameFor, setName: setName, headerWithName: headerWithName,
    narratorFor: narratorFor, setNarrator: setNarrator, slotFor: slotFor,
    whenNarrationShown: whenNarrationShown
  };

  function field(name, root) {
    return (root || document).querySelector('[data-field="' + name + '"]');
  }

  function setText(name, value) {
    var el = field(name);
    if (el && value !== null && value !== undefined) el.textContent = value;
  }

  function carryMatchThroughLinks() {
    var links = document.querySelectorAll('a[href]');
    for (var i = 0; i < links.length; i++) {
      var href = links[i].getAttribute("href");
      if (!href || /^(https?:|mailto:|#)/.test(href)) continue;
      var path = href.split("?")[0];
      if (!/\.html$/.test(path)) continue;
      links[i].setAttribute("href", url(path));
    }
  }

  // The pill names a match and says it is live, so it has nothing true to say
  // before the fan has chosen one. The list ships it hidden and this is what
  // shows it; a header with no pill is a shape the app already has, because
  // the scanner screen carries one. Every other screen is about one match by
  // the time it can be reached, so its pill is in the markup and shown.
  function renderChip(match) {
    var el = field("chip");
    if (!el) return;
    el.textContent = match.label + " · LIVE";
    var pill = field("chip_pill");
    if (pill) pill.style.removeProperty("display");
  }

  function renderLiveSeated(match) {
    var seated = match.live_seated;
    if (!seated || !field("state_badge")) return;
    // Before the moment the clock sits short of it; after, it has moved on and
    // the score is the one the data records at that point.
    var state = momentSeen() ? seated.after : seated.before;

    var teams = field("teams_upper");
    if (teams) {
      teams.innerHTML =
        match.home_team.toUpperCase() +
        ' <span class="text-on-surface-variant font-normal">vs</span> ' +
        match.away_team.toUpperCase();
    }
    setText("venue", seated.venue);

    var ticket = field("ticket");
    if (ticket) {
      // A seat entered by hand is this fan's own ticket, so it wins over the
      // one in matches.json for as long as the session lasts.
      var line = ticketLine(ticketFor(match.match_id)) || seated.ticket;
      if (line) {
        ticket.textContent = line;
        ticket.parentElement.style.removeProperty("display");
      } else {
        ticket.parentElement.style.display = "none";
      }
    }

    setText("state_badge", state.period_label + " · " + state.display_minute + "'");
    setText("home_name", match.home_team);
    setText("away_name", match.away_team);
    setText("home_goals", state.home_goals);
    setText("away_goals", state.away_goals);
    setText("half_line", state.half_label + " · " + state.display_minute + "'");
    setText("caption", seated.caption);

    setText("live_prompt", state.prompt);
    setText("live_action", state.action);
    setText("live_help", state.help);
  }

  function renderHero(match) {
    if (!field("hero_caption")) return;
    setText("hero_caption", match.hero.caption);
    if (match.hero.opening) {
      setText("hero_header", headerWithName(match.hero.opening.header, nameFor()));
    }
    setText("hero_quote", match.hero.quote);
    // The share sheet must describe this match, not the one in the markup.
    var share = document.getElementById("shareAction");
    if (share && match.hero.share_text) {
      share.setAttribute("data-share-text", match.hero.share_text);
    }
  }

  // The narration this fan is about to hear, frozen by
  // scripts/freeze_narrations.py. It is fetched rather than carried in
  // matches.json because it is not hand-written copy: narrations.json records
  // who wrote each one and the check's verdict beside the words, and the
  // moment card needs only the words.
  //
  // This one field does not take the fallback the rest of this file takes.
  // Everywhere else the inline copy is the default match's and a failed fetch
  // leaves a correct screen; here it would leave the 1986 narration under a
  // 2022 header and under the grounding label, which a fan on a slow
  // connection can read. So the card carries no narration inline at all: the
  // paragraph and the label ship hidden and empty, and showNarration is the
  // one thing that fills and shows them. Until the frozen text for this match
  // and this listener's slot arrives there is nothing to label, and a blank
  // where the words will be is better than another match's words.
  //
  // The card shows what the fan hears. There is one narration per
  // hero.voice_for key and narration-player.js picks the recording by the
  // same lookup, so the text under the grounding label and the voice reading
  // it are one piece of writing. With no listener answer the key is the
  // neutral one. The label itself is spelled in the markup and in
  // app/narration.py and never here: scripts/scan_copy.py refuses it in a
  // copy file, because copy data carries no markup that could place it over
  // anything.
  // The play button waits for these words. app/web/narration-player.js
  // subscribes here and enables the button when this fires, and showNarration
  // below is the one thing that fires it, so the words, the label and the
  // offer of the voice arrive in one step. A narrations.json that fails, that
  // holds nothing for this match, or that holds nothing for this listener's
  // slot never reaches showNarration, so this never fires and the button
  // stays as the markup ships it: disabled.
  var narrationShown = false;
  var narrationWaiting = [];

  function whenNarrationShown(callback) {
    if (narrationShown) { callback(); return; }
    narrationWaiting.push(callback);
  }

  function announceNarration() {
    narrationShown = true;
    while (narrationWaiting.length) narrationWaiting.shift()();
  }

  function showNarration(text) {
    var narration = field("hero_narration");
    var label = field("hero_label");
    if (!narration) return;
    narration.textContent = text;
    narration.style.removeProperty("display");
    // The label is shown in the same breath as the words it is about, so
    // there is no moment at which one of the two is on screen without the
    // other.
    if (label) label.style.removeProperty("display");
    // And the play button in the same breath again, for the reason on
    // announceNarration above: the card and the voice are one piece of
    // writing, so the offer of the voice arrives with the words.
    announceNarration();
  }

  function renderNarration(match) {
    if (!field("hero_narration")) return;

    fetch(VERSION ? "narrations.json?v=" + VERSION : "narrations.json")
      .then(function (response) {
        if (!response.ok) throw new Error("narrations.json " + response.status);
        return response.json();
      })
      .then(function (doc) {
        var frozen = (doc.narrations || {})[String(match.match_id)];
        if (!frozen) return;
        var slots = frozen.slots || {};
        var key = slotFor(match);
        var slot = (key && slots[key]) || slots.storyteller_neutral;
        // No narration for this listener means the words under the grounding
        // label were never checked for them, so nothing is shown rather than
        // another listener's telling sitting under a label it did not earn.
        if (slot && slot.text) showNarration(slot.text);
      })
      .catch(function () {
        /* The narration and the label stay hidden. */
      });
  }

  function renderMoments(match) {
    var list = field("moments_list");
    if (!list) return;

    setText("synced", match.synced_count + " Synced");
    setText("moments_subtitle", match.moments_subtitle);

    var templates = [];
    for (var i = 0; i < list.children.length; i++) templates.push(list.children[i]);
    if (!templates.length) return;

    var built = [];
    for (var j = 0; j < match.moments.length; j++) {
      var moment = match.moments[j];
      var card = templates[j % templates.length].cloneNode(true);
      var tag = field("tag", card);
      var clock = field("clock", card);
      var title = field("title", card);
      var body = field("body", card);
      if (tag) tag.textContent = moment.tag;
      if (clock) clock.textContent = moment.period_label + " · " + moment.display_minute + "'";
      if (title) title.textContent = moment.title;
      if (body) body.textContent = moment.body;
      built.push(card);
    }

    list.innerHTML = "";
    for (var k = 0; k < built.length; k++) list.appendChild(built[k]);
  }

  function renderProfile(match) {
    if (!field("profile_name")) return;
    var allegiance = listenerFor(match.match_id);
    var withLabel;
    if (allegiance === "team_a") {
      withLabel = match.home_team;
    } else if (allegiance === "team_b") {
      withLabel = match.away_team;
    } else if (allegiance === "neutral") {
      withLabel = "Just here for the game";
    } else {
      withLabel = "Not set";
    }
    setText("profile_name", nameFor() || "Not set");
    setText("profile_with", withLabel);
  }

  function renderNarrators(match) {
    var list = field("narrator_list");
    var note = field("narrator_note");
    if (!list || !note) return;

    fetch(VERSION ? "narrators.json?v=" + VERSION : "narrators.json")
      .then(function (response) {
        if (!response.ok) throw new Error("narrators.json " + response.status);
        return response.json();
      })
      .then(function (doc) {
        var currentSlot = slotFor(match);
        var currentId = currentSlot ? currentSlot.split("_")[0] : null;

        var narrators = doc.narrators || [];

        while (list.firstChild) list.removeChild(list.firstChild);

        for (var i = 0; i < narrators.length; i++) {
          var narrator = narrators[i];
          var isCurrent = narrator.id === currentId;

          var btn = document.createElement("button");
          btn.type = "button";
          var baseClasses = "w-full text-left rounded-xl p-card-padding-sm flex flex-col gap-space-2xs";
          if (isCurrent) {
            btn.className = baseClasses + " bg-primary-container text-on-primary";
            btn.setAttribute("aria-current", "true");
          } else {
            btn.className = baseClasses + " bg-surface-container-highest text-on-surface";
          }

          var nameSpan = document.createElement("span");
          nameSpan.className = "font-label-lg text-label-lg font-bold";
          nameSpan.textContent = narrator.name;

          var profileSpan = document.createElement("span");
          profileSpan.className = "font-body-md text-body-md";
          profileSpan.textContent = narrator.profile;

          btn.appendChild(nameSpan);
          btn.appendChild(profileSpan);

          var ownSlot = slotFor(match, narrator.id);
          var canChoose = ownSlot ? ownSlot.indexOf(narrator.id + "_") === 0 : false;

          (function (n, choosable) {
            if (choosable && !isCurrent) {
              btn.addEventListener("click", function () {
                setNarrator(n.id);
                renderNarrators(match);
              });
            } else if (!choosable) {
              btn.setAttribute("aria-disabled", "true");
              btn.addEventListener("click", function () {
                var hasAnySlot = ["team_a", "team_b", "neutral"].some(function (ans) {
                  var s = slotFor(match, n.id, ans);
                  return s ? s.indexOf(n.id + "_") === 0 : false;
                });
                note.textContent = hasAnySlot
                  ? n.name + " needs a team. Choose a team under 'Who are you with.'"
                  : n.name + " is coming soon.";
                note.removeAttribute("hidden");
              });
            }
          }(narrator, canChoose));

          list.appendChild(btn);
        }
      })
      .catch(function () {
        /* Leave the list empty on failure. */
      });
  }

  function render(match) {
    renderChip(match);
    renderLiveSeated(match);
    renderHero(match);
    renderNarration(match);
    renderMoments(match);
    renderProfile(match);
    renderNarrators(match);
    document.documentElement.setAttribute("data-match-rendered", String(match.match_id));
  }

  function start() {
    if (SENT_TO_PICKER) return;
    carryMatchThroughLinks();
    fetch(VERSION ? "matches.json?v=" + VERSION : "matches.json")
      .then(function (response) {
        if (!response.ok) throw new Error("matches.json " + response.status);
        return response.json();
      })
      .then(function (doc) {
        publishMatches(doc);
        // Nothing is rendered until the fan has chosen a match. The list and
        // the scanner are whole without one, and rendering a match here that
        // nobody picked is what put one into the header.
        if (!CHOSEN_MATCH) return;
        var match = null;
        for (var i = 0; i < doc.matches.length; i++) {
          if (doc.matches[i].match_id === CHOSEN_MATCH) match = doc.matches[i];
        }
        // The URL names a match this app does not hold. A screen about one
        // match has nothing to show for it, so the fan goes to the list.
        if (!match) {
          if (needsMatch()) goToPicker();
          return;
        }
        render(match);
      })
      .catch(function () {
        /* Left on the inline copy, which is the default match. */
        publishMatches(null);
      });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
