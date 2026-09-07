"""E5 gate tests: backfill replays byte-identical; commit totals reconcile
to an independent git count (shown + truncated == total); no verify fact
ever appears in a backfilled day; quiet days are explicit."""

import json
import os
import subprocess

from dispatch import facts, history, probe

START, END = "2026-06-01", "2026-06-14"


def _git_dated(path, date, *args):
    env = dict(os.environ, GIT_AUTHOR_DATE=date + "T12:00:00+0000",
               GIT_COMMITTER_DATE=date + "T12:00:00+0000")
    subprocess.run(
        ["git", "-C", str(path), "-c", "user.name=t", "-c", "user.email=t@example.com"] + list(args),
        check=True, capture_output=True, env=env)


def _commit(path, date, msg, files):
    for name, body in files.items():
        (path / name).parent.mkdir(parents=True, exist_ok=True)
        (path / name).write_text(body)
    _git_dated(path, date, "add", "-A")
    _git_dated(path, date, "commit", "-q", "-m", msg)


def _repo(tmp_path, name="alpha"):
    p = tmp_path / name
    p.mkdir()
    _git_dated(p, "2026-05-20", "init", "-q")
    _commit(p, "2026-05-20", "before range", {"README.md": "r\n"})
    _commit(p, "2026-06-03", "first in range", {"a.txt": "1\n"})
    _commit(p, "2026-06-03", "second same day", {"a.txt": "2\n"})
    _commit(p, "2026-06-05", "add a trace", {"traces/2026-06-05-thing.md": "t\n"})
    _commit(p, "2026-06-10", "close a phase", {
        "ROADMAP.md": "# r\n\n- **E1 — Build.** done. **CLOSED 2026-06-10**\n"
                      "- **E2 — Next.** work. **← current phase**\n\n"
                      "## Decisions on record\n\n1. **Thing** (2026-06-04): x.\n",
        "LIBRARY.md": "# L\n\n[L0001] One | candidate | added: 2026-06-07 | tags: a | lesson: x | evidence: y | falsifier: z | supersedes: —\n"
                      "[L0002] Two\n| tier: candidate | added: 2026-06-12\n| lesson: multi-line\n",
    })
    _commit(p, "2026-06-20", "after range", {"b.txt": "1\n"})
    return p


def _project(p):
    return {"name": p.name, "group": None, "public": False,
            "surfaces": {"git": True}, "path": str(p)}


def test_commits_bucketed_by_committer_day(tmp_path):
    p = _repo(tmp_path)
    days = history.commits_by_day(str(p), START, END)
    assert sorted(days) == ["2026-06-03", "2026-06-05", "2026-06-10"]
    assert [c["subject"] for c in days["2026-06-03"]] == ["second same day", "first in range"]
    assert "before range" not in json.dumps(days) and "after range" not in json.dumps(days)


def test_traces_dated_by_add_commit(tmp_path):
    p = _repo(tmp_path)
    assert history.traces_by_day(str(p), START, END) == {"2026-06-05": ["2026-06-05-thing.md"]}


def test_lessons_single_and_multi_line(tmp_path):
    p = _repo(tmp_path)
    assert history.lessons_by_day(str(p), START, END) == {
        "2026-06-07": ["L0001"], "2026-06-12": ["L0002"]}


def test_phase_close_and_dated_decision(tmp_path):
    p = _repo(tmp_path)
    assert history.phase_closes_by_day(str(p), START, END) == {
        "2026-06-10": [{"id": "E1", "title": "Build"}]}
    assert history.decisions_by_day(str(p), START, END) == {"2026-06-04": ["1"]}


def test_every_day_present_and_quiet_days_explicit(tmp_path):
    p = _repo(tmp_path)
    proj = _project(p)
    days = history.build_days([proj], {proj["name"]: history.observe_range(str(p), START, END)},
                              START, END)
    assert len(days) == 14
    by = dict(days)
    assert by["2026-06-01"]["quiet_day"] is True
    assert [f["kind"] for f in by["2026-06-01"]["projects"][0]["facts"]] == ["quiet"]
    assert by["2026-06-03"]["quiet_day"] is False
    kinds = [f["kind"] for f in by["2026-06-10"]["projects"][0]["facts"]]
    assert kinds[0] == "phase" and "commit" in kinds


def test_no_verify_fact_and_all_inferred(tmp_path):
    p = _repo(tmp_path)
    proj = _project(p)
    days = history.build_days([proj], {proj["name"]: history.observe_range(str(p), START, END)},
                              START, END)
    for _, doc in days:
        for rec in doc["projects"]:
            assert rec["source"] == "inferred" and rec["status_surface"] == "absent"
            for f in rec["facts"]:
                assert f["kind"] != "verify"
                assert "backfill" in f["evidence"]


def test_replay_is_byte_identical(tmp_path):
    p = _repo(tmp_path)
    proj = _project(p)

    def run():
        obs = {proj["name"]: history.observe_range(str(p), START, END)}
        return [facts.serialize(d) for _, d in history.build_days([proj], obs, START, END)]

    assert run() == run()


def test_commit_totals_reconcile_to_independent_git_count(tmp_path):
    # Independent oracle: git's own count over the same window, via a
    # different git command than the collector uses.
    p = _repo(tmp_path)
    for i in range(probe.MAX_COMMITS + 5):  # force truncation on one day
        _commit(p, "2026-06-08", "bulk %d" % i, {"bulk.txt": "%d\n" % i})
    proj = _project(p)
    days = history.build_days([proj], {proj["name"]: history.observe_range(str(p), START, END)},
                              START, END)
    shown = dropped = 0
    for _, doc in days:
        for f in doc["projects"][0]["facts"]:
            if f["kind"] == "commit":
                shown += 1
            elif f["kind"] == "commits_truncated":
                dropped += f["data"]["dropped"]
    expected = int(subprocess.run(
        ["git", "-C", str(p), "rev-list", "--count", "HEAD",
         "--since=%sT00:00:00+0000" % START, "--until=%sT00:00:00+0000" % "2026-06-15"],
        capture_output=True, text=True, check=True).stdout.strip())
    assert shown + dropped == expected == probe.MAX_COMMITS + 5 + 4
    assert dropped == 5


def test_bad_range_refused():
    try:
        history._dates("2026-06-10", "2026-06-01")
    except ValueError as exc:
        assert "precedes" in str(exc)
    else:
        raise AssertionError("reversed range was not refused")
