"""History backfill (E5) — the collector run BACKWARD over git history.

Live collection diffs the working tree against a ledger. A backfill has no
ledger: git history IS the record, so each past day is reconstructed from
what git can date exactly — commits (committer date), traces (the commit that
added the file), lessons (`added:` in LIBRARY.md), phase closures (`CLOSED`
markers in ROADMAP.md), and dated decision entries.

Deterministic: one `git log` per repo per source (never one per day), no
wall clock, stable ordering. Same history in -> byte-identical documents out.

What history cannot give is left OUT and NAMED (see LIMITS), never
approximated: `.harness/` is untracked, so no past verify result exists;
no project has ever emitted a STATUS surface, so every backfilled fact is
`inferred`. Output documents are ordinary `dispatch-facts.1` so every
downstream stage consumes them unchanged (decision 14); provenance rides in
each fact's `evidence` string, which always says `(backfill: ...)`.
"""

import datetime
import re

from . import facts, probe

LIMITS = {
    "verify": "not recoverable — .harness/ is untracked; no past verify result exists",
    "status_surface": "never declared — no project has emitted STATUS.json; all facts inferred",
    "roster": "today's registry — repositories removed since are invisible",
}

_LESSON = re.compile(r"^\[(L\d{4})\]")
_ADDED = re.compile(r"added:\s*(\d{4}-\d{2}-\d{2})")
_PHASE_HEAD = re.compile(r"\*\*(?:Phase\s+)?([A-Za-z]\w*)\s*—\s*(.+?)\.?\*\*")
_CLOSED = re.compile(r"\*\*CLOSED\s+(\d{4}-\d{2}-\d{2})\*\*")
_DECISION = re.compile(r"^(\d+)\.\s+\*\*.*?\((\d{4}-\d{2}-\d{2})")


def _dates(start, end):
    """Every ISO date from start to end inclusive."""
    a = datetime.date.fromisoformat(start)
    b = datetime.date.fromisoformat(end)
    if b < a:
        raise ValueError("end %s precedes start %s" % (end, start))
    out = []
    while a <= b:
        out.append(a.isoformat())
        a += datetime.timedelta(days=1)
    return out


def _next_day(date):
    return (datetime.date.fromisoformat(date) + datetime.timedelta(days=1)).isoformat()


def _in_range(date, start, end):
    return start <= date <= end


def commits_by_day(path, start, end):
    """{date: [{hash, subject}, ...]} newest-first within a day, like git log.

    %cs is the committer date in the COMMIT's own timezone, so the calendar
    day is the one the committer saw and does not shift with the machine
    running the backfill.
    """
    out = probe._git(
        path,
        ["log", "--format=%cs%x1f%h%x1f%s",
         "--since", start + "T00:00:00", "--until", _next_day(end) + "T00:00:00"],
    )
    days = {}
    for line in (out or "").split("\n"):
        if not line:
            continue
        date, _, rest = line.partition("\x1f")
        chash, _, subject = rest.partition("\x1f")
        if _in_range(date, start, end):
            days.setdefault(date, []).append({"hash": chash, "subject": subject})
    return days


def traces_by_day(path, start, end):
    """{date: [trace filenames]} dated by the commit that ADDED each file."""
    out = probe._git(
        path,
        ["log", "--diff-filter=A", "--name-only", "--format=%x1e%cs",
         "--since", start + "T00:00:00", "--until", _next_day(end) + "T00:00:00",
         "--", "traces"],
    )
    days, current = {}, None
    # split("\n"), NOT splitlines(): Python treats \x1e (the record separator
    # used as the date marker) as a line boundary, which strips the marker
    # onto its own empty line and silently dates nothing. \x1f is safe;
    # \x1c-\x1e are not.
    for line in (out or "").split("\n"):
        if line.startswith("\x1e"):
            current = line[1:].strip()
        elif line.startswith("traces/") and line.endswith(".md") and current:
            name = line[len("traces/"):]
            if name != "README.md" and _in_range(current, start, end):
                days.setdefault(current, []).append(name)
    return {d: sorted(v) for d, v in days.items()}


def lessons_by_day(path, start, end):
    """{date: [lesson ids]} from LIBRARY.md `added:` dates (single- or
    multi-line entries: fields may continue on following lines)."""
    lines = probe._read_lines(path + "/LIBRARY.md")
    days, current_id, buf = {}, None, []

    def flush():
        if current_id and buf:
            m = _ADDED.search(" ".join(buf))
            if m and _in_range(m.group(1), start, end):
                days.setdefault(m.group(1), []).append(current_id)

    for line in lines:
        m = _LESSON.match(line.strip())
        if m:
            flush()
            current_id, buf = m.group(1), [line]
        elif current_id:
            buf.append(line)
    flush()
    return {d: sorted(v) for d, v in days.items()}


