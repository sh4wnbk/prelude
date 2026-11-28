/* The bird's-eye renderer: marks on an SVG surface, drawn up to a time.
 *
 * It knows five primitives and nothing about what they stand for:
 *
 *   dot     an actor: a plain circle, or a circle with an embedded X
 *           (`crossed`)
 *   object  an object path: a solid straight line from `at` to `to`, with
 *           an arrowhead
 *   actor   an actor path: a dashed straight line from `at` to `to`, with an
 *           arrowhead
 *   burst   an attempt burst at `at`
 *   ring    a beat ring at `at`, with an embedded X when `crossed`
 *
 * A mark is {id, kind, at, to, crossed, tone, startMs, actor, label,
 * labelAt}. `tone` is the colour the mark is drawn in. `actor` and `label`
 * are optional: where a mark has both, the label is written at its
 * `labelAt`, and where one actor has several drawn marks, only the latest
 * one's label is shown, so a name sits where that actor was last drawn.
 *
 * The surface is the adapter's. This file adds one group to it and changes
 * nothing else there. `picture(ms)` redraws that group with every mark whose
 * `startMs` is at or before `ms`, in the order the marks were given, and
 * answers the ids it drew.
 */
(function () {
  "use strict";

  var NS = "http://www.w3.org/2000/svg";
  var made = 0;

  function el(name, attrs) {
    var node = document.createElementNS(NS, name);
    for (var key in attrs) {
      if (Object.prototype.hasOwnProperty.call(attrs, key)) {
        node.setAttribute(key, String(attrs[key]));
      }
    }
    return node;
  }

  function create(svg, marks) {
    var prefix = "birdseye" + (made += 1) + "-";
    var defs = el("defs", {});
    var layer = el("g", { "data-layer": "marks" });
    svg.appendChild(defs);
    svg.appendChild(layer);
    var heads = {};

    // One arrowhead per colour, made the first time that colour is drawn.
    function head(tone) {
      if (heads[tone]) return heads[tone];
      var id = prefix + "head" + Object.keys(heads).length;
      var marker = el("marker", {
        id: id, viewBox: "0 0 10 10", refX: 8, refY: 5,
        markerWidth: 4, markerHeight: 4, orient: "auto-start-reverse",
      });
      marker.appendChild(el("path", { d: "M0,0 L10,5 L0,10 z", fill: tone }));
      defs.appendChild(marker);
      heads[tone] = id;
      return id;
    }

    function cross(group, x, y, r, tone) {
      var d = r * 0.7;
      group.appendChild(el("line", {
        x1: x - d, y1: y - d, x2: x + d, y2: y + d,
        stroke: tone, "stroke-width": 0.35,
      }));
      group.appendChild(el("line", {
        x1: x - d, y1: y + d, x2: x + d, y2: y - d,
        stroke: tone, "stroke-width": 0.35,
      }));
    }

    function line(group, mark, dashed) {
      var attrs = {
        x1: mark.at[0], y1: mark.at[1], x2: mark.to[0], y2: mark.to[1],
        stroke: mark.tone, "stroke-width": 0.45, "stroke-linecap": "round",
        "marker-end": "url(#" + head(mark.tone) + ")",
      };
      if (dashed) attrs["stroke-dasharray"] = "1.4 1";
      group.appendChild(el("line", attrs));
    }

    var DRAW = {
      dot: function (group, mark) {
        var x = mark.at[0], y = mark.at[1], r = 1.4;
        group.appendChild(el("circle", {
          cx: x, cy: y, r: r, stroke: mark.tone, "stroke-width": 0.4,
          fill: mark.tone, "fill-opacity": 0.2,
        }));
        if (mark.crossed) cross(group, x, y, r, mark.tone);
      },
      object: function (group, mark) { line(group, mark, false); },
      actor: function (group, mark) { line(group, mark, true); },
      burst: function (group, mark) {
        var x = mark.at[0], y = mark.at[1];
        group.appendChild(el("circle", { cx: x, cy: y, r: 0.7, fill: mark.tone }));
        for (var n = 0; n < 8; n += 1) {
          var a = (Math.PI / 4) * n;
          group.appendChild(el("line", {
            x1: x + Math.cos(a) * 1.4, y1: y + Math.sin(a) * 1.4,
            x2: x + Math.cos(a) * 2.8, y2: y + Math.sin(a) * 2.8,
            stroke: mark.tone, "stroke-width": 0.4, "stroke-linecap": "round",
          }));
        }
      },
      ring: function (group, mark) {
        var x = mark.at[0], y = mark.at[1], r = 2.6;
        group.appendChild(el("circle", {
          cx: x, cy: y, r: r, stroke: mark.tone, "stroke-width": 0.4,
          fill: "none",
        }));
        if (mark.crossed) cross(group, x, y, 1.4, mark.tone);
      },
    };

    marks.forEach(function (mark) {
      if (!DRAW[mark.kind]) throw new Error("no primitive called " + mark.kind);
      if (typeof mark.startMs !== "number") {
        throw new Error("mark " + mark.id + " has no start time");
      }
    });

    function picture(ms) {
      while (layer.firstChild) layer.removeChild(layer.firstChild);
      var drawn = [];
      var latest = {};
      var order = [];
      marks.forEach(function (mark) {
        if (mark.startMs > ms) return;
        var group = el("g", { "data-mark": mark.id, "data-kind": mark.kind });
        DRAW[mark.kind](group, mark);
        layer.appendChild(group);
        drawn.push(mark.id);
        if (mark.actor && mark.label) {
          if (!latest[mark.actor]) order.push(mark.actor);
          latest[mark.actor] = mark;
        }
      });
      order.forEach(function (actor) {
        var mark = latest[actor];
        var text = el("text", {
          x: mark.labelAt[0], y: mark.labelAt[1],
          "text-anchor": "middle", "font-size": 2.4, fill: mark.tone,
          stroke: "#000", "stroke-opacity": 0.6, "stroke-width": 0.6,
          "paint-order": "stroke", "data-label-for": mark.id,
        });
        text.textContent = mark.label;
        layer.appendChild(text);
      });
      return drawn;
    }

    return { picture: picture, marks: marks };
  }

  window.Prelude = window.Prelude || {};
  window.Prelude.birdseye = create;
})();
