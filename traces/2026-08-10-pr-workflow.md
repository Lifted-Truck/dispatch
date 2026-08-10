# pr-workflow — E3 ratified; git workflow moves to reviewed PRs

- **Queue item:** ROADMAP E3 closure (human ratified 2026-08-10) + decision
  10 (PR-based git workflow). This is also the first change to use it.
- **Why:** the charter gated "any git operation beyond add/commit on the
  working branch", so every change stacked on local `main` until the human
  pushed by hand — the agent idled on a manual step. Moving to PRs keeps the
  human as the merge gate (nothing lands unreviewed) while removing the
  waiting: branch, push, and PR-open become pre-authorized.
- **What changed:** CLAUDE.md §Human gates drops the blanket git clause and
  gains §Git workflow (normative); ROADMAP decision 10 records the ruling;
  E3 marked CLOSED, E4 marked current-phase and BLOCKED on the
  website-target question.
- **Evidence consulted:** charter §Human gates (protected path — the edit
  was proposed, not assumed); git state read directly (`git ls-remote`
  confirmed origin/main == 1a88f87, i.e. the human's push had landed and the
  hook's "9 unpushed" was stale); `gh auth status` (authenticated as
  Lifted-Truck).
- **Alternatives rejected:** keeping direct-to-main commits and asking for a
  push each time (the status quo that prompted this change); giving the
  agent merge authority too (rejected — merging stays the human gate, which
  is the whole point of review; the agent gains speed, not authority).
- **Verify:** full, exit 0 (recorded in .harness/last-verify.json at the
  branch commit).
- **Open questions:** whether the human wants to merge PRs themselves or
  authorize agent-merge after approval (asked at PR-open time); E4's
  website target still blocks E4.
