"""Narration checker (E3) — the deterministic fence around AI prose.

The narrator (a model) receives ONLY the FACTS file and writes the day's
narrative. This module never calls a model; it is the gate that makes the
narrator safe to trust: every factual claim must cite a fact id, and every
cited id must exist in the FACTS the collector produced. Prose the collector
can't back is rejected, not published.

Citation contract (deterministic, so the narrator must follow it exactly):
  - A citation is `[F0007]` or a group `[F0007, F0012]`, inline in the prose.
  - Every sentence carrying a factual claim ends with >=1 citation. A
    "sentence" is a `.`/`!`/`?`-terminated span; markdown headings (`#…`)
    and fenced code blocks are exempt (structure, not claims).
  - Every cited id must appear in the FACTS document.

`check()` is pure: same narration + same FACTS -> same report. Two failure
classes are reported separately — fabricated ids (the model invented a fact)
and uncited sentences (a claim with no ground) — because they mean different
things to a human reviewer.
"""

import re

_CITATION = re.compile(r"\[(F\d{4}(?:\s*,\s*F\d{4})*)\]")
_ID = re.compile(r"F\d{4}")


def real_ids(facts_doc):
    """The set of every fact id the collector actually produced."""
    return {
        fact["id"]
        for project in facts_doc.get("projects", [])
        for fact in project.get("facts", [])
    }


def cited_ids(narration):
    """Every fact id cited in the prose, in order (groups flattened)."""
    ids = []
    for match in _CITATION.finditer(narration):
        ids.extend(_ID.findall(match.group(1)))
    return ids


def _claim_sentences(narration):
    """Sentences that must be grounded — headings and code fences removed."""
    body, in_code = [], False
    for line in narration.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code or line.lstrip().startswith("#"):
            continue
        body.append(line)
    joined = " ".join(body)
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", joined) if s.strip()]


def check(narration, facts_doc):
    """Report whether `narration` is safe to publish against `facts_doc`.

    ok is True only when the model invented no fact id AND left no claim
    ungrounded. `uncited_facts` is informational (real ids the narration
    never mentioned) — a coverage note, not a failure.
    """
    ids = real_ids(facts_doc)
    cited = cited_ids(narration)
    fabricated = sorted({c for c in cited if c not in ids})
    uncited = [
        s
        for s in _claim_sentences(narration)
        if re.search("[A-Za-z]", s) and not _CITATION.search(s)
    ]
    return {
        "ok": not fabricated and not uncited,
        "fabricated": fabricated,
        "uncited_sentences": uncited,
        "cited": sorted(set(cited)),
        "uncited_facts": sorted(ids - set(cited)),
    }
