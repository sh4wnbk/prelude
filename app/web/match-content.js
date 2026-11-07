/* Renders a screen from matches.json for the selected match.
 *
 * The match travels in the query string, for example ?match=3869685. With no
 * match in the URL the default is 1986, which is also the copy sitting inline
 * in the markup, so a screen opened on its own is already correct before this
 * runs.
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
 */
(function () {
  "use strict";

  var DEFAULT_MATCH = 3750191;

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
  var MATCH_ID = Number(queryValue("match")) || DEFAULT_MATCH;

  function url(path, matchId) {
    var parts = [];
    if (VERSION) parts.push("v=" + VERSION);
    parts.push("match=" + (matchId || MATCH_ID));
    return path + "?" + parts.join("&");
  }

  // Whether the session clock has reached the hero moment, for this match. It
  // is per session rather than per URL, so returning to Live keeps the updated
  // score without the state having to travel in the query string.
  function seenKey(matchId) {
    return "prelude.moment." + (matchId || MATCH_ID);
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
    return "prelude.ticket." + (matchId || MATCH_ID);
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
    matchId: MATCH_ID, url: url, defaultMatch: DEFAULT_MATCH,
    momentSeen: momentSeen, markMomentSeen: markMomentSeen,
    resetMoment: resetMoment, ticketFor: ticketFor, setTicket: setTicket,
    ticketLine: ticketLine, whenMatches: whenMatches, matches: null,
    listenerFor: listenerFor, setListener: setListener,
    nameFor: nameFor, setName: setName, headerWithName: headerWithName
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

  function renderChip(match) {
    setText("chip", match.label + " · LIVE");
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
  // moment card needs only the words. The inline markup already holds the
  // default match's neutral narration, so a failed fetch leaves a correct
  // screen rather than an empty one, which is the same bargain the rest of
  // this file makes.
  //
  // The card shows what the fan hears. There is one narration per
  // hero.voice_for key and narration-player.js picks the recording by the
  // same lookup, so the text under the grounding label and the voice reading
  // it are one piece of writing. With no listener answer the key is the
  // neutral one, which is what the inline copy holds. The label itself is
  // spelled in the markup and in app/narration.py and never here:
  // scripts/scan_copy.py refuses it in a copy file, because copy data
  // carries no markup that could place it over anything.
  function narrationKey(match) {
    var voiceFor = match.hero && match.hero.voice_for;
    if (!voiceFor) return null;
    var allegiance = listenerFor(match.match_id) || "neutral";
    return voiceFor[allegiance] || voiceFor.neutral || null;
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
        var key = narrationKey(match);
        var slot = (key && slots[key]) || slots.storyteller_neutral;
        // No narration for this listener means the words under the grounding
        // label were never checked for them, so the inline copy stays rather
        // than a blank sitting under a label it did not earn.
        if (slot && slot.text) setText("hero_narration", slot.text);
      })
      .catch(function () {
        /* Left on the inline copy, which is the default match. */
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
        var voiceFor = match.hero && match.hero.voice_for;
        var allegiance = listenerFor(match.match_id) || "neutral";
        var voiceKey = voiceFor ? voiceFor[allegiance] : null;
        var currentId = voiceKey ? voiceKey.split("_")[0] : null;

        var narrators = doc.narrators || [];
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

          (function (n, current) {
            btn.addEventListener("click", function () {
              if (current) return;
              note.textContent = n.name + " is coming soon. For now, Prelude picks your narrator from who you're with.";
              note.removeAttribute("hidden");
            });
          }(narrator, isCurrent));

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
    carryMatchThroughLinks();
    fetch(VERSION ? "matches.json?v=" + VERSION : "matches.json")
      .then(function (response) {
        if (!response.ok) throw new Error("matches.json " + response.status);
        return response.json();
      })
      .then(function (doc) {
        var match = null;
        for (var i = 0; i < doc.matches.length; i++) {
          if (doc.matches[i].match_id === MATCH_ID) match = doc.matches[i];
        }
        if (!match) {
          for (var j = 0; j < doc.matches.length; j++) {
            if (doc.matches[j].match_id === DEFAULT_MATCH) match = doc.matches[j];
          }
        }
        publishMatches(doc);
        if (match) render(match);
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
