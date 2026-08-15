"""Publish gate (E4) — what stands between a rendered digest and the world.

Deterministic: no model calls, no network, no clock (timestamps are inputs).
This module owns the three properties that make outward publishing safe, and
it enforces them in ONE place so no caller can route around them:

1. **Public filter.** Only projects flagged `public: true` in the watch
   config may appear in a publishable digest (charter invariant). Withheld
   projects are NAMED in the bundle, never silently dropped — a digest that
   omits work should say how much it omitted.
2. **Narration fence.** The narration must have passed the deterministic
   checker (dispatch/narration.py). Ungrounded prose cannot be published.
3. **Human ratification, bound to content.** A ratification records the
   bundle's content hash. Publishing requires a ratification whose hash
   matches the bundle being published — so a digest cannot be swapped,
   edited, or injected AFTER approval and ride out on that approval. This is
   the "an injected bad digest is stoppable before publish" gate.

`gate()` returns every blocker it finds, not just the first: a human fixing
one problem should see the rest in the same pass.
"""

import hashlib
import json

SCHEMA = "dispatch-staged.1"


def publishable_facts(facts_doc):
    """(filtered_facts, withheld_names) — public projects only.

    The filtered document keeps the FACTS schema so downstream renderers are
    unchanged; only the project list narrows.
    """
    public, withheld = [], []
    for project in facts_doc.get("projects", []):
        (public if project.get("public") else withheld).append(project)
    filtered = dict(facts_doc)
    filtered["projects"] = public
    filtered["quiet_day"] = all(p["quiet"] for p in public) if public else True
    return filtered, [p["name"] for p in withheld]


def content_hash(bundle):
    """Stable digest of the publishable content (facts + narration).

    Deliberately covers ONLY what would be published — re-staging the same
    day with the same facts and narration yields the same hash, so a prior
    ratification still applies; changing a single character of either does
    not.
    """
    payload = json.dumps(
        {"date": bundle["date"], "facts": bundle["facts"], "narration": bundle["narration"]},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def stage(facts_doc, narration_text, narration_report, date=None):
    """Assemble a staged bundle from a FACTS doc and its checked narration."""
    filtered, withheld = publishable_facts(facts_doc)
    bundle = {
        "schema": SCHEMA,
        "date": date or facts_doc.get("date"),
        "facts": filtered,
        "narration": narration_text,
        "checks": {
            "narration_ok": bool(narration_report.get("ok")),
            "fabricated": list(narration_report.get("fabricated", [])),
            "uncited_sentences": list(narration_report.get("uncited_sentences", [])),
        },
        "withheld": withheld,
        "publishable_projects": [p["name"] for p in filtered["projects"]],
    }
    bundle["hash"] = content_hash(bundle)
    return bundle


def ratification(bundle_hash, date, approver, ts):
    """A human's approval of one exact bundle. `ts` is an input, not a clock read."""
    return {
        "schema": "dispatch-ratification.1",
        "hash": bundle_hash,
        "date": date,
        "approver": approver,
        "ts": ts,
    }


def gate(bundle, ratification_record=None):
    """Every reason this bundle may NOT be published (empty list = clear)."""
    blockers = []
    if bundle.get("schema") != SCHEMA:
        blockers.append("bundle is not %s" % SCHEMA)
    if not bundle.get("publishable_projects"):
        blockers.append(
            "no project is flagged public — a published digest would be empty "
            "(%d withheld)" % len(bundle.get("withheld", []))
        )
    checks = bundle.get("checks", {})
    if not checks.get("narration_ok"):
        detail = []
        if checks.get("fabricated"):
            detail.append("fabricated ids: %s" % ", ".join(checks["fabricated"]))
        if checks.get("uncited_sentences"):
            detail.append("%d uncited claim(s)" % len(checks["uncited_sentences"]))
        blockers.append(
            "narration failed the checker%s"
            % (" (" + "; ".join(detail) + ")" if detail else "")
        )
    # Re-derive rather than trusting the stored value: a tampered bundle that
    # carries its own stale hash must not authenticate itself.
    actual = content_hash(bundle)
    if bundle.get("hash") != actual:
        blockers.append(
            "bundle hash does not match its content (stored %s, actual %s) — "
            "content changed after staging" % (bundle.get("hash"), actual)
        )
    if ratification_record is None:
        blockers.append("not ratified by a human (publishing is human-gated per digest)")
    else:
        if ratification_record.get("hash") != actual:
            blockers.append(
                "ratification is for a different bundle (approved %s, publishing %s) — "
                "content changed after approval"
                % (ratification_record.get("hash"), actual)
            )
        if ratification_record.get("date") != bundle.get("date"):
            blockers.append("ratification is for a different date")
    return blockers


def may_publish(bundle, ratification_record=None):
    """True only when nothing blocks. Callers must not publish on their own judgment."""
    return not gate(bundle, ratification_record)
