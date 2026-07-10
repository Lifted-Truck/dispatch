# dispatch — ROADMAP

> **Single source of truth for this project's direction.** Phase gates are
> never weakened to pass. Ecosystem-level sequencing lives in
> autonomous/ROADMAP.md (Ecosystem tracks).

## Build sequence (phase-gated)

- **E0 — Charter.** Scaffolded, manifest drafted, brief filed with
  autonomous. *Gate: human ratifies manifest + roadmap, and confirms the
  watch registry's initial allowlist.* **← current phase**
- **E1 — Registry + collector (deterministic).** Watched-repo allowlist
  (config file); collector reads git log, traces/, DECISIONS.md, ROADMAP
  phase markers, verify results (.harness/last-verify.json) since last run;
  hash-ledgered incremental sweeps; output = one dated FACTS file
  (structured JSON) per day. NO model calls in E1. Degrade visibly where a
  repo lacks the status surface (mark facts as inferred-from-git vs
  declared). *Gate: two consecutive runs over the real project tree — second
  collects only the delta; FACTS replay byte-identical from the same inputs;
  a repo with zero activity produces an explicit "quiet" record, not an
  absence.*
- **E2 — Renderer (deterministic).** Styled static digest from a FACTS file
  (template + CSS, self-contained HTML per the visual-first doctrine); a
  golden-render test pins the output for a fixture FACTS file. *Gate: golden
  render byte-stable; renders correctly with empty/quiet days; no network
  dependencies in the page.*
- **E3 — Narration (AI, fenced).** Model writes the day's narrative FROM the
  FACTS file only (prompt receives facts, not repo access); every prose claim
  must cite a fact id; a deterministic checker rejects narration containing
  fact ids that don't exist. *Gate: planted-fact test — narration over a
  fixture FACTS file cites only real fact ids; a fabricated-claim fixture is
  caught by the checker.*
- **E4 — Publish pipeline.** Website integration; per-digest human
  ratification flow; auto-publish criteria defined and DECISIONS-recorded
  before any unattended publish. *Gate: one full day-cycle lands on the
  website via ratification; an injected bad digest is stoppable before
  publish.*

## Decisions on record (append-only)

1. **Facts before prose** — the model narrates over deterministically
   collected facts, never collects facts itself (AI/deterministic boundary).
2. **Publishing human-gated per digest** until auto-publish criteria are
   explicitly decided (outward-facing action; autonomy graded by
   reversibility — a published post is only softly reversible).

## Open questions (blocking, ask the human)

- Website target: static-site generator? Which host/repo receives the
  published page? (Determines E4's shape.)
- Digest voice/format preferences (length, tone).
- `public:` flags per watched project (which projects may appear in
  published digests — layered in THIS repo's watch config over the canonical
  roster; default `public: false` until the human flags otherwise).

## Answered (moved from open questions)

- **Watch allowlist** (2026-07-10): the canonical ecosystem roster at
  `autonomous/registry.json` (autonomous Decision 14). dispatch layers
  per-project flags (`public:` etc.) in its own config over that roster —
  never a duplicate roster. Groups (synthetic-worlds) recurse one level;
  un-normalized projects are watched anyway with facts marked
  inferred-vs-declared.

## Deferred / demoted

- Weekly/monthly rollup digests (build daily first).
- Pulling distillery lesson-highlights into digests (needs distillery D4).
- Auto-publish (explicitly earned, E4+).
