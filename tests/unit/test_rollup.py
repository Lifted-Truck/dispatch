"""E5 rollup tests: ISO-week bucketing, counts, and a golden render."""

import json
import os

from conftest import FIXTURES
from dispatch import rollup, rollup_render

GOLDEN = os.path.join(FIXTURES, "..", "golden")


def _day(date, projects):
    seq = [0]

    def fact(name, kind, data=None):
        seq[0] += 1
        return {"id": "F%04d" % seq[0], "project": name, "kind": kind,
                "data": data or {}, "source": "inferred", "evidence": "git log (backfill)"}

    recs = []
    for name, kinds in projects.items():
        fs = [fact(name, k, d) for k, d in kinds] or [fact(name, "quiet")]
        recs.append({"name": name, "group": "worlds" if "/" in name else None,
                     "public": False, "source": "inferred", "status_surface": "absent",
                     "surfaces": {}, "quiet": all(f["kind"] == "quiet" for f in fs), "facts": fs})
    return {"schema": "dispatch-facts.1", "date": date,
            "quiet_day": all(r["quiet"] for r in recs), "projects": recs}


def _docs():
    return [
        _day("2026-06-02", {"alpha": [("commit", {"hash": "a1", "subject": "x"})] * 3
                            + [("trace", {"file": "t.md"})],
                            "worlds/beta": [], "gamma": []}),
        _day("2026-06-06", {"alpha": [("commits_truncated", {"dropped": 7, "cap": 50})],
                            "worlds/beta": [("lesson", {"id": "L0001"})], "gamma": []}),
        _day("2026-06-09", {"alpha": [], "worlds/beta": [("phase", {"id": "B1", "title": "T"}),
                                                          ("decision", {"number": "2"})],
                            "gamma": []}),
    ]


def test_week_bounds_are_iso_weeks():
    assert rollup.week_bounds("2026-06-03") == ("2026-06-01", "2026-06-07")  # Wed -> Mon..Sun
    assert rollup.week_bounds("2026-06-07") == ("2026-06-01", "2026-06-07")  # Sunday stays
    assert rollup.week_bounds("2026-06-08") == ("2026-06-08", "2026-06-14")


def test_counts_and_ordering():
    doc = rollup.build(_docs(), first_commit={"gamma": "2026-06-10", "alpha": "2026-05-01"})
    assert [w["week_start"] for w in doc["weeks"]] == ["2026-06-01", "2026-06-08"]
    w1, w2 = doc["weeks"]
    assert w1["days_covered"] == 2 and w2["days_covered"] == 1
    alpha = next(p for p in w1["projects"] if p["name"] == "alpha")
    assert alpha["commits"] == 10 and alpha["traces"] == 1 and alpha["active_days"] == 2
    assert w1["fleet"]["active_projects"] == 2 and w1["fleet"]["quiet_projects"] == 1
    assert w1["projects"][0]["name"] == "alpha"  # most commits first
    beta2 = next(p for p in w2["projects"] if p["name"] == "worlds/beta")
    assert beta2["phases_closed"] == ["B1"] and beta2["decisions"] == 1
    assert w2["fleet"]["new_projects"] == ["gamma"]
    assert doc["range"] == {"start": "2026-06-01", "end": "2026-06-14"}


def test_build_is_pure():
    assert rollup.build(_docs()) == rollup.build(_docs())


def test_golden_rollup_render_byte_stable():
    with open(os.path.join(FIXTURES, "rollups", "fixture-rollup.json")) as f:
        doc = json.load(f)
    with open(os.path.join(GOLDEN, "fixture-rollup.html"), encoding="utf-8") as f:
        golden = f.read()
    page = rollup_render.render(doc)
    assert page == golden
    assert "<script" not in page and "http" not in page
    assert "Not recoverable" in page


def test_wrong_schema_refused():
    try:
        rollup_render.render({"schema": "dispatch-facts.1"})
    except ValueError as exc:
        assert "dispatch-rollup.1" in str(exc)
    else:
        raise AssertionError("wrong schema was not refused")


def test_narration_renders_above_week_table():
    with open(os.path.join(FIXTURES, "rollups", "fixture-rollup.json")) as f:
        doc = json.load(f)
    md = "## Shipped\n\nAlpha landed the **core** [F0001, F0004].\nBeta went <quiet> [F0009].\n"
    page = rollup_render.render(doc, {"2026-06-01": md})
    assert '<div class="narr">' in page
    assert "<h3>Shipped</h3>" in page
    assert '<span class="cite">F0001, F0004</span>' in page
    assert "<b>core</b>" in page
    assert "&lt;quiet&gt;" in page and "<quiet>" not in page
    # only the week that has a narration gets one
    assert page.count('<div class="narr">') == 1
    # and a render with no narrations is unchanged (golden still holds)
    with open(os.path.join(GOLDEN, "fixture-rollup.html"), encoding="utf-8") as f:
        assert rollup_render.render(doc) == f.read()
