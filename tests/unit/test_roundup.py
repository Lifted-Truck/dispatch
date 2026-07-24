"""E2b gate tests: golden board byte-stable; every roster project appears
exactly once; inferred-vs-declared carried through; no network deps."""

import json
import os

from conftest import FIXTURES
from dispatch import roundup

GOLDEN = os.path.join(FIXTURES, "..", "golden")


def _fixture():
    with open(os.path.join(FIXTURES, "snapshots", "fixture-board.json")) as f:
        return json.load(f)


def _golden():
    with open(os.path.join(GOLDEN, "fixture-board.html"), encoding="utf-8") as f:
        return f.read()


def test_golden_board_byte_stable():
    assert roundup.render(_fixture()) == _golden()


def test_render_is_pure():
    doc = _fixture()
    assert roundup.render(doc) == roundup.render(doc)


def test_every_project_appears_exactly_once():
    doc = _fixture()
    page = roundup.render(doc)
    for project in doc["projects"]:
        leaf = project["name"].split("/")[-1]
        assert page.count(">%s<" % leaf) == 1


def test_inferred_vs_declared_carried_through():
    page = roundup.render(_fixture())
    assert "declared" in page
    assert "inferred" in page
    assert "off-contract" in page  # the invalid status surface stays visible


def test_missing_data_is_named_not_invented():
    page = roundup.render(_fixture())
    assert "no roadmap phase" in page
    assert "never run" in page


def test_staleness_buckets_rendered():
    page = roundup.render(_fixture())
    for bucket in ("active", "recent", "idle", "stale", "unknown"):
        assert 'age %s"' % bucket in page
    assert ">today<" in page
    assert ">96d<" in page


def test_no_network_dependencies():
    page = roundup.render(_fixture())
    assert "<script" not in page
    assert "<link" not in page
    assert "@import" not in page
    assert "url(" not in page
    assert "https://" not in page and "http://" not in page


def test_untrusted_data_is_escaped():
    page = roundup.render(_fixture())
    assert "<widget>" not in page
    assert "Build the &lt;widget&gt; &amp; ship it" in page


def test_wrong_schema_refused():
    try:
        roundup.render({"schema": "dispatch-facts.1", "date": "2026-07-01"})
    except ValueError as exc:
        assert "dispatch-snapshot.1" in str(exc)
    else:
        raise AssertionError("wrong schema was not refused")
