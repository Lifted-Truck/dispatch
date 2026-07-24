"""Snapshot assembly tests (E2b) — pure, observations constructed by hand."""

from dispatch import snapshot


def _obs(**kw):
    base = {
        "git_head": "aaa111",
        "last_commit_date": "2026-07-10",
        "commits": [],
        "commits_basis": "since-last-run",
        "commits_dropped": 0,
        "traces": ["t1.md"],
        "decisions": ["1"],
        "roadmap_phase": {"id": "E1", "title": "Build"},
        "verify": {"target": "fast", "exit": 0, "git": "aaa111", "ts": "T"},
        "status": {"present": False, "valid": False, "errors": [], "doc": None},
        "files": {},
    }
    base.update(kw)
    return base


def _project(obs, name="p", group=None, surfaces=None):
    return {
        "name": name,
        "group": group,
        "public": False,
        "surfaces": surfaces or {"git": True, "verify": True, "library": False},
        "obs": obs,
    }


def test_every_project_appears_exactly_once():
    observed = [_project(_obs(), n) for n in ("a", "b", "c")]
    doc = snapshot.build("2026-07-10", observed)
    names = [p["name"] for p in doc["projects"]]
    assert sorted(names) == ["a", "b", "c"]
    assert len(names) == len(set(names))
    assert doc["summary"]["projects"] == 3


def test_phase_reported_even_when_unchanged():
    # The point of the board: FACTS would emit nothing for a parked project.
    doc = snapshot.build("2026-07-10", [_project(_obs())])
    assert doc["projects"][0]["phase"] == {"id": "E1", "title": "Build"}


def test_staleness_from_collection_date_not_clock():
    fresh = _project(_obs(last_commit_date="2026-07-10"), "fresh")
    idle = _project(_obs(last_commit_date="2026-06-25"), "idle")
    old = _project(_obs(last_commit_date="2026-01-01"), "old")
    doc = snapshot.build("2026-07-10", [fresh, idle, old])
    by = {p["name"]: p for p in doc["projects"]}
    assert (by["fresh"]["stale_days"], by["fresh"]["staleness"]) == (0, "active")
    assert (by["idle"]["stale_days"], by["idle"]["staleness"]) == (15, "idle")
    assert by["old"]["staleness"] == "stale"
    assert doc["summary"]["stale"] == 1


def test_no_git_is_unknown_not_zero():
    doc = snapshot.build("2026-07-10", [_project(_obs(last_commit_date=None))])
    rec = doc["projects"][0]
    assert rec["stale_days"] is None
    assert rec["staleness"] == "unknown"


def test_future_commit_date_clamped():
    doc = snapshot.build("2026-07-10", [_project(_obs(last_commit_date="2026-07-20"))])
    assert doc["projects"][0]["stale_days"] == 0


def test_freshest_first_unknown_last():
    observed = [
        _project(_obs(last_commit_date=None), "nogit"),
        _project(_obs(last_commit_date="2026-06-01"), "old"),
        _project(_obs(last_commit_date="2026-07-10"), "new"),
    ]
    doc = snapshot.build("2026-07-10", observed)
    assert [p["name"] for p in doc["projects"]] == ["new", "old", "nogit"]


def test_declared_status_wins_over_inferred():
    status_doc = {
        "schema": "status.1",
        "project": "p",
        "ts": "2026-07-10T21:00:00Z",
        "quiet": False,
        "roadmap_phase": {"id": "D9", "title": "Declared phase", "gate_state": "green"},
        "last_verify": {"target": "full", "exit": 1, "git": "zzz", "ts": "T"},
    }
    obs = _obs(status={"present": True, "valid": True, "errors": [], "doc": status_doc})
    doc = snapshot.build("2026-07-10", [_project(obs)])
    rec = doc["projects"][0]
    assert rec["source"] == "declared"
    assert rec["status_surface"] == "declared"
    assert rec["phase"] == {"id": "D9", "title": "Declared phase", "gate_state": "green"}
    assert rec["verify"]["state"] == "red"
    assert doc["summary"]["verify_red"] == 1


def test_invalid_status_falls_back_and_is_visible():
    obs = _obs(status={"present": True, "valid": False, "errors": ["bad"], "doc": None})
    rec = snapshot.build("2026-07-10", [_project(obs)])["projects"][0]
    assert rec["source"] == "inferred"
    assert rec["status_surface"] == "invalid"
    assert rec["phase"] == {"id": "E1", "title": "Build"}  # inferred fallback


def test_missing_phase_and_verify_are_none_not_invented():
    obs = _obs(roadmap_phase=None, verify=None)
    rec = snapshot.build("2026-07-10", [_project(obs)])["projects"][0]
    assert rec["phase"] is None
    assert rec["verify"] is None


def test_harness_surfaces_listed():
    rec = snapshot.build("2026-07-10", [_project(_obs())])["projects"][0]
    assert rec["harness"] == ["git", "verify"]  # library=False omitted


def test_build_is_pure():
    observed = [_project(_obs(), "a"), _project(_obs(), "b")]
    assert snapshot.build("2026-07-10", observed) == snapshot.build("2026-07-10", observed)
