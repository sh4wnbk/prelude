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
  var SEEN_KEY = "prelude.moment." + MATCH_ID;

  function momentSeen() {
    try {
      return window.sessionStorage.getItem(SEEN_KEY) === "1";
    } catch (e) {
      return false;   // private mode, blocked storage: treat as not yet seen
    }
  }

  function markMomentSeen() {
    try {
      window.sessionStorage.setItem(SEEN_KEY, "1");
    } catch (e) {
      /* nothing to do; the screens still work, they just do not advance */
    }
  }

  // Available to the screens' own scripts before the fetch resolves, because
  // the match id comes from the URL and not from the file.
  window.Prelude = {
    matchId: MATCH_ID, url: url, defaultMatch: DEFAULT_MATCH,
    momentSeen: momentSeen, markMomentSeen: markMomentSeen
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
      if (seated.ticket) {
        ticket.textContent = seated.ticket;
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
    setText("hero_quote", match.hero.quote);
    // The share sheet must describe this match, not the one in the markup.
    var share = document.getElementById("shareAction");
    if (share && match.hero.share_text) {
      share.setAttribute("data-share-text", match.hero.share_text);
    }
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

  function render(match) {
    renderChip(match);
    renderLiveSeated(match);
    renderHero(match);
    renderMoments(match);
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
        if (match) render(match);
      })
      .catch(function () {
        /* Left on the inline copy, which is the default match. */
      });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
