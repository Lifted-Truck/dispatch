"""Rollup renderer (E5) — `dispatch-rollup.1` -> self-contained HTML.

Pure like the other renderers: no clock, no network, no model calls. Shares
theme.TOKENS so the rollup is visibly the same publication as the digest
and the board.
"""

import html
import re

from . import theme

SUPPORTED_SCHEMA = "dispatch-rollup.1"
_TOP = 8  # projects shown per week before "and N more"

_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul",
           "Aug", "Sep", "Oct", "Nov", "Dec")

_CSS = theme.TOKENS + """html { background: var(--paper); }
body { font-family: var(--sans); color: var(--ink); background: var(--paper);
  margin: 0; padding: 2.5rem 1.25rem 4rem; line-height: 1.5; }
main { max-width: 52rem; margin: 0 auto; }
.eyebrow { font-family: var(--mono); font-size: .72rem; letter-spacing: .14em;
  text-transform: uppercase; color: var(--accent); margin: 0 0 .5rem; }
h1 { font-size: 1.7rem; line-height: 1.2; margin: 0 0 .3rem; font-weight: 650; }
.lede { color: var(--muted); margin: 0 0 1.4rem; max-width: 42rem; font-size: .92rem; }
.limits { font-size: .8rem; color: var(--muted); border: 1px solid var(--line);
  border-radius: 6px; padding: .6rem .9rem; margin: 0 0 1.6rem; background: var(--card); }
.limits b { color: var(--warn); }
.week { background: var(--card); border: 1px solid var(--line); border-radius: 6px;
  padding: 1rem 1.2rem; margin: 0 0 1rem; }
.whead { display: flex; flex-wrap: wrap; align-items: baseline; gap: .6rem; margin: 0 0 .6rem; }
.wname { font-size: 1.05rem; font-weight: 650; margin: 0; }
.wdays { font-family: var(--mono); font-size: .7rem; color: var(--muted); }
.stats { display: flex; flex-wrap: wrap; gap: .4rem; margin: 0 0 .8rem; }
.stat { flex: 1 1 5.5rem; border: 1px solid var(--line); border-radius: 5px; padding: .4rem .6rem; }
.stat .n { font-family: var(--mono); font-size: 1.05rem; font-weight: 650; display: block;
  font-variant-numeric: tabular-nums; }
.stat .l { font-size: .66rem; color: var(--muted); }
table { border-collapse: collapse; width: 100%; font-size: .85rem;
  font-variant-numeric: tabular-nums; }
th, td { text-align: left; padding: .32rem .5rem; border-top: 1px solid var(--line); }
th { border-top: none; font-size: .66rem; text-transform: uppercase; letter-spacing: .08em;
  color: var(--muted); font-weight: 600; }
td.num, th.num { text-align: right; }
.name { font-weight: 600; } .group { color: var(--muted); font-weight: 400; }
.pill { font-family: var(--mono); font-size: .64rem; letter-spacing: .05em; text-transform: uppercase;
  padding: .1rem .4rem; border-radius: 999px; border: 1px solid var(--accent); color: var(--accent-ink); }
.more { font-size: .78rem; color: var(--muted); margin: .5rem 0 0; }
.new { font-size: .8rem; color: var(--muted); margin: .4rem 0 0; }
.narr { margin: 0 0 .9rem; font-size: .93rem; }
.narr h3 { font-size: .72rem; letter-spacing: .1em; text-transform: uppercase;
  color: var(--muted); margin: .9rem 0 .3rem; font-weight: 600; }
.narr p { margin: 0 0 .6rem; }
.cite { font-family: var(--mono); font-size: .72em; color: var(--accent-ink);
  background: var(--code-bg); padding: .03em .3em; border-radius: 3px; white-space: nowrap; }
.foot { margin-top: 2rem; font-size: .74rem; color: var(--muted); font-family: var(--mono); }
"""


_CITE = re.compile(r"\[(F\d{4}(?:\s*,\s*F\d{4})*)\]")
_BOLD = re.compile(r"\*\*(.+?)\*\*")


def _inline(text):
    """Escape, then re-introduce the two inline forms the narrator uses:
    citations (kept visible — they are the provenance) and bold."""
    out = _esc(text)
    out = _CITE.sub(lambda m: '<span class="cite">%s</span>' % m.group(1), out)
    return _BOLD.sub(r"<b>\1</b>", out)


def narration_html(markdown):
    """Narrator output -> HTML. Deliberately tiny: headings, paragraphs,
    bold, citations. The narrator's contract permits nothing else, and a
    Markdown library would be a dependency for four constructs."""
    blocks, para = [], []

    def flush():
        if para:
            blocks.append("<p>%s</p>" % _inline(" ".join(para)))
            para.clear()

    for line in markdown.splitlines():
        s = line.strip()
        if not s:
            flush()
        elif s.startswith("#"):
            flush()
            blocks.append("<h3>%s</h3>" % _inline(s.lstrip("#").strip()))
        else:
            para.append(s)
    flush()
    return '<div class="narr">%s</div>' % "".join(blocks)


