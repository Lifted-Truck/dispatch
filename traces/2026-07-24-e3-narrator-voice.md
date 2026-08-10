# e3-narrator-voice — voice chosen, narrator proven end-to-end

- **Queue item:** ROADMAP E3 — Narration (AI, fenced). Completes the phase:
  the checker (deterministic gate) was built in
  traces/2026-07-24-e3-checker.md; this closes the narrator half.
- **Why:** the human ran a three-voice test over the fixture day and chose
  Executive brief; the checker's every-sentence-cited rule stays strict
  (decision 9). The narrator now produces a digest that passes the checker.
- **What was done:** set `narrator.DEFAULT_VOICE = "brief"`; refined the
  citation contract (soft/closing/headline sentences must cite the fact they
  rest on or be dropped; the brief omits empty theme sections). Ran the
  brief narrator as a Sonnet subagent fed ONLY the facts; its output passes
  `bin/check-narration` clean — 14 citations, all grounded — saved as
  `tests/fixtures/narration/brief-clean.md` and pinned by a regression test.
- **Evidence consulted:** the 3-voice comparison (all three checked); ROADMAP
  E3 gate; decision 8 (citation contract) + decision 9 (voice + strict rule).
- **Finding (recorded, decision 9):** across FOUR narrator spawns, every
  general-purpose subagent reflexively ran `./verify` despite an explicit
  no-tools instruction, and the project Stop-gate hook derailed their final
  message — the narration had to be retrieved via a follow-up message each
  time. Two lessons: (1) the deterministic checker, not narrator obedience,
  is the real fence — proven, not asserted; (2) the production narrator must
  run WITHOUT this repo's Stop-gate hook (E4 runtime wiring), e.g. a subagent
  whose cwd is not the dispatch repo. The narrate→check→revise loop also
  showed its value: the checker caught an uncited closer, then an empty
  "nothing to report" section, then an uncited headline — each fixed by a
  contract refinement, never by weakening the gate.
- **Alternatives rejected:** softening uncited-sentence to a warning (would
  weaken a charter-stated gate; the human chose strict); a one-shot narrator
  with no check loop (the iterations above show why the loop is needed).
- **Verify:** full, exit 0; 70 unit tests (incl. the canonical brief passing
  end-to-end and both failure-class fixtures).
- **Open questions:** production narrator runtime (subagent outside the repo,
  or hook scoping) is E4 wiring; auto-publish still explicitly deferred.
