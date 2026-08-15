"""E4 gate tests: an injected/tampered/unapproved digest is stoppable.

Adversarial by design — each test is an attempt to get something published
that should not be. The publish gate must refuse every one.
"""

import json
import os

from conftest import FIXTURES
from dispatch import narration, publish

APPROVER = "julian"
TS = "2026-08-12T12:00:00Z"


def _facts(public_names=()):
    with open(os.path.join(FIXTURES, "facts", "fixture-day.json")) as f:
        doc = json.load(f)
    for project in doc["projects"]:
        project["public"] = project["name"] in public_names
    return doc


def _clean_narration():
    with open(
        os.path.join(FIXTURES, "narration", "brief-clean.md"), encoding="utf-8"
    ) as f:
        return f.read()


def _staged(public_names=("alpha",), text=None):
    facts = _facts(public_names)
    text = _clean_narration() if text is None else text
    # The checker runs against the FULL facts (what the narrator was given).
    report = narration.check(text, _facts())
    return publish.stage(facts, text, report)


def _ratify(bundle):
    return publish.ratification(bundle["hash"], bundle["date"], APPROVER, TS)


# --- the happy path -------------------------------------------------------

def test_ratified_public_bundle_may_publish():
    bundle = _staged()
    assert publish.may_publish(bundle, _ratify(bundle)) is True


# --- property 1: the public filter ---------------------------------------

def test_private_projects_never_reach_the_bundle():
    bundle = _staged(public_names=("alpha",))
    assert bundle["publishable_projects"] == ["alpha"]
    for name in ("beta", "gamma", "delta"):
        assert name in bundle["withheld"]
    blob = json.dumps(bundle["facts"])
    assert "beta" not in blob and "delta" not in blob


def test_withheld_projects_are_named_not_silently_dropped():
    bundle = _staged(public_names=("alpha",))
    assert sorted(bundle["withheld"]) == ["beta", "delta", "gamma"]


def test_all_private_is_blocked_not_an_empty_publish():
    bundle = _staged(public_names=())
    blockers = publish.gate(bundle, _ratify(bundle))
    assert any("no project is flagged public" in b for b in blockers)
    assert publish.may_publish(bundle, _ratify(bundle)) is False


# --- property 2: the narration fence -------------------------------------

def test_ungrounded_narration_is_blocked():
    bad = "Alpha shipped the payment integration and closed the round [F9999]."
    bundle = _staged(text=bad)
    blockers = publish.gate(bundle, _ratify(bundle))
    assert any("narration failed the checker" in b for b in blockers)
    assert any("F9999" in b for b in blockers)


def test_uncited_claim_is_blocked():
    text = "Alpha shipped its widget core [F0004]. Morale has never been higher."
    bundle = _staged(text=text)
    assert any(
        "narration failed the checker" in b
        for b in publish.gate(bundle, _ratify(bundle))
    )


# --- property 3: ratification bound to content ---------------------------

def test_unratified_bundle_is_blocked():
    bundle = _staged()
    assert any("not ratified" in b for b in publish.gate(bundle, None))


def test_narration_swapped_after_approval_is_caught():
    # The injection attack: get a clean bundle approved, then swap the prose.
    bundle = _staged()
    approval = _ratify(bundle)
    assert publish.may_publish(bundle, approval) is True

    bundle["narration"] = "Alpha shipped nothing and the project is cancelled."
    blockers = publish.gate(bundle, approval)
    assert blockers
    assert any("changed after" in b for b in blockers)
    assert publish.may_publish(bundle, approval) is False


def test_facts_swapped_after_approval_is_caught():
    bundle = _staged()
    approval = _ratify(bundle)
    bundle["facts"]["projects"][0]["facts"][0]["data"]["title"] = "Something else"
    assert publish.may_publish(bundle, approval) is False


def test_private_project_smuggled_in_after_approval_is_caught():
    bundle = _staged(public_names=("alpha",))
    approval = _ratify(bundle)
    smuggled = _facts()["projects"][1]  # beta, which is private
    bundle["facts"]["projects"].append(smuggled)
    assert publish.may_publish(bundle, approval) is False


def test_tampered_bundle_cannot_authenticate_with_its_own_hash():
    # Re-stamping the hash after tampering must not launder the change:
    # the ratification still refers to the ORIGINAL content.
    bundle = _staged()
    approval = _ratify(bundle)
    bundle["narration"] = "Rewritten after approval."
    bundle["hash"] = publish.content_hash(bundle)  # attacker re-stamps
    blockers = publish.gate(bundle, approval)
    assert any("ratification is for a different bundle" in b for b in blockers)


def test_ratification_from_another_day_is_rejected():
    bundle = _staged()
    stale = publish.ratification(bundle["hash"], "2026-01-01", APPROVER, TS)
    assert any("different date" in b for b in publish.gate(bundle, stale))


# --- determinism ----------------------------------------------------------

def test_restaging_identical_content_keeps_the_approval_valid():
    first = _staged()
    approval = _ratify(first)
    again = _staged()
    assert again["hash"] == first["hash"]
    assert publish.may_publish(again, approval) is True


def test_gate_reports_every_blocker_not_just_the_first():
    bundle = _staged(public_names=(), text="Uncited claim with no citation.")
    blockers = publish.gate(bundle, None)
    assert len(blockers) >= 3
