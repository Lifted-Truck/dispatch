# dispatch — ROADMAP

> **Single source of truth for this project's direction.** Phase gates are
> never weakened to pass. Ecosystem-level sequencing lives in
> autonomous/ROADMAP.md (Ecosystem tracks).

## Build sequence (phase-gated)

- **E0 — Charter.** Scaffolded, manifest drafted, brief filed with
  autonomous. *Gate: human ratifies manifest + roadmap, and confirms the
  watch registry's initial allowlist.* **CLOSED 2026-07-10** (user
  go-ahead; allowlist = autonomous/registry.json; brief answered —
  `status.1` pinned, see decisions).
- **E1 — Registry + collector (deterministic).** Watched-repo allowlist
  (config file); collector reads git log, traces/, DECISIONS.md, ROADMAP
  phase markers, verify results (.harness/last-verify.json) since last run;
  hash-ledgered incremental sweeps; output = one dated FACTS file
  (structured JSON) per day. NO model calls in E1. Degrade visibly where a
  repo lacks the status surface (mark facts as inferred-from-git vs
  declared). *Gate: two consecutive runs over the real project tree — second
  collects only the delta; FACTS replay byte-identical from the same inputs;
  a repo with zero activity produces an explicit "quiet" record, not an
  absence.* **CLOSED 2026-07-12** (human ratified; evidence in
  traces/2026-07-10-e1-collector.md; built at 8f94a27).
- **E2 — Renderer (deterministic).** Styled static digest from a FACTS file
  (template + CSS, self-contained HTML per the visual-first doctrine); a
  golden-render test pins the output for a fixture FACTS file. *Gate: golden
  render byte-stable; renders correctly with empty/quiet days; no network
  dependencies in the page.* **← current phase**
- **E2b — Roadmap roundup (deterministic).** A second render target, for
  the human: a cross-project portfolio board — every watched project's
  current phase, gate state, last-verify, and staleness, whether or not
  anything changed today (state snapshot, not daily delta; needs a
  collector snapshot mode, since FACTS carry phase facts only on change).
  Added 2026-07-13 at the human's request. *Gate: golden-render
  byte-stable; every roster project appears exactly once;
  inferred-vs-declared marking carried through.*
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
3. **Pins** (2026-07-10, per autonomous's response to dispatch-001):
   `status.1` (STATUS surface; `.harness/last-verify.json` lifted verbatim;
   NO public flag in STATUS — publishability lives in OUR watch config,
   default false) and the shared sweep primitive
   (`autonomous/kit/sweep/sweep.py`; our own ledger file). E1 proceeds now
   against schema + example; inferred-vs-declared marking is the migration
   plan for repos without writers. Owed: contract-test fixtures for
   `status.1` (author during E1, file via the integrations channel).
4. **E1 data design** (2026-07-10): FACTS schema `dispatch-facts.1` (global
   sequential fact ids `F0001…`; per-fact `source: declared|inferred` plus
   the evidence artifact; truncation is itself a fact — no silent caps).
   Ledger `dispatch-ledger.1` diffs every run against the DAY-START
   snapshot: same-day reruns regenerate the same file cumulatively
   (idempotent, byte-stable replay); the first run of a new date rolls
   day-start forward; a backwards date is refused. Watch config
   `watch.json` (schema `dispatch-watch.1`) layers `public:` flags
   (default false) over the canonical roster and pins the registry schema
   and sweep-module path. Decision-3 owed item CLOSED: `status.1` fixtures
   filed at `autonomous/integrations/dispatch/contract-tests-status1.md`
   (ball: provider).
5. **Verify gate extended** (2026-07-12, human ratified): `fast` now runs
   `ruff check .` and `pytest -q tests/unit` (project venv) after the
   structural checks — a strengthening, applied with explicit approval per
   the charter's protected-paths rule.
6. **Public flags** (2026-07-12, human decision): ALL watched projects stay
   `public: false` for now; revisit when E4 makes publishing real.

## Open questions (blocking, ask the human)

- Website target: static-site generator? Which host/repo receives the
  published page? (Determines E4's shape. Needed by E4, not before.)
- Digest voice/format preferences (length, tone). (Needed by E3.)

## Answered (moved from open questions)

- **`public:` flags** (2026-07-12): keep every watched project private for
  now (decision 6); the flag layer in watch.json is live and defaults false.
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
