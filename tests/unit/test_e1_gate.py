"""E1 gate tests (ROADMAP): two consecutive runs — second collects only the
delta; FACTS replay byte-identical from the same inputs; zero-activity repos
produce an explicit quiet record, never an absence."""

import datetime
import json

from conftest import git
from dispatch import run

D0 = datetime.date.today().isoformat()
D1 = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
D2 = (datetime.date.today() + datetime.timedelta(days=2)).isoformat()


def _read(path):
    with open(path, "rb") as f:
        return f.read()


def _doc(path):
    return json.loads(_read(path))


def test_gate_sequence(roster):
    # Run 1: baseline over the roster.
    p0 = run.run(roster["watch"], roster["ledger"], D0, roster["out"])
    doc0 = _doc(p0)
    assert [p["name"] for p in doc0["projects"]] == ["alpha", "beta"]
    assert doc0["quiet_day"] is False
    for rec in doc0["projects"]:
        assert rec["source"] == "inferred"  # no STATUS surface in fixtures
        kinds = [f["kind"] for f in rec["facts"]]
        assert "baseline" in kinds and "commit" in kinds

    # public flags layered from watch config, default false.
    assert doc0["projects"][0]["public"] is True
    assert doc0["projects"][1]["public"] is False

    # Same-date rerun regenerates identical bytes (idempotent vs day-start).
    bytes_before = _read(p0)
    run.run(roster["watch"], roster["ledger"], D0, roster["out"])
    assert _read(p0) == bytes_before

    # Run 2 (next day, zero activity): explicit quiet records, not absence.
    p1 = run.run(roster["watch"], roster["ledger"], D1, roster["out"])
    doc1 = _doc(p1)
    assert doc1["quiet_day"] is True
    for rec in doc1["projects"]:
        assert rec["quiet"] is True
        assert [f["kind"] for f in rec["facts"]] == ["quiet"]

    # Replay with the same inputs (ledger untouched): byte-identical.
    bytes1 = _read(p1)
    run.run(roster["watch"], roster["ledger"], D1, roster["out"], update_ledger=False)
    assert _read(p1) == bytes1

    # Run 3 after one commit in alpha: the delta and ONLY the delta.
    (roster["alpha"] / "feature.txt").write_text("x\n")
    git(roster["alpha"], "add", "-A")
    git(roster["alpha"], "commit", "-q", "-m", "add feature")
    p2 = run.run(roster["watch"], roster["ledger"], D2, roster["out"])
    doc2 = _doc(p2)
    alpha, beta = doc2["projects"]
    assert alpha["quiet"] is False
    assert [f["kind"] for f in alpha["facts"]] == ["commit"]
    assert alpha["facts"][0]["data"]["subject"] == "add feature"
    assert alpha["facts"][0]["data"]["basis"] == "since-last-run"
    assert beta["quiet"] is True


def test_date_regression_refused(roster):
    run.run(roster["watch"], roster["ledger"], D1, roster["out"])
    try:
        run.run(roster["watch"], roster["ledger"], D0, roster["out"])
    except ValueError as exc:
        assert "refusing to run backwards" in str(exc)
    else:
        raise AssertionError("date regression was not refused")
