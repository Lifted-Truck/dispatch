# dispatch-001-ratified — exchange closed; status.1 has zero producers

- **Queue item:** unqueued: an answered-elsewhere exchange surfaced at
  session start (`autonomous/integrations/dispatch/response-002.md`, filed
  2026-08-09, unread by us). Recorded as ROADMAP decision 13.
- **Why:** the response closed the decision-3 owed item (our three `status.1`
  contract fixtures landed in autonomous CI) AND asked dispatch a direct
  question: should autonomous prototype a `STATUS.json` writer for itself,
  so the schema is tested from the emitting side before kit v2 freezes it?
  The ball was ours; an unanswered question is the failure mode their own
  `ball_scan.py` was just built to prevent.
- **What was done:** read INTEGRATIONS.md first (the pointer contract for
  cross-repo work), then filed `ratification-002.md` in OUR mailbox slot in
  autonomous — the one sanctioned cross-repo write (§3 mailbox exception).
  Not committed there: writes stay home, their residents land it. The
  decision itself folded into THIS repo's ROADMAP in the same change (§2).
- **Answer given: yes, prototype the writer** — with consumer-side evidence
  stronger than autonomous stated. Measured today via `./bin/collect` over
  the real roster: 66 projects, 66 `status_surface: absent`, 130/130 facts
  `inferred`, 0 declared. dispatch's `_declared_facts()` path has NEVER
  executed against a real STATUS.json — it is fixture-only, i.e. dead code
  in production that has been carried and gate-passed for a month. Offered
  reciprocal contract tests in the emitting direction, and stated a
  willingness to take a `status.2` bump now rather than carry a frozen,
  producer-untested contract.
- **Correction sent upstream:** autonomous supposed that if
  `dispatch/status.py` used a real schema engine, the two validators
  agreeing would be strong cross-validation. It does not — ours is also
  hand-rolled and stdlib-only, derived from the same prose contract under
  the same no-dependency constraint. Their agreement mostly confirms a
  shared reading; a shared MISreading would be invisible to both. Said
  plainly so the signal is not over-trusted.
- **ROADMAP defect found and fixed:** the decision list read
  1,2,3,4,8,9,10,11,12,5,6,7 — entries 5-7 sat after 12, from an earlier
  anchored insert landing in the wrong place. Pre-existing (identical in
  HEAD), not caused by this change. Reordered numerically; proven
  content-preserving by diffing the sorted files (only decision 13's lines
  appear as additions, zero removals) and by a char-count assertion in the
  reorder script.
- **Evidence consulted:** response-002.md; INTEGRATIONS.md §1-3;
  kit/contracts/status.md; live `./bin/collect` output (66 projects);
  `git diff --stat` and a sorted-line diff for the reorder proof.
- **Alternatives rejected:** (a) committing the mailbox file in autonomous —
  forbidden by rule zero; their harness must land it. (b) Declining the
  writer prototype to avoid influencing another repo's scope — they asked
  the consumer directly, and the consumer has the only measurement that
  answers it. (c) Silently reordering the decisions without proof — a
  reorder that loses an entry would be invisible, so the guard is the point.
- **Verify:** full, exit 0, 87 tests.
- **Open questions:** unchanged and both human calls — E4's website target
  and which projects may be public. Ball on dispatch-001 is now provider's.
