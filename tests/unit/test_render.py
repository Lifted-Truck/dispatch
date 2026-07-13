"""E2 gate tests: golden render byte-stable; quiet day renders correctly;
no network dependencies in the page; data is escaped."""

import json
import os

from conftest import FIXTURES
from dispatch import render

GOLDEN = os.path.join(FIXTURES, "..", "golden")


def _fixture(name):
    with open(os.path.join(FIXTURES, "facts", name)) as f:
        return json.load(f)


def _golden(name):
    with open(os.path.join(GOLDEN, name), encoding="utf-8") as f:
        return f.read()


def test_golden_render_byte_stable():
    doc = _fixture("fixture-day.json")
    assert render.render(doc) == _golden("fixture-day.html")


def test_golden_quiet_day_byte_stable():
    doc = _fixture("quiet-day.json")
    page = render.render(doc)
    assert page == _golden("quiet-day.html")
    assert "A quiet day, on the record." in page
    assert "an explicit finding, not an absence" in page


def test_render_is_pure():
    doc = _fixture("fixture-day.json")
    assert render.render(doc) == render.render(doc)


def test_no_network_dependencies():
    for name in ("fixture-day.json", "quiet-day.json"):
        page = render.render(_fixture(name))
        assert "<script" not in page
        assert "<link" not in page
        assert "@import" not in page
        assert "url(" not in page
        assert "https://" not in page and "http://" not in page


def test_untrusted_data_is_escaped():
    page = render.render(_fixture("fixture-day.json"))
    assert "<script>" not in page
    assert "escape &lt;script&gt; &amp; &quot;quotes&quot; properly" in page


def test_every_fact_id_appears():
    doc = _fixture("fixture-day.json")
    page = render.render(doc)
    for project in doc["projects"]:
        for fact in project["facts"]:
            if fact["kind"] != "quiet":  # quiet projects render as a roll-up
                assert fact["id"] in page


def test_failing_verify_is_visible():
    page = render.render(_fixture("fixture-day.json"))
    assert "red (exit 1)" in page


def test_wrong_schema_refused():
    try:
        render.render({"schema": "dispatch-facts.2", "date": "2026-07-01"})
    except ValueError as exc:
        assert "dispatch-facts.1" in str(exc)
    else:
        raise AssertionError("wrong schema was not refused")
