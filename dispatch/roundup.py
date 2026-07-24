"""Portfolio board renderer (E2b) — snapshot document -> self-contained HTML.

Pure function of its input, like the digest renderer: no clock, no network,
no model calls. This page is a UI, not a document — it is scanned, so state
is encoded in form (severity pills) as well as in text, and the summary
reads before the detail.
"""

import html

from . import theme

SUPPORTED_SCHEMA = "dispatch-snapshot.1"

_MONTHS = (
    "January", "February", "March", "April", "May", "June", "July",
    "August", "September", "October", "November", "December",
)

_STALE_LABEL = {
    "active": "active",
    "recent": "recent",
    "idle": "idle",
    "stale": "stale",
    "unknown": "no commits",
}

_CSS = theme.TOKENS + """html { background: var(--paper); }
body { font-family: var(--sans); color: var(--ink); background: var(--paper);
  margin: 0; padding: 2.5rem 1.25rem 4rem; line-height: 1.5; }
main { max-width: 60rem; margin: 0 auto; }
.eyebrow { font-family: var(--mono); font-size: .72rem; letter-spacing: .14em;
  text-transform: uppercase; color: var(--accent); margin: 0 0 .5rem; }
h1 { font-size: 1.7rem; line-height: 1.2; margin: 0 0 .3rem; font-weight: 650; }
.lede { color: var(--muted); margin: 0 0 1.5rem; max-width: 40rem; font-size: .92rem; }
.stats { display: flex; flex-wrap: wrap; gap: .45rem; margin: 0 0 1.6rem; }
.stat { flex: 1 1 7rem; background: var(--card); border: 1px solid var(--line);
  border-radius: 6px; padding: .55rem .75rem; }
.stat .n { font-family: var(--mono); font-size: 1.2rem; font-weight: 650;
  display: block; font-variant-numeric: tabular-nums; }
.stat .l { font-size: .7rem; color: var(--muted); }
.stat.green .n { color: var(--good); }
.stat.red .n { color: var(--bad); }
.tablewrap { overflow-x: auto; background: var(--card); border: 1px solid var(--line);
  border-radius: 6px; }
table { border-collapse: collapse; width: 100%; font-size: .87rem;
  font-variant-numeric: tabular-nums; }
th, td { text-align: left; padding: .5rem .7rem; border-top: 1px solid var(--line);
  vertical-align: middle; white-space: nowrap; }
thead th { border-top: none; font-size: .68rem; text-transform: uppercase;
  letter-spacing: .08em; color: var(--muted); font-weight: 600; }
tbody tr:first-child td { border-top: 1px solid var(--line); }
.name { font-weight: 600; }
.group { color: var(--muted); font-weight: 400; }
.phase { font-family: var(--mono); font-size: .78rem; }
.phase b { color: var(--accent-ink); }
.dash { color: var(--muted); }
.pill { font-family: var(--mono); font-size: .66rem; letter-spacing: .05em;
  text-transform: uppercase; padding: .14rem .45rem; border-radius: 999px;
  border: 1px solid var(--line); color: var(--muted); display: inline-block; }
.pill.green { color: var(--good); background: var(--good-bg); border-color: transparent; }
.pill.red { color: var(--bad); background: var(--bad-bg); border-color: transparent; }
.pill.warn { color: var(--warn); background: var(--warn-bg); border-color: transparent; }
.pill.declared { color: var(--accent-ink); border-color: var(--accent); }
.age { font-family: var(--mono); font-size: .78rem; }
.age.active { color: var(--good); }
.age.recent { color: var(--ink); }
.age.idle { color: var(--warn); }
.age.stale { color: var(--bad); font-weight: 650; }
.age.unknown { color: var(--muted); }
.harness { font-family: var(--mono); font-size: .68rem; color: var(--muted); }
.foot { margin-top: 2rem; font-size: .74rem; color: var(--muted);
  font-family: var(--mono); }
"""


def _esc(value):
    return html.escape(str(value), quote=True)


def _human_date(iso):
    year, month, day = iso.split("-")
    return "%s %d, %s" % (_MONTHS[int(month) - 1], int(day), year)


