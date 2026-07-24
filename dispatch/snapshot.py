"""Snapshot assembly (E2b) — the portfolio view: current state of EVERY
watched project, whether or not it moved today.

This is the deliberate counterpart to FACTS. FACTS are a *delta* (a phase
appears only when it changes), which is right for a daily digest and wrong
for a standing board — a project that has been parked on the same phase for
a month emits no phase fact at all. So the same observations are rendered a
second way: one collector, two renderings.

Pure functions of (date, observations). Staleness is computed from the
collection date, never the wall clock, so a snapshot replays identically.
"""

import datetime

SCHEMA = "dispatch-snapshot.1"

# Staleness buckets, in days since the last commit. Ordered; first match wins.
_BUCKETS = (
    (1, "active"),
    (7, "recent"),
    (30, "idle"),
)
_STALE = "stale"
_UNKNOWN = "unknown"


def build(date, observed):
    """observed: [{name, group, public, surfaces, obs}] -> snapshot document."""
    projects = [_record(p, date) for p in observed]
    # Freshest first: a board is scanned for what is moving and what is
    # rotting. Unknown-activity projects sort last; name breaks ties so the
    # ordering is total and the golden render is stable.
    projects.sort(key=lambda r: (r["stale_days"] is None, r["stale_days"] or 0, r["name"]))
    return {
        "schema": SCHEMA,
        "date": date,
        "summary": _summary(projects),
        "projects": projects,
    }


def _days_between(start, end):
    """Whole days from `start` to `end` (both YYYY-MM-DD); None if unparseable.

    Clamped at 0: collecting for a past date must not report negative age.
    """
    try:
        a = datetime.date.fromisoformat(start)
        b = datetime.date.fromisoformat(end)
    except (TypeError, ValueError):
        return None
    return max(0, (b - a).days)


def _bucket(days):
    if days is None:
        return _UNKNOWN
    for limit, name in _BUCKETS:
        if days <= limit:
            return name
    return _STALE


def _record(project, date):
    obs = project["obs"]
    status = obs["status"]
    declared = status["valid"]
    doc = status["doc"] if declared else None

    phase = (doc.get("roadmap_phase") if doc else None) or obs["roadmap_phase"]
    verify = (doc.get("last_verify") if doc else None) or obs["verify"]
    stale_days = _days_between(obs["last_commit_date"], date)

    return {
        "name": project["name"],
        "group": project["group"],
        "public": project["public"],
        "source": "declared" if declared else "inferred",
        "status_surface": "declared" if declared else (
            "invalid" if status["present"] else "absent"
        ),
        "phase": _phase(phase),
        "verify": _verify(verify),
        "stale_days": stale_days,
        "staleness": _bucket(stale_days),
        "harness": _harness(project["surfaces"]),
    }


def _phase(phase):
    if not phase:
        return None
    out = {"id": phase.get("id"), "title": phase.get("title")}
    if phase.get("gate_state"):
        out["gate_state"] = phase["gate_state"]
    return out


def _verify(verify):
    if not verify:
        return None
    return {
        "target": verify.get("target"),
        "exit": verify.get("exit"),
        "git": verify.get("git"),
        "state": "green" if verify.get("exit") == 0 else "red",
    }


def _harness(surfaces):
    """Which harness surfaces the project actually exposes (retrofit chore
    visibility — un-normalized projects are watched, never hidden)."""
    return sorted(k for k, present in surfaces.items() if present)


def _summary(projects):
    return {
        "projects": len(projects),
        "declared": sum(1 for p in projects if p["source"] == "declared"),
        "phase_known": sum(1 for p in projects if p["phase"]),
        "verify_green": sum(1 for p in projects if (p["verify"] or {}).get("state") == "green"),
        "verify_red": sum(1 for p in projects if (p["verify"] or {}).get("state") == "red"),
        "verify_unknown": sum(1 for p in projects if not p["verify"]),
        "stale": sum(1 for p in projects if p["staleness"] == _STALE),
    }
