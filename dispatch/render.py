"""Deterministic digest renderer (E2): FACTS document -> self-contained
HTML page. Pure function of its input — no wall clock, no network, no
model calls; the same document always renders byte-identical output.

Every rendered item carries its fact id, so a human (and later the E3
narration checker) can trace any claim on the page back to the collected
fact. Styling is inline CSS with system font stacks only (no CDNs,
per the visual-first doctrine and the E2 gate).
"""

import html

from . import theme

SUPPORTED_SCHEMA = "dispatch-facts.1"

_MONTHS = (
    "January", "February", "March", "April", "May", "June", "July",
    "August", "September", "October", "November", "December",
)

# Render order for fact kinds within a project card.
_KIND_ORDER = (
    "phase", "verify", "commit", "commits_truncated", "trace", "decision",
    "lesson", "library", "baseline", "changed", "status_invalid",
)

_CSS = theme.TOKENS + """html { background: var(--paper); }
body { font-family: var(--sans); color: var(--ink); background: var(--paper);
  margin: 0; padding: 2.5rem 1.25rem 4rem; line-height: 1.55; }
main { max-width: 46rem; margin: 0 auto; }
.eyebrow { font-family: var(--mono); font-size: .72rem; letter-spacing: .14em;
  text-transform: uppercase; color: var(--accent); margin: 0 0 .5rem; }
h1 { font-size: 1.7rem; line-height: 1.2; margin: 0 0 1rem; font-weight: 650; }
.stats { display: flex; flex-wrap: wrap; gap: .45rem; margin: 0 0 1.8rem; }
.stat { flex: 1 1 8rem; background: var(--card); border: 1px solid var(--line);
  border-radius: 6px; padding: .55rem .75rem; }
.stat .n { font-family: var(--mono); font-size: 1.2rem; font-weight: 650;
  display: block; font-variant-numeric: tabular-nums; }
.stat .l { font-size: .72rem; color: var(--muted); }
.quietday { background: var(--card); border: 1px solid var(--line);
  border-radius: 6px; padding: 1.2rem 1.4rem; margin: 0 0 1.6rem; }
.quietday b { display: block; font-size: 1.05rem; margin-bottom: .2rem; }
.quietday span { color: var(--muted); font-size: .9rem; }
.project { background: var(--card); border: 1px solid var(--line);
  border-radius: 6px; padding: 1rem 1.2rem; margin: 0 0 .9rem; }
.phead { display: flex; flex-wrap: wrap; align-items: baseline; gap: .5rem;
  margin-bottom: .5rem; }
.pname { font-size: 1.05rem; font-weight: 650; margin: 0; }
.badge { font-family: var(--mono); font-size: .66rem; letter-spacing: .06em;
  text-transform: uppercase; padding: .14rem .45rem; border-radius: 999px;
  border: 1px solid var(--line); color: var(--muted); }
.badge.declared { color: var(--accent-ink); border-color: var(--accent); }
.badge.warn { color: var(--warn); background: var(--warn-bg); border-color: transparent; }
ul.facts { list-style: none; margin: 0; padding: 0; }
ul.facts li { padding: .28rem 0; border-top: 1px solid var(--line);
  font-size: .9rem; display: flex; gap: .6rem; align-items: baseline; }
ul.facts li:first-child { border-top: none; }
.fid { font-family: var(--mono); font-size: .66rem; color: var(--muted);
  flex: 0 0 3.2rem; }
.kind { font-family: var(--mono); font-size: .7rem; color: var(--accent);
  flex: 0 0 5.2rem; text-transform: uppercase; letter-spacing: .05em; }
.fbody { flex: 1; min-width: 0; overflow-wrap: anywhere; }
code { font-family: var(--mono); font-size: .84em; background: var(--code-bg);
  padding: .08em .3em; border-radius: 3px; }
.pass { color: var(--good); font-weight: 650; }
.fail { color: var(--bad); font-weight: 650; }
h2 { font-size: .8rem; letter-spacing: .12em; text-transform: uppercase;
  color: var(--muted); margin: 2rem 0 .8rem; font-weight: 600;
  display: flex; align-items: center; gap: .7rem; }
h2::after { content: ""; flex: 1; height: 1px; background: var(--line); }
.quietlist { display: flex; flex-wrap: wrap; gap: .4rem; }
.quietlist span { font-family: var(--mono); font-size: .74rem;
  border: 1px solid var(--line); border-radius: 999px; padding: .2rem .55rem;
  color: var(--muted); background: var(--card); }
.foot { margin-top: 2.6rem; font-size: .74rem; color: var(--muted);
  font-family: var(--mono); }
"""


def _esc(value):
    return html.escape(str(value), quote=True)


def _human_date(iso):
    year, month, day = iso.split("-")
    return "%s %d, %s" % (_MONTHS[int(month) - 1], int(day), year)