def phase_closes_by_day(path, start, end):
    """{date: [{id, title}]} from `**CLOSED YYYY-MM-DD**` markers in ROADMAP.md.

    A phase bullet wraps across lines, so the entry is the span from one
    `- **` bullet to the next; the CLOSED marker anywhere in that span
    belongs to the heading that opened it.
    """
    text = "\n".join(probe._read_lines(path + "/ROADMAP.md"))
    days = {}
    for entry in re.split(r"\n(?=- \*\*)", text):
        head = _PHASE_HEAD.search(entry)
        closed = _CLOSED.search(entry)
        if head and closed and _in_range(closed.group(1), start, end):
            days.setdefault(closed.group(1), []).append(
                {"id": head.group(1), "title": head.group(2)}
            )
    return days


def decisions_by_day(path, start, end):
    """{date: [decision numbers]} for numbered entries carrying a date in
    their first line, from DECISIONS.md or the ROADMAP decisions section."""
    lines = probe._read_lines(path + "/DECISIONS.md") or probe._read_lines(
        path + "/ROADMAP.md"
    )
    days = {}
    for line in lines:
        m = _DECISION.match(line)
        if m and _in_range(m.group(2), start, end):
            days.setdefault(m.group(2), []).append(m.group(1))
    return days


def observe_range(path, start, end):
    """Every dated signal for one repo over the range, in one pass per source."""
    return {
        "commits": commits_by_day(path, start, end),
        "traces": traces_by_day(path, start, end),
        "lessons": lessons_by_day(path, start, end),
        "phases": phase_closes_by_day(path, start, end),
        "decisions": decisions_by_day(path, start, end),
    }


def _project_day(project, obs, date, seq):
    """One project's record for one past day — same shape as facts.py emits."""
    name = project["name"]

    def fact(kind, data, evidence):
        return {
            "id": seq.next(),
            "project": name,
            "kind": kind,
            "data": data,
            "source": "inferred",
            "evidence": evidence,
        }

    out = []
    for phase in obs["phases"].get(date, []):
        out.append(fact("phase", dict(phase, event="closed"),
                        "ROADMAP.md (backfill: CLOSED marker)"))
    commits = obs["commits"].get(date, [])
    for commit in commits[: probe.MAX_COMMITS]:
        out.append(fact("commit", dict(commit, basis="backfill"), "git log (backfill)"))
    if len(commits) > probe.MAX_COMMITS:
        out.append(fact("commits_truncated",
                        {"dropped": len(commits) - probe.MAX_COMMITS, "cap": probe.MAX_COMMITS},
                        "git log (backfill)"))
    for tname in obs["traces"].get(date, []):
        out.append(fact("trace", {"file": tname}, "traces/ (backfill: add-commit date)"))
    for number in obs["decisions"].get(date, []):
        out.append(fact("decision", {"number": number}, "DECISIONS.md (backfill: dated entry)"))
    for lid in obs["lessons"].get(date, []):
        out.append(fact("lesson", {"id": lid}, "LIBRARY.md (backfill: added date)"))
    if not out:
        out.append(fact("quiet", {}, "git history (backfill: no dated activity)"))
    return {
        "name": name,
        "group": project["group"],
        "public": project["public"],
        "source": "inferred",
        "status_surface": "absent",
        "surfaces": project["surfaces"],
        "quiet": all(f["kind"] == "quiet" for f in out),
        "facts": out,
    }


def build_days(projects, observations, start, end):
    """[(date, facts_doc)] for every day in the range, roster order preserved.

    `projects`: [{name, group, public, surfaces}] from the boundary;
    `observations`: {name: observe_range(...)}.
    """
    docs = []
    for date in _dates(start, end):
        seq = facts._Seq()
        records = [_project_day(p, observations[p["name"]], date, seq) for p in projects]
        docs.append((date, {
            "schema": facts.SCHEMA,
            "date": date,
            "quiet_day": all(r["quiet"] for r in records),
            "projects": records,
        }))
    return docs


def manifest(projects, start, end, heads):
    """What this backfill was computed from, and what it could not recover."""
    return {
        "schema": "dispatch-history.1",
        "range": {"start": start, "end": end},
        "projects": len(projects),
        "heads": heads,
        "limits": LIMITS,
    }
