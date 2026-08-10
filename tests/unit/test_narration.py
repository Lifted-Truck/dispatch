"""E3 gate tests: the narration checker grounds prose against the FACTS.

Planted-fact test — narration over fixture-day.json must cite only real
fact ids; a fabricated-claim fixture must be caught; an uncited claim must
be caught. The checker is deterministic and calls no model.
"""

import json
import os

from conftest import FIXTURES
from dispatch import narration


def _facts():
    with open(os.path.join(FIXTURES, "facts", "fixture-day.json")) as f:
        return json.load(f)


def _narration(name):
    with open(os.path.join(FIXTURES, "narration", name), encoding="utf-8") as f:
        return f.read()


def test_real_ids_are_every_collected_fact():
    ids = narration.real_ids(_facts())
    assert ids == {"F%04d" % n for n in range(1, 15)}


def test_grouped_citations_flatten():
    assert narration.cited_ids("landed core [F0001, F0004] and green [F0002].") == [
        "F0001", "F0004", "F0002",
    ]


def test_good_narration_passes():
    report = narration.check(_narration("good.md"), _facts())
    assert report["ok"] is True
    assert report["fabricated"] == []
    assert report["uncited_sentences"] == []


def test_fabricated_fact_id_is_caught():
    report = narration.check(_narration("fabricated.md"), _facts())
    assert report["ok"] is False
    assert "F9999" in report["fabricated"]


def test_uncited_claim_is_caught():
    report = narration.check(_narration("uncited.md"), _facts())
    assert report["ok"] is False
    assert report["fabricated"] == []
    assert any("morale" in s for s in report["uncited_sentences"])


def test_headings_are_exempt_from_citation():
    text = "# A title with no citation\n\nAlpha shipped [F0004]."
    assert narration.check(text, _facts())["ok"] is True


def test_uncited_facts_reported_but_not_a_failure():
    # A narration that grounds every sentence but mentions only one fact is
    # still OK; the unmentioned ids are a coverage note, not a rejection.
    text = "Alpha shipped its widget core [F0004]."
    report = narration.check(text, _facts())
    assert report["ok"] is True
    assert "F0001" in report["uncited_facts"]
    assert "F0004" not in report["uncited_facts"]


def test_canonical_brief_narration_passes():
    # End-to-end example (decision 9): a real executive-brief narration
    # produced by the narrator subagent over fixture-day.json, every
    # sentence — headline included — grounded. Pins the E3 happy path.
    report = narration.check(_narration("brief-clean.md"), _facts())
    assert report["ok"] is True
    assert report["fabricated"] == []
    assert report["uncited_sentences"] == []
    assert len(report["cited"]) == 14


def test_empty_narration_is_vacuously_ok():
    report = narration.check("", _facts())
    assert report["ok"] is True
    assert report["cited"] == []