def _esc(v):
    return html.escape(str(v), quote=True)


def _short(iso):
    y, m, d = iso.split("-")
    return "%s %d" % (_MONTHS[int(m) - 1], int(d))


def _name(p):
    n, g = p["name"], p["group"]
    if g and n.startswith(g + "/"):
        return '<span class="group">%s/</span><span class="name">%s</span>' % (
            _esc(g), _esc(n[len(g) + 1:]))
    return '<span class="name">%s</span>' % _esc(n)


def _row(p):
    phases = "".join('<span class="pill">%s closed</span> ' % _esc(x) for x in p["phases_closed"])
    return (
        '<tr><td>%s %s</td><td class="num">%d</td><td class="num">%d</td>'
        '<td class="num">%d</td><td class="num">%d</td><td class="num">%d</td></tr>'
        % (_name(p), phases, p["commits"], p["traces"], p["lessons"],
           p["decisions"], p["active_days"])
    )


def _week(w, narration=None):
    f = w["fleet"]
    active = [p for p in w["projects"] if p["active_days"]]
    shown, rest = active[:_TOP], active[_TOP:]
    parts = [
        '<section class="week"><div class="whead">'
        '<h2 class="wname">Week of %s — %s</h2>'
        '<span class="wdays">%d day%s collected</span></div>'
        % (_esc(_short(w["week_start"])), _esc(_short(w["week_end"])),
           w["days_covered"], "" if w["days_covered"] == 1 else "s"),
        '<div class="stats">'
        '<div class="stat"><span class="n">%d</span><span class="l">commits</span></div>'
        '<div class="stat"><span class="n">%d</span><span class="l">projects active</span></div>'
        '<div class="stat"><span class="n">%d</span><span class="l">quiet</span></div>'
        '<div class="stat"><span class="n">%d</span><span class="l">traces</span></div>'
        '<div class="stat"><span class="n">%d</span><span class="l">lessons</span></div>'
        '<div class="stat"><span class="n">%d</span><span class="l">phases closed</span></div>'
        "</div>"
        % (f["commits"], f["active_projects"], f["quiet_projects"],
           f["traces"], f["lessons"], f["phases_closed"]),
    ]
    if narration:
        parts.append(narration_html(narration))
    if shown:
        parts.append(
            "<table><thead><tr><th>Project</th><th class=\"num\">Commits</th>"
            "<th class=\"num\">Traces</th><th class=\"num\">Lessons</th>"
            "<th class=\"num\">Decisions</th><th class=\"num\">Active days</th></tr></thead><tbody>"
            + "".join(_row(p) for p in shown) + "</tbody></table>"
        )
    if rest:
        parts.append('<p class="more">and %d more active project%s: %s</p>' % (
            len(rest), "" if len(rest) == 1 else "s",
            _esc(", ".join(p["name"] for p in rest))))
    if f["new_projects"]:
        parts.append('<p class="new">New this week: %s</p>' % _esc(", ".join(f["new_projects"])))
    parts.append("</section>")
    return "".join(parts)


def render(doc, narrations=None):
    """narrations: optional {week_start: markdown} — rendered above each
    week's table when present."""
    narrations = narrations or {}
    if doc.get("schema") != SUPPORTED_SCHEMA:
        raise ValueError("rollup renderer supports %s, got %r" % (SUPPORTED_SCHEMA, doc.get("schema")))
    r = doc["range"]
    parts = [
        "<!doctype html>",
        '<html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>dispatch rollup — %s to %s</title>" % (_esc(r["start"]), _esc(r["end"])),
        "<style>%s</style></head><body><main>" % _CSS,
        '<p class="eyebrow">history rollup · weekly</p>',
        "<h1>%s → %s</h1>" % (_esc(_short(r["start"])), _esc(_short(r["end"]))),
        '<p class="lede">%d week%s reconstructed from git history — commits by committer '
        "date, traces by the commit that added them, lessons by their recorded date, "
        "phases by their close markers.</p>"
        % (len(doc["weeks"]), "" if len(doc["weeks"]) == 1 else "s"),
    ]
    if doc.get("limits"):
        parts.append('<div class="limits"><b>Not recoverable from history:</b> %s</div>' % _esc(
            "; ".join("%s — %s" % (k, v) for k, v in sorted(doc["limits"].items()))))
    parts.extend(_week(w, narrations.get(w["week_start"])) for w in doc["weeks"])
    parts.append('<p class="foot">rendered deterministically from %s</p>' % _esc(SUPPORTED_SCHEMA))
    parts.append("</main></body></html>")
    return "\n".join(parts) + "\n"
