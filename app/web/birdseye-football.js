/* The football adapter for the bird's-eye renderer in birdseye.js.
 *
 * It reads `play_segments.json` (each match's records, and each slot's
 * segments and `draw_from`) and `segment_timings.json` (when each segment
 * starts in that slot's recording), and turns every record a slot draws into
 * one mark for `Prelude.birdseye`:
 *
 *   Pass                                       object path
 *   Carry                                      actor path
 *   Dribble, Dribbled Past                     beat ring
 *   Shot                                       attempt burst
 *   Ball Receipt*, Ball Recovery, Pressure     actor dot
 *
 * A path runs straight from `location` to `end_location`, x and y only. A
 * mark starts at the `start_ms` of the segment `draw_from` names for its
 * record.
 *
 * **One frame.** StatsBomb records each team attacking left to right, so
 * every record of the side that did not score is turned to
 * (120 - x, 80 - y). The scoring side is the team of the match's Shot
 * record, which the records hold exactly one of.
 *
 * **Sides.** The scoring side's actors are plain circles and the other
 * side's carry an X. The listener's side is amber and everything else is
 * chalk white; a neutral listener, `null`, gets no amber. Nothing in the
 * repo records a team's colours, so none are used.
 *
 * **Names.** A record's `label` is written where its actor is drawn, from
 * the moment its segment starts: above the scoring side's actors and below
 * the other side's.
 *
 * Not wired into any screen yet.
 */
(function () {
  "use strict";

  var NS = "http://www.w3.org/2000/svg";
  var WIDTH = 120;
  var HEIGHT = 80;
  var SURFACE = "#1d2621";
  var EDGE = "#3a4740";
  var CHALK = "#ece8dc";
  var AMBER = "#f2b33d";

  var KIND = {
    "Pass": "object",
    "Carry": "actor",
    "Dribble": "ring",
    "Dribbled Past": "ring",
    "Shot": "burst",
    "Ball Receipt*": "dot",
    "Ball Recovery": "dot",
    "Pressure": "dot",
  };

  function load(base) {
    var root = base || "";
    function get(name) {
      return fetch(root + name).then(function (response) {
        if (!response.ok) throw new Error(name + " answered " + response.status);
        return response.json();
      });
    }
    return Promise.all([get("play_segments.json"), get("segment_timings.json")])
      .then(function (both) { return { segments: both[0], timings: both[1] }; });
  }

  function scoringTeam(records) {
    var teams = {};
    Object.keys(records).forEach(function (id) {
      if (records[id].type === "Shot") teams[records[id].team] = true;
    });
    var found = Object.keys(teams);
    if (found.length !== 1) {
      throw new Error("expected one team with a Shot record, found " + found.length);
    }
    return found[0];
  }

  // The one frame: the scoring side as recorded, the other side turned.
  function frame(point, turned) {
    if (!point) return null;
    return turned ? [WIDTH - point[0], HEIGHT - point[1]] : [point[0], point[1]];
  }

  // Where a name is written: above the scoring side's actor and below the
  // other side's, so the two actors of one duel do not write over each other.
  function labelAt(point, turned) {
    return [point[0], turned ? point[1] + 4.4 : point[1] - 2.4];
  }

  function marksFor(data, matchId, slot, listenerTeam) {
    var match = data.segments.matches[String(matchId)];
    if (!match || !match.slots[slot]) {
      throw new Error("no segments for " + matchId + " " + slot);
    }
    var cut = match.slots[slot];
    var timed = data.timings.matches[String(matchId)][slot].segments;
    if (timed.length !== cut.segments.length) {
      throw new Error(slot + ": " + timed.length + " timings for " +
                      cut.segments.length + " segments");
    }
    cut.segments.forEach(function (segment, n) {
      if (timed[n].said !== segment.said) {
        throw new Error(slot + " segment " + n + " is timed as " + timed[n].said);
      }
    });
    var scorer = scoringTeam(match.records);
    var ids = Object.keys(cut.draw_from).sort(function (a, b) {
      return match.records[a].index - match.records[b].index;
    });
    return ids.map(function (id) {
      var record = match.records[id];
      var kind = KIND[record.type];
      if (!kind) throw new Error("no mark for a " + record.type + " record");
      var turned = record.team !== scorer;
      var at = frame(record.location, turned);
      var to = frame(record.end_location, turned);
      if ((kind === "object" || kind === "actor") && !to) {
        throw new Error(record.type + " " + record.index + " has no end_location");
      }
      return {
        id: id,
        kind: kind,
        at: at,
        to: to,
        crossed: turned,
        tone: listenerTeam && record.team === listenerTeam ? AMBER : CHALK,
        startMs: timed[cut.draw_from[id]].start_ms,
        actor: record.player,
        label: record.label,
        labelAt: labelAt(kind === "actor" ? to : at, turned),
      };
    });
  }

  function surface(svg) {
    svg.setAttribute("viewBox", "0 0 " + WIDTH + " " + HEIGHT);
    var area = document.createElementNS(NS, "rect");
    area.setAttribute("x", "0");
    area.setAttribute("y", "0");
    area.setAttribute("width", String(WIDTH));
    area.setAttribute("height", String(HEIGHT));
    area.setAttribute("fill", SURFACE);
    area.setAttribute("stroke", EDGE);
    area.setAttribute("stroke-width", "0.5");
    svg.appendChild(area);
    return svg;
  }

  function mount(svg, data, matchId, slot, listenerTeam) {
    var marks = marksFor(data, matchId, slot, listenerTeam || null);
    return window.Prelude.birdseye(surface(svg), marks);
  }

  window.Prelude = window.Prelude || {};
  window.Prelude.birdseyeFootball = {
    load: load,
    marksFor: marksFor,
    mount: mount,
    frame: frame,
    scoringTeam: scoringTeam,
    AMBER: AMBER,
    CHALK: CHALK,
  };
})();
