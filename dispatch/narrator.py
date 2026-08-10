"""Narrator prompt builder (E3) — the fenced hand-off to the model.

Deterministic: no model calls here. This assembles the prompt the narrator
model receives, and its one job is the fence — the prompt carries ONLY the
FACTS document as ground truth, plus the citation contract the deterministic
checker (dispatch/narration.py) will enforce. The model never sees the repo;
if it strays, the checker rejects it. Prompt and checker share one contract.

Voices are data, not code — add one by adding a VOICES entry.
"""

import json

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
collected FACTS. Output ONLY the narration as markdown — no preamble, no
explanation, no code fence around it.

## Voice: {voice_label}
{voice_spec}

## {contract}

## FACTS ({date}) — your only source of truth
```json
{facts_json}
```
"""


def build_prompt(facts_doc, voice_key):
    """Assemble the narrator prompt for one FACTS document and one voice."""
    if voice_key not in VOICES:
        raise KeyError(
            "unknown voice %r; choices: %s"
            % (voice_key, ", ".join(sorted(VOICES)))
        )
    voice = VOICES[voice_key]
    return _TEMPLATE.format(
        date=facts_doc.get("date", "unknown date"),
        voice_label=voice["label"],
        voice_spec=voice["spec"],
        contract=CONTRACT,
        facts_json=json.dumps(facts_doc, indent=2, sort_keys=True),
    )
