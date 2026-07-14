"""FACTS assembly — pure functions: observations + day-start ledger + date
-> the day's FACTS document (schema `dispatch-facts.1`).

Every fact carries a stable id (E3 narration must cite these), a `source`
of "declared" (lifted from a valid status.1 surface) or "inferred"
(derived from git/file conventions), and the evidence artifact it came
from. Serialization is byte-stable: same inputs -> same bytes.
"""

import json

from . import probe

SCHEMA = "dispatch-facts.1"


class _Seq:
    def __init__(self):
        self.n = 0

    def next(self):
        self.n += 1
        return "F%04d" % self.n


def build(date, observed, day_start):
    """observed: [{name, path, group, public, surfaces, obs}] in roster order."""
    seq = _Seq()
    projects = [_project_record(p, day_start.get(p["name"]), seq) for p in observed]
    return {
        "schema": SCHEMA,
        "date": date,
        "quiet_day": all(rec["quiet"] for rec in projects),
        "projects": projects,
    }


def serialize(doc):
    return json.dumps(doc, indent=2, sort_keys=True) + "\n"


def new_ledger_entries(observed):
    return {p["name"]: probe.ledger_entry(p["obs"]) for p in observed}


def _project_record(project, prev, seq):
    obs = project["obs"]
    status = obs["status"]
    source = "declared" if status["valid"] else "inferred"
    changed = prev is None or probe.ledger_entry(obs) != prev

    def fact(kind, data, evidence, fact_source=source):
        return {
            "id": seq.next(),
            "project": project["name"],
            "kind": kind,
            "data": data,
            "source": fact_source,
            "evidence": evidence,
        }

    if not changed:
        facts = [fact("quiet", {}, "hash ledger (unchanged since day start)")]
    elif source == "declared":
        facts = _declared_facts(obs, fact)
    else:
        facts = _inferred_facts(obs, prev, fact)

    if status["present"] and not status["valid"]:
        # Visible degrade: a STATUS.json exists but is off-contract.
        facts.append(
            fact(
                "status_invalid",
                {"errors": status["errors"]},
                "STATUS.json vs status.1",
                "inferred",
            )
        )

    quiet = bool(facts) and all(f["kind"] == "quiet" for f in facts)
    return {
        # No absolute path: `name` is the portable identifier (basename or
        # group/child). Persisting sweep's absolute path would bake the local
        # username + machine layout into an artifact bound for a public
        # remote. See ROADMAP decision 7.
        "name": project["name"],
        "group": project["group"],
        "public": project["public"],
        "source": source,
        "status_surface": "declared" if status["valid"] else (
            "invalid" if status["present"] else "absent"
        ),
        "surfaces": project["surfaces"],
        "quiet": quiet,
        "facts": facts,
    }


def _declared_facts(obs, fact):
    doc = obs["status"]["doc"]
    if doc.get("quiet"):
        return [fact("quiet", {"declared_ts": doc["ts"]}, "STATUS.json")]
    facts = []
    phase = doc.get("roadmap_phase")
    if phase:
        facts.append(fact("phase", phase, "STATUS.json"))
    verify = doc.get("last_verify")
    if verify:
        facts.append(fact("verify", verify, "STATUS.json"))
    recent = doc.get("recent") or {}
    for commit in recent.get("commits") or []:
        facts.append(fact("commit", commit, "STATUS.json"))
    for number in recent.get("decisions") or []:
        facts.append(fact("decision", {"number": number}, "STATUS.json"))
    for name in recent.get("traces") or []:
        facts.append(fact("trace", {"file": name}, "STATUS.json"))
    for lesson in recent.get("lessons") or []:
        facts.append(fact("lesson", {"id": lesson}, "STATUS.json"))
    if not facts:
        facts.append(fact("changed", {"detail": "status surface updated"}, "STATUS.json"))
    return facts


def _inferred_facts(obs, prev, fact):
    facts = []
    baseline = prev is None
    prev_files = (prev or {}).get("files", {})

    if obs["roadmap_phase"] and (
        baseline or prev_files.get("ROADMAP.md") != obs["files"].get("ROADMAP.md")
    ):
        facts.append(fact("phase", obs["roadmap_phase"], "ROADMAP.md"))
    if obs["verify"] and (
        baseline
        or prev_files.get(".harness/last-verify.json")
        != obs["files"].get(".harness/last-verify.json")
    ):
        facts.append(fact("verify", obs["verify"], ".harness/last-verify.json"))

    for commit in obs["commits"]:
        facts.append(
            fact("commit", dict(commit, basis=obs["commits_basis"]), "git log")
        )
    if obs["commits_dropped"]:
        # No silent caps: say how many commits the window dropped.
        facts.append(
            fact(
                "commits_truncated",
                {"dropped": obs["commits_dropped"], "cap": probe.MAX_COMMITS},
                "git log",
            )
        )

    if baseline:
        facts.append(
            fact(
                "baseline",
                {
                    "traces": len(obs["traces"] or []),
                    "decisions": len(obs["decisions"] or []),
                },
                "first sighting (no day-start ledger entry)",
            )
        )
        return facts

    for name in sorted(set(obs["traces"] or []) - set(prev.get("traces", []))):
        facts.append(fact("trace", {"file": name}, "traces/"))
    for number in [
        n for n in (obs["decisions"] or []) if n not in set(prev.get("decisions", []))
    ]:
        facts.append(fact("decision", {"number": number}, "DECISIONS.md"))
    if prev_files.get("LIBRARY.md") != obs["files"].get("LIBRARY.md") and (
        "LIBRARY.md" in prev_files or "LIBRARY.md" in obs["files"]
    ):
        facts.append(fact("library", {"changed": True}, "LIBRARY.md"))

    if not facts:
        # The fingerprint moved but nothing above captured it (e.g. a trace
        # or decision was removed). Never silent: record the raw change.
        facts.append(
            fact("changed", {"detail": "fingerprint changed"}, "hash ledger")
        )
    return facts
