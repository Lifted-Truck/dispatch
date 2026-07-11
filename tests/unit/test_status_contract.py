"""Contract tests for the pinned status.1 surface (dispatch-001).

The fixtures in tests/fixtures/status1/ are the suite offered to the
provider (consumer-authored, resident-landed): valid parse, quiet day,
missing-field rejection.
"""

import json
import os

from conftest import FIXTURES
from dispatch import status


def _load(name):
    with open(os.path.join(FIXTURES, "status1", name)) as f:
        return json.load(f)


def test_valid_fixture_parses():
    assert status.validate(_load("valid.json")) == []


def test_quiet_day_fixture_parses():
    doc = _load("quiet.json")
    assert status.validate(doc) == []
    assert doc["quiet"] is True


def test_missing_field_fixture_rejected():
    errors = status.validate(_load("missing-field.json"))
    assert "missing required field: quiet" in errors
    assert any("last_verify missing required field: ts" == e for e in errors)
    assert any("recent.commits[0] missing subject" == e for e in errors)
    assert any(e.startswith("recent.lessons") for e in errors)


def test_wrong_schema_rejected():
    doc = _load("valid.json")
    doc["schema"] = "status.2"
    assert any("expected 'status.1'" in e for e in status.validate(doc))


def test_non_object_rejected():
    assert status.validate([1, 2]) == ["document is not a JSON object"]


def test_bad_gate_state_rejected():
    doc = _load("valid.json")
    doc["roadmap_phase"]["gate_state"] = "closed"
    assert any("gate_state" in e for e in status.validate(doc))
