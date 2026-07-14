"""Pure facts-assembly tests — no IO, observations constructed by hand."""

from dispatch import facts, probe


def _obs(**kw):
    base = {
        "git_head": "aaa111",
        "commits": [],
        "commits_basis": "since-last-run",
        "commits_dropped": 0,
        "traces": ["t1.md"],
        "decisions": ["1"],
        "roadmap_phase": {"id": "E1", "title": "Build"},
        "verify": {"target": "fast", "exit": 0, "git": "aaa111", "ts": "T"},
        "status": {"present": False, "valid": False, "errors": [], "doc": None},
        "files": {"ROADMAP.md": "h1", ".harness/last-verify.json": "h2"},
    }
    base.update(kw)
    return base


def _project(obs, name="p"):
    return {
        "name": name,
        "path": "/x/" + name,
        "group": None,
        "public": False,
        "surfaces": {"git": True},
        "obs": obs,
    }


def _kinds(record):
    return [f["kind"] for f in record["facts"]]


def test_baseline_first_sighting():
    doc = facts.build("2026-07-10", [_project(_obs())], {})
    rec = doc["projects"][0]
    assert rec["quiet"] is False
    assert rec["source"] == "inferred"
    assert _kinds(rec) == ["phase", "verify", "baseline"]
    assert doc["quiet_day"] is False


def test_quiet_when_fingerprint_unchanged():
    obs = _obs()
    prev = probe.ledger_entry(obs)
    doc = facts.build("2026-07-10", [_project(obs)], {"p": prev})
    rec = doc["projects"][0]
    assert rec["quiet"] is True
    assert _kinds(rec) == ["quiet"]
    assert doc["quiet_day"] is True


def test_inferred_delta_commit_and_trace():
    obs = _obs(
        git_head="bbb222",
        commits=[{"hash": "bbb222", "subject": "fix"}],
        traces=["t1.md", "t2.md"],
        decisions=["1", "2"],
    )
    prev = {
        "git_head": "aaa111",
        "files": {"ROADMAP.md": "h1", ".harness/last-verify.json": "h2"},
        "traces": ["t1.md"],
        "decisions": ["1"],
    }
    doc = facts.build("2026-07-10", [_project(obs)], {"p": prev})
    rec = doc["projects"][0]
    assert _kinds(rec) == ["commit", "trace", "decision"]
    trace_fact = rec["facts"][1]
    assert trace_fact["data"] == {"file": "t2.md"}
    assert all(f["source"] == "inferred" for f in rec["facts"])


def test_phase_and_verify_facts_only_when_their_files_changed():
    obs = _obs(files={"ROADMAP.md": "h1-new", ".harness/last-verify.json": "h2"})
    prev = probe.ledger_entry(_obs())
    doc = facts.build("2026-07-10", [_project(obs)], {"p": prev})
    assert _kinds(doc["projects"][0]) == ["phase"]


def test_declared_source_lifts_status():
    status_doc = {
        "schema": "status.1",
        "project": "p",
        "ts": "2026-07-10T21:00:00Z",
        "quiet": False,
        "roadmap_phase": {"id": "D1", "title": "Stream"},
        "last_verify": {"target": "fast", "exit": 0, "git": "abc", "ts": "T"},
        "recent": {
            "commits": [{"hash": "abc", "subject": "s"}],
            "decisions": ["2"],
            "traces": ["x.md"],
            "lessons": ["L0001"],
        },
    }
    obs = _obs(
        status={"present": True, "valid": True, "errors": [], "doc": status_doc}
    )
    doc = facts.build("2026-07-10", [_project(obs)], {})
    rec = doc["projects"][0]
    assert rec["source"] == "declared"
    assert rec["status_surface"] == "declared"
    assert _kinds(rec) == ["phase", "verify", "commit", "decision", "trace", "lesson"]
    assert all(f["source"] == "declared" for f in rec["facts"])
    assert all(f["evidence"] == "STATUS.json" for f in rec["facts"])


def test_declared_quiet():
    status_doc = {
        "schema": "status.1",
        "project": "p",
        "ts": "2026-07-10T21:00:00Z",
        "quiet": True,
    }
    obs = _obs(
        status={"present": True, "valid": True, "errors": [], "doc": status_doc}
    )
    doc = facts.build("2026-07-10", [_project(obs)], {})
    rec = doc["projects"][0]
    assert rec["quiet"] is True
    assert _kinds(rec) == ["quiet"]
    assert rec["facts"][0]["source"] == "declared"


def test_invalid_status_surface_is_visible():
    obs = _obs(
        status={
            "present": True,
            "valid": False,
            "errors": ["missing required field: quiet"],
            "doc": None,
        }
    )
    doc = facts.build("2026-07-10", [_project(obs)], {})
    rec = doc["projects"][0]
    assert rec["source"] == "inferred"
    assert rec["status_surface"] == "invalid"
    assert "status_invalid" in _kinds(rec)


def test_commit_truncation_is_visible():
    obs = _obs(
        commits=[{"hash": "h%d" % i, "subject": "s"} for i in range(probe.MAX_COMMITS)],
        commits_dropped=7,
    )
    doc = facts.build("2026-07-10", [_project(obs)], {})
    kinds = _kinds(doc["projects"][0])
    assert "commits_truncated" in kinds


def test_facts_carry_no_absolute_path():
    # Regression guard (ROADMAP decision 7): the persisted FACTS artifact is
    # bound for a public remote and must never bake in an absolute filesystem
    # path. `name` is the portable identifier; no `path` key, no leaked root.
    observed = [_project(_obs(), "a"), _project(_obs(), "b")]
    doc = facts.build("2026-07-10", observed, {})
    for rec in doc["projects"]:
        assert "path" not in rec
        assert rec["name"] in ("a", "b")
    blob = facts.serialize(doc)
    assert "/x/" not in blob  # the fake absolute path fed via _project
    assert "/Users/" not in blob
    assert "/home/" not in blob


def test_fact_ids_globally_sequential_and_serialization_stable():
    observed = [_project(_obs(), "a"), _project(_obs(), "b")]
    doc = facts.build("2026-07-10", observed, {})
    ids = [f["id"] for rec in doc["projects"] for f in rec["facts"]]
    assert ids == ["F%04d" % i for i in range(1, len(ids) + 1)]
    doc2 = facts.build("2026-07-10", observed, {})
    assert facts.serialize(doc) == facts.serialize(doc2)
