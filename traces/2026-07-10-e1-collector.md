# e1-collector — registry + deterministic collector built (E1 body of work)

- **Queue item:** ROADMAP E1 — Registry + collector (deterministic)
- **Why:** E1 was the open phase, unblocked by the dispatch-001 response
  (`status.1` pinned, sweep primitive shipped). Built the watch-config
  layer, the read-only probe, the pure FACTS assembler, day-start ledger
  semantics, and the `bin/collect` CLI; authored and filed the owed
  `status.1` contract fixtures.
- **Evidence consulted:** ROADMAP E1 gate + decision 3;
  autonomous/integrations/dispatch/{brief,response}.md;
  autonomous/kit/contracts/status.md (`status.1`);
  autonomous/kit/sweep/sweep.py; autonomous/registry.json; CLAUDE.md
  §Domain invariants; INTEGRATIONS.md §1–3 (boundary module, writes stay
  home, mailbox exception).
- **Alternatives rejected:** (a) merging same-day facts files run-over-run —
  replaced by day-start-ledger diffing (idempotent regeneration, no merge
  logic, byte-stable replay for free); (b) a local fallback re-implementing
  sweep's resolve when the provider file is missing — rejected as
  rule-3 duplication; a missing pinned artifact is a visible named failure;
  (c) per-line same-line ROADMAP phase parsing — failed on the real tree
  (wrapped bullets produced ZERO phase facts across 42 repos); replaced by
  last-seen-heading attribution with a regression test.
- **Verify:** fast, exit 0, git df6211e (pre-commit; verify does not yet run
  pytest/ruff — extension proposed to the human, see Open questions). Test
  evidence outside verify: 23/23 pytest green, ruff clean; real-tree gate
  runs: replay byte-identical; next-day run = 43/43 explicit quiet records;
  post-commit delta run emits exactly the one new commit fact
  (tests/unit/test_e1_gate.py).
- **Open questions:** (1) `./verify` extension to `ruff + pytest` is a
  human-gated edit — diff proposed, awaiting go-ahead; (2) E1 gate
  ratification is the human's call; (3) whether facts/ artifacts should be
  committed daily or generated-only once E4 shapes publishing.
