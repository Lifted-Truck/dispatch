"""Observation-layer tests over a git fixture repo (read-only IO)."""

import datetime

from conftest import git, make_repo
from dispatch import probe, status

TODAY = datetime.date.today().isoformat()


def _hasher(path, targets):
    # stdlib stand-in for the boundary hasher: presence-keyed content marker
    import hashlib
    import os

    out = {}
    for t in targets:
        fp = os.path.join(path, t)
        if os.path.isfile(fp):
            with open(fp, "rb") as f:
                out[t] = hashlib.sha256(f.read()).hexdigest()[:16]
    return out


def test_observe_shape(tmp_path):
    repo = make_repo(tmp_path, "alpha")
    obs = probe.observe(str(repo), TODAY, None, _hasher, status.validate)
    assert obs["git_head"]
    assert obs["commits_basis"] == "since-midnight"
    assert [c["subject"] for c in obs["commits"]] == ["scaffold alpha"]
    assert obs["traces"] == ["2026-01-01-scaffold.md"]
    assert obs["decisions"] == ["1"]
    assert obs["roadmap_phase"] == {"id": "E1", "title": "Build the thing"}
    assert obs["verify"]["exit"] == 0
    assert obs["status"] == {
        "present": False,
        "valid": False,
        "errors": [],
        "doc": None,
    }
    assert "ROADMAP.md" in obs["files"]


def test_commits_since_last_run(tmp_path):
    repo = make_repo(tmp_path, "alpha")
    first = probe.observe(str(repo), TODAY, None, _hasher, status.validate)
    (repo / "new.txt").write_text("x\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "second commit")
    obs = probe.observe(
        str(repo), TODAY, probe.ledger_entry(first), _hasher, status.validate
    )
    assert obs["commits_basis"] == "since-last-run"
    assert [c["subject"] for c in obs["commits"]] == ["second commit"]


def test_non_git_dir(tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    obs = probe.observe(str(plain), TODAY, None, _hasher, status.validate)
    assert obs["git_head"] is None
    assert obs["commits"] == []
    assert obs["traces"] is None
    assert obs["decisions"] is None


def test_roadmap_phase_marker_on_wrapped_line(tmp_path):
    repo = make_repo(tmp_path, "alpha")
    (repo / "ROADMAP.md").write_text(
        "# r\n\n"
        "- **E0 — Charter.** done. **CLOSED**\n"
        "- **E1 — Registry + collector (deterministic).** Long bullet that\n"
        "  wraps across several lines before the marker appears.\n"
        "  *Gate: things.* **← current phase**\n"
        "- **E2 — Renderer.** later.\n"
    )
    assert probe.read_roadmap_phase(str(repo)) == {
        "id": "E1",
        "title": "Registry + collector (deterministic)",
    }


def test_roadmap_phase_with_phase_word_prefix(tmp_path):
    # autonomous spells ids as `**Phase C0 — ...**`; the prefix is stripped so
    # the id matches the bare-id convention used elsewhere.
    repo = make_repo(tmp_path, "alpha")
    (repo / "ROADMAP.md").write_text(
        "# r\n\n"
        "- **Phase C0 — Consolidation.** Pull the corpus in.\n"
        "  *Gate: dedup sweep clean.* **← current phase**\n"
        "- **Phase P0 — Enforcement floor.** Later.\n"
    )
    assert probe.read_roadmap_phase(str(repo)) == {
        "id": "C0",
        "title": "Consolidation",
    }


def test_decisions_from_decisions_md(tmp_path):
    repo = make_repo(tmp_path, "alpha")
    (repo / "DECISIONS.md").write_text("# d\n\n1. One.\n2. Two.\n")
    assert probe.read_decisions(str(repo)) == ["1", "2"]


def test_status_surface_read(tmp_path):
    repo = make_repo(tmp_path, "alpha")
    (repo / "STATUS.json").write_text(
        '{"schema": "status.1", "project": "alpha", '
        '"ts": "2026-07-10T00:00:00Z", "quiet": true}\n'
    )
    obs = probe.observe(str(repo), TODAY, None, _hasher, status.validate)
    assert obs["status"]["valid"] is True
    assert obs["status"]["doc"]["quiet"] is True
