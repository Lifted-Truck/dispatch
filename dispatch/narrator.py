"""Narrator prompt builder (E3) — the fenced hand-off to the model.

Deterministic: no model calls here. This assembles the prompt the narrator
model receives, and its one job is the fence — the prompt carries ONLY the
FACTS document as ground truth, plus the citation contract the deterministic
checker (dispatch/narration.py) will enforce. The model never sees the repo;
if it strays, the checker rejects it. Prompt and checker share one contract.

Voices are data, not code — add one by adding a VOICES entry.
"""

import json
import re

CONTRACT = """\
Ground rules (a deterministic checker enforces these; violations are rejected):
- The FACTS below are your ONLY source of truth. Do not use any tool, and do
  not assert anything the facts do not state. If it is not in the facts, it
  did not happen.
- End every sentence that makes a factual claim with a citation to the fact
  id(s) it rests on, in square brackets: `[F0007]`, or grouped `[F0007, F0012]`.
- Cite only fact ids that appear in the FACTS. Inventing an id fails the check.
- Markdown headings need no citation. EVERY other sentence does — including
  soft, connective, or closing lines and recommendations. A closer like
  "worth watching before tomorrow" must cite the fact it rests on
  (e.g. `[F0014]`) or be dropped. There is no uncited sentence.
- Write about what the facts show; you need not mention every fact."""

DEFAULT_VOICE = "brief"

VOICES = {
    "changelog": {
        "label": "Terse changelog",
        "spec": (
            "A few tight, factual sentences covering the active projects, dry "
            "and unembellished — closest to the raw facts. One short paragraph "
            "on a normal day. No headline, no framing, no adjectives that the "
            "facts don't earn."
        ),
    },
    "operator": {
        "label": "Warm operator's log",
        "spec": (
            "A brief narrative that reads like a build journal: plain, human, "
            "lightly connective (e.g. 'A quiet day across the fleet; the "
            "exception was...'). Two or three short paragraphs. Warm but never "
            "marketing; the connective tissue is tone, not invented fact."
        ),
    },
    "weekly": {
        "label": "Weekly brief",
        "spec": (
            "This is a WEEK, not a day: the facts span seven days and each "
            "fact carries the `day` it happened on. Open with the "
            "week's one-line headline — a cited claim sentence, not a bare "
            "title. Then the movements grouped by theme: what shipped, what "
            "closed a phase, what went quiet, what is new. Four to six short "
            "paragraphs; group with markdown headings. Prefer naming the "
            "projects that carried the week over listing every commit; a "
            "reader wants the shape of the week. Omit a theme's section "
            "entirely when no fact supports it — never write a 'nothing to "
            "report' line."
        ),
    },
    "brief": {
        "label": "Executive brief",
        "spec": (
            "Open with the day's one-line headline — which is itself a claim "
            "sentence and MUST cite the facts it summarizes (it is a lede, not "
            "a bare title); then the notable movements "
            "grouped by theme — what shipped, what went red, what is stalled. "
            "Skimmable and slightly formal, three to four short paragraphs. "
            "Group with markdown headings if it helps scanning. Omit a theme's "
            "section entirely when no fact supports it — never write a "
            "'nothing to report' line (it is an uncited claim and will fail)."
        ),
    },
}

_TEMPLATE = """\
Origin: dispatch (the daily progress publisher), E3 narrator, {date}.
Authored by the dispatch lead session per ROADMAP decision 8 (narration
citation contract). You are the narrator for a single day's digest.

Task: write the narrative for {date} in the voice specified below, over the
collected FACTS. {delivery}

## Voice: {voice_label}
{voice_spec}

## {contract}

## FACTS ({date}) — your only source of truth
```json
{facts_json}
```
"""


_DELIVER_MESSAGE = (
    "Output ONLY the narration as markdown — no preamble, no explanation, no "
    "code fence around it."
)

_DELIVER_FILE = (
    "Write the narration (markdown only) to `{path}` using the Write tool, "
    "then stop. The FILE is the deliverable — your chat message is not read, "
    "so do not paste the narration into your reply or report on tooling. If a "
    "harness hook interrupts you after the write, the file is already "
    "delivered: do not rewrite it and do not run anything."
)


def build_prompt(facts_doc, voice_key, out_path=None, compact=False):
    """Assemble the narrator prompt for one FACTS document and one voice.

    With `out_path`, the narrator is told to deliver as a FILE. That is the
    production runtime (decision 12): a subagent's final message is fragile —
    a harness hook firing at SubagentStop can bury it — whereas a written file
    survives. Without it, the prompt asks for the narration inline (useful for
    manual runs).
    """
    if voice_key not in VOICES:
        raise KeyError(
            "unknown voice %r; choices: %s"
            % (voice_key, ", ".join(sorted(VOICES)))
        )
    voice = VOICES[voice_key]
    delivery = _DELIVER_FILE.format(path=out_path) if out_path else _DELIVER_MESSAGE
    return _TEMPLATE.format(
        date=facts_doc.get("date", "unknown date"),
        delivery=delivery,
        voice_label=voice["label"],
        voice_spec=voice["spec"],
        contract=CONTRACT,
        facts_json=_payload(facts_doc, compact),
    )


def _payload(doc, compact):
    """The facts as the narrator sees them. `compact` drops fields the
    narrator never needs (per-project flags, per-fact `project`/`source`,
    which are constant within a project) and pretty-printing — a week of
    facts can run to hundreds of records, and the payload is the prompt."""
    if not compact:
        return json.dumps(doc, indent=2, sort_keys=True)
    # Per fact: id, kind, the day (parsed off the evidence suffix that
    # history.merge_days appends, else absent), and data minus constants
    # (`basis` is "backfill" on every commit). Evidence text itself is
    # dropped: the checker validates ids, and the narrator needs the day,
    # not the artifact name.
    slim = {"date": doc["date"], "projects": []}
    for p in doc["projects"]:
        fs = []
        for f in p["facts"]:
            item = {"id": f["id"], "kind": f["kind"]}
            m = re.search(r"\[(\d{4}-\d{2}-\d{2})\]$", f.get("evidence", ""))
            if m:
                item["day"] = m.group(1)
            data = {k: v for k, v in f["data"].items() if k != "basis"}
            if data:
                item["data"] = data
            fs.append(item)
        slim["projects"].append({"name": p["name"], "facts": fs})
    return _one_fact_per_line(slim)


def _one_fact_per_line(slim):
    """Valid JSON laid out one fact per line. A narrator that must READ its
    brief from a file (narrator-file agent) reads by lines with a size cap;
    a week's facts as a single line blew past it and the narrator could
    read nothing — a grounded refusal, but no narration. Lines are the
    unit the tool pages by, so lines are the unit we emit."""
    def dumps(o):
        return json.dumps(o, separators=(",", ":"), sort_keys=True)
    lines = ['{"date":%s,"projects":[' % dumps(slim["date"])]
    for i, p in enumerate(slim["projects"]):
        lines.append('{"name":%s,"facts":[' % dumps(p["name"]))
        lines.append(",\n".join(dumps(f) for f in p["facts"]))
        lines.append("]}" + ("," if i < len(slim["projects"]) - 1 else ""))
    lines.append("]}")
    return "\n".join(lines)