def _age_cell(record):
    days, bucket = record["stale_days"], record["staleness"]
    if days is None:
        label = "—"
    elif days == 0:
        label = "today"
    else:
        label = "%dd" % days
    return '<span class="age %s">%s</span>' % (_esc(bucket), _esc(label))


def _phase_cell(record):
    phase = record["phase"]
    if not phase:
        return '<span class="dash">no roadmap phase</span>'
    gate = ""
    if phase.get("gate_state"):
        cls = "green" if phase["gate_state"] == "green" else ""
        gate = ' <span class="pill %s">%s</span>' % (cls, _esc(phase["gate_state"]))
    return '<span class="phase"><b>%s</b> %s</span>%s' % (
        _esc(phase.get("id") or "?"), _esc(phase.get("title") or ""), gate,
    )


def _verify_cell(record):
    verify = record["verify"]
    if not verify:
        return '<span class="dash">never run</span>'
    cls = "green" if verify["state"] == "green" else "red"
    return '<span class="pill %s">%s %s</span>' % (
        cls, _esc(verify.get("target") or "?"), _esc(verify["state"]),
    )


def _name_cell(record):
    name, group = record["name"], record["group"]
    if group and name.startswith(group + "/"):
        return '<span class="group">%s/</span><span class="name">%s</span>' % (
            _esc(group), _esc(name[len(group) + 1:]),
        )
    return '<span class="name">%s</span>' % _esc(name)


def _row(record):
    source_cls = "declared" if record["source"] == "declared" else ""
    source = '<span class="pill %s">%s</span>' % (source_cls, _esc(record["source"]))
    if record["status_surface"] == "invalid":
        source += ' <span class="pill warn">off-contract</span>'
    return (
        "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
        '<td class="harness">%s</td></tr>'
        % (
            _name_cell(record),
            _phase_cell(record),
            _verify_cell(record),
            _age_cell(record),
            source,
            _esc(", ".join(record["harness"])) or "—",
        )
    )


def render(doc):
    """Snapshot document (dict) -> complete self-contained HTML page (str)."""
    if doc.get("schema") != SUPPORTED_SCHEMA:
        raise ValueError(
            "roundup supports %s, got %r" % (SUPPORTED_SCHEMA, doc.get("schema"))
        )
    summary, projects = doc["summary"], doc["projects"]
    parts = [
        "<!doctype html>",
        '<html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>dispatch roundup — %s</title>" % _esc(doc["date"]),
        "<style>%s</style></head><body><main>" % _CSS,
        '<p class="eyebrow">roadmap roundup · portfolio board</p>',
        "<h1>Where every project stands</h1>",
        '<p class="lede">State of all %d watched projects as of %s — a standing '
        "snapshot, not a daily delta, so a project parked on the same phase for "
        "a month still appears.</p>"
        % (summary["projects"], _esc(_human_date(doc["date"]))),
        '<div class="stats">'
        '<div class="stat"><span class="n">%d</span><span class="l">projects watched</span></div>'
        '<div class="stat"><span class="n">%d</span><span class="l">with a roadmap phase</span></div>'
        '<div class="stat green"><span class="n">%d</span><span class="l">verify green</span></div>'
        '<div class="stat red"><span class="n">%d</span><span class="l">verify red</span></div>'
        '<div class="stat"><span class="n">%d</span><span class="l">declared status surface</span></div>'
        '<div class="stat"><span class="n">%d</span><span class="l">stale &gt; 30d</span></div>'
        "</div>"
        % (
            summary["projects"], summary["phase_known"], summary["verify_green"],
            summary["verify_red"], summary["declared"], summary["stale"],
        ),
        '<div class="tablewrap"><table><thead><tr>'
        "<th>Project</th><th>Roadmap phase</th><th>Last verify</th>"
        "<th>Last commit</th><th>Facts</th><th>Harness</th>"
        "</tr></thead><tbody>",
    ]
    parts.extend(_row(r) for r in projects)
    parts.append("</tbody></table></div>")
    parts.append(
        '<p class="foot">rendered deterministically from %s · %s · '
        "freshest first</p>" % (_esc(SUPPORTED_SCHEMA), _esc(doc["date"]))
    )
    parts.append("</main></body></html>")
    return "\n".join(parts) + "\n"
