"""Weekly rollup (E5) — pure: per-day FACTS documents -> `dispatch-rollup.1`.

Weeks are ISO weeks (Monday..Sunday) so the bucketing is a function of the
date alone. Counts come only from fact records that are present; a week's
"active" project is one with any non-quiet fact. No clock, no IO.
"""

import collections
import datetime

SCHEMA = "dispatch-rollup.1"

_COUNTED = ("commit", "trace", "lesson", "decision")


def week_bounds(date):
    """(monday, sunday) ISO dates of the ISO week containing `date`."""
    d = datetime.date.fromisoformat(date)
    monday = d - datetime.timedelta(days=d.weekday())
    return monday.isoformat(), (monday + datetime.timedelta(days=6)).isoformat()


def _empty_totals():
    return {"commits": 0, "traces": 0, "lessons": 0, "decisions": 0,
            "phases_closed": [], "active_days": 0}


def build(day_docs, first_commit=None, limits=None):
    """day_docs: iterable of facts documents (any order). first_commit:
    {name: date} of each project's first-ever commit, used to mark projects
    born inside a week; optional."""
    first_commit = first_commit or {}
    by_week = collections.OrderedDict()
    for doc in sorted(day_docs, key=lambda d: d["date"]):
        start, end = week_bounds(doc["date"])
        week = by_week.setdefault(start, {
            "week_start": start, "week_end": end, "days": [], "projects": {},
        })
        week["days"].append(doc["date"])
        for rec in doc["projects"]:
            tot = week["projects"].setdefault(rec["name"], dict(
                _empty_totals(), name=rec["name"], group=rec["group"]))
            active = False
            for f in rec["facts"]:
                k = f["kind"]
                if k in _COUNTED:
                    tot[k + "s"] += 1
                    active = True
                elif k == "commits_truncated":
                    tot["commits"] += int(f["data"].get("dropped", 0))
                    active = True
                elif k == "phase":
                    tot["phases_closed"].append(f["data"].get("id"))
                    active = True
                elif k != "quiet":
                    active = True
            if active:
                tot["active_days"] += 1

    weeks = []
    for start, week in by_week.items():
        projects = sorted(
            week["projects"].values(),
            key=lambda p: (-p["commits"], -p["traces"], p["name"]),
        )
        active = [p for p in projects if p["active_days"]]
        fleet = {
            "commits": sum(p["commits"] for p in projects),
            "traces": sum(p["traces"] for p in projects),
            "lessons": sum(p["lessons"] for p in projects),
            "decisions": sum(p["decisions"] for p in projects),
            "phases_closed": sum(len(p["phases_closed"]) for p in projects),
            "active_projects": len(active),
            "quiet_projects": len(projects) - len(active),
            "new_projects": sorted(
                n for n, d in first_commit.items()
                if week["week_start"] <= d <= week["week_end"]
            ),
        }
        weeks.append({
            "week_start": week["week_start"],
            "week_end": week["week_end"],
            "days_covered": len(week["days"]),
            "fleet": fleet,
            "projects": projects,
        })
    return {
        "schema": SCHEMA,
        "range": {
            "start": weeks[0]["week_start"] if weeks else None,
            "end": weeks[-1]["week_end"] if weeks else None,
        },
        "weeks": weeks,
        "limits": limits or {},
    }