def _fact_body(fact):
    kind, data = fact["kind"], fact["data"]
    if kind == "phase":
        return "<b>%s</b> — %s" % (_esc(data.get("id", "?")), _esc(data.get("title", "")))
    if kind == "verify":
        state = (
            '<span class="pass">green</span>'
            if data.get("exit") == 0
            else '<span class="fail">red (exit %s)</span>' % _esc(data.get("exit"))
        )
        return "verify <code>%s</code> %s at <code>%s</code>" % (
            _esc(data.get("target", "?")), state, _esc(data.get("git", "?")),
        )
    if kind == "commit":
        return "<code>%s</code> %s" % (_esc(data.get("hash", "?")), _esc(data.get("subject", "")))
    if kind == "commits_truncated":
        return "…and %s more commits beyond the %s-commit window" % (
            _esc(data.get("dropped", "?")), _esc(data.get("cap", "?")),
        )
    if kind == "trace":
        return "trace <code>%s</code>" % _esc(data.get("file", "?"))
    if kind == "decision":
        return "decision #%s recorded" % _esc(data.get("number", "?"))
    if kind == "lesson":
        return "lesson <code>%s</code>" % _esc(data.get("id", "?"))
    if kind == "library":
        return "LIBRARY.md changed"
    if kind == "baseline":
        return "first sighting — baseline: %s traces, %s decisions on record" % (
            _esc(data.get("traces", 0)), _esc(data.get("decisions", 0)),
        )
    if kind == "status_invalid":
        return "STATUS.json present but off-contract: %s" % _esc(
            "; ".join(data.get("errors", [])) or "unspecified"
        )
    if kind == "changed":
        return "activity fingerprint changed (%s)" % _esc(data.get("detail", ""))
    return _esc(data)


def _project_card(record):
    badges = ['<span class="badge %s">%s</span>' % (
        "declared" if record["source"] == "declared" else "", _esc(record["source"]))]
    if record["status_surface"] == "invalid":
        badges.append('<span class="badge warn">status off-contract</span>')
    badges.append(
        '<span class="badge">%s</span>' % ("public" if record["public"] else "private")
    )
    grouped = sorted(
        record["facts"],
        key=lambda f: (_KIND_ORDER.index(f["kind"])
                       if f["kind"] in _KIND_ORDER else len(_KIND_ORDER)),
    )
    items = []
    for fact in grouped:
        items.append(
            '<li><span class="fid">%s</span><span class="kind">%s</span>'
            '<span class="fbody">%s</span></li>'
            % (_esc(fact["id"]), _esc(fact["kind"]), _fact_body(fact))
        )
    return (
        '<article class="project"><div class="phead">'
        '<h3 class="pname">%s</h3>%s</div><ul class="facts">%s</ul></article>'
        % (_esc(record["name"]), "".join(badges), "".join(items))
    )


def render(doc):
    """FACTS document (dict) -> complete self-contained HTML page (str)."""
    if doc.get("schema") != SUPPORTED_SCHEMA:
        raise ValueError(
            "renderer supports %s, got %r" % (SUPPORTED_SCHEMA, doc.get("schema"))
        )
    date = doc["date"]
    projects = doc["projects"]
    active = [p for p in projects if not p["quiet"]]
    quiet = [p for p in projects if p["quiet"]]
    total_facts = sum(len(p["facts"]) for p in projects)

    parts = [
        "<!doctype html>",
        '<html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>dispatch — %s</title>" % _esc(date),
        "<style>%s</style></head><body><main>" % _CSS,
        '<p class="eyebrow">daily dispatch · deterministic digest</p>',
        "<h1>%s</h1>" % _esc(_human_date(date)),
        '<div class="stats">'
        '<div class="stat"><span class="n">%d</span><span class="l">projects active</span></div>'
        '<div class="stat"><span class="n">%d</span><span class="l">projects quiet</span></div>'
        '<div class="stat"><span class="n">%d</span><span class="l">facts collected</span></div>'
        "</div>" % (len(active), len(quiet), total_facts),
    ]

    if doc["quiet_day"]:
        parts.append(
            '<div class="quietday"><b>A quiet day, on the record.</b>'
            "<span>All %d watched projects were collected and none changed "
            "— an explicit finding, not an absence.</span></div>" % len(projects)
        )

    if active:
        parts.append("<h2>Activity</h2>")
        parts.extend(_project_card(p) for p in active)

    if quiet:
        parts.append("<h2>Quiet — collected, unchanged</h2>")
        parts.append(
            '<div class="quietlist">%s</div>'
            % "".join("<span>%s</span>" % _esc(p["name"]) for p in quiet)
        )

    parts.append(
        '<p class="foot">rendered deterministically from %s · %s · '
        "every item cites its fact id</p>" % (_esc(SUPPORTED_SCHEMA), _esc(date))
    )
    parts.append("</main></body></html>")
    return "\n".join(parts) + "\n"
