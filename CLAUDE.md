# Agent Charter — dispatch

Everything above §Domain is the invariant harness layer. Do not edit it
per-project. Project-specific facts live in §Domain and in ROADMAP.md.

## Truth contract

- **ROADMAP.md is the single source of truth.** Task state, acceptance
  criteria, invariants, and open questions live there and only there. If the
  conversation and ROADMAP.md disagree, ROADMAP.md wins; if ROADMAP.md is
  wrong, fixing it is the first task.
- **Passing ≠ done.** Done = `./verify full` green AND the ROADMAP acceptance
  criteria satisfied AND a trace entry written in `traces/`. Never collapse
  these into each other.
- **Grounded refusal is a success class.** "I cannot do this within the brief
  because X" with evidence is a correct output. Guessing to appear productive
  is a failure.
- **Reduce, never invent.** Prefer deleting code, tightening a contract, or
  reusing an existing mechanism over adding a new one. Every new abstraction
  must displace at least as much complexity as it introduces.

## Provenance

- Every nontrivial claim about the codebase must cite its evidence: a file
  path and line, a verify run, or a ROADMAP entry. No provenance → phrase it
  as a hypothesis, not a fact.
- Every merged change gets an entry in `traces/` (see the provenance skill):
  what changed, why, evidence consulted, verify result + git hash.

## Delegation policy (lead session)

- The lead plans, delegates, integrates, and is the **only** writer of
  ROADMAP.md. Subagents never touch it.
- Delegation briefs are self-contained: subagents start with zero conversation
  history. Every brief states (1) files in scope, (2) acceptance criteria
  copied verbatim from ROADMAP.md, (3) the verify target, (4) what is
  explicitly out of scope.
- Use built-in Explore for codebase reconnaissance. Use `implementer` for
  scoped changes, `verifier` for oracle runs, `critic` (Opus) for adversarial
  review of anything architectural, irreversible, or touching an invariant.
- One queue item per implementer dispatch. Parallel dispatches only for items
  with disjoint file scopes.
- Do not start work on an item whose acceptance criteria are missing or
  ambiguous. Surface the gap to the human; that is the deliverable.

## Oracle discipline

- Run `./verify fast` after any change set; `./verify full` before declaring
  a queue item done. Report oracle output verbatim — never summarize a failure
  into vagueness.
- A red oracle halts forward work. Fix or revert; do not stack changes on red.
- Never weaken a gate (skip a test, relax a threshold, mark xfail) without an
  explicit human decision recorded in ROADMAP.md.

## Human gates

Stop and ask before: deleting files, changing the public interface of
anything, editing `./verify` or the gates it runs, adding a dependency,
and anything §Domain lists as protected.

## Git workflow (PR-based, decision 10)

`main` is never committed to directly. Work happens on a branch and lands
through a pull request the human reviews.

- **Pre-authorized** (no need to ask): create a branch, commit to it, push
  that branch to origin, open/update a PR, and push follow-up commits to an
  open PR's branch.
- **Still gated** (ask first): merging any PR, pushing to `main`,
  force-pushing, rewriting history, and deleting branches or remote refs.
- Branch names: `feat/…`, `fix/…`, `chore/…`, `docs/…` — one queue item or
  concern per branch.
- A PR is opened only on green: `./verify full` passes, and the PR body
  states the queue item, the evidence, and the verify result. Red halts
  forward work exactly as before.
- Trace entries (see §Provenance) are written on the branch, so a merged PR
  arrives with its provenance attached.

---

## §Domain — dispatch

**What this is.** The daily progress publisher: deterministic collector over
watched repos (git log, traces/, DECISIONS, ROADMAP markers, verify results)
→ dated structured FACTS file → styled static digest → AI narration over
facts → human-ratified publish to the owner's website. See README.md for the
pipeline and boundaries.

**Stack & entrypoints.** Python core + template-based static HTML rendering
(self-contained pages, no CDNs — visual-first doctrine). CLI under `bin/`
(to be created in E1). Tests: pytest. `./verify fast` = lint + unit;
`full` = fast + golden-render + narration-checker fixtures.

**Domain invariants** (the critic checks against these):
- **Facts before prose.** The collector is deterministic; NO model calls in
  the collect/render path. The narrator (E3) receives ONLY the FACTS file —
  never repo access — and every prose claim cites a fact id; the
  deterministic checker rejects uncited or nonexistent-id claims.
- Watched repos are READ-ONLY to this project (writes-stay-home). The watch
  registry is an explicit allowlist with a `public:` flag per repo —
  anything not flagged public never appears in a publishable digest.
- **Publishing is human-gated per digest** until auto-publish criteria are
  DECISIONS-recorded (a published post is only softly reversible).
- A quiet day produces an explicit "quiet" record, never a silent absence.
- Collection is incremental and idempotent (hash ledger); FACTS files replay
  byte-identical from the same inputs.

**Protected paths.** The watch registry (allowlist + public flags); the
publish pipeline config (E4); `verify` and this charter; golden render
fixtures.

**Verify targets.** fast: seconds (lint + unit + structure). full: adds
golden-render byte-stability + narration-checker fixture tests; target < 2 min.
