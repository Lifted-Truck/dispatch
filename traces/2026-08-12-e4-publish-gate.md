# e4-publish-gate — the stoppability half of E4

- **Queue item:** ROADMAP E4 — Publish pipeline. Delivers the
  target-INDEPENDENT half: the gate that stands between a rendered digest
  and the world. Recorded as decision 11.
- **Why:** E4 read as fully blocked on the website target, but only the
  TRANSPORT depends on it. The gate criterion "an injected bad digest is
  stoppable before publish" needs no target at all, and it is the half that
  makes publishing safe — so it was built first.
- **Gap found:** the charter invariant "anything not flagged public never
  appears in a publishable digest" (CLAUDE.md:101) had NO implementation.
  `dispatch/render.py` only rendered a public/private *badge*; every
  project's facts were in the page regardless. Correct for the private ops
  view (E2/E2b), unsafe for publication. `publish.publishable_facts()`
  closes it.
- **What was built:** `dispatch/publish.py` — one chokepoint enforcing the
  public filter, the E3 narration fence, and hash-bound human ratification;
  `bin/stage` (assemble + check), `bin/ratify` (the human's approval, bound
  to a content hash), `bin/publish` (refuses unless clear; exits 3 with no
  transport rather than pretending).
- **Evidence consulted:** CLAUDE.md §Domain invariants (public flag,
  human-gated publishing); ROADMAP E4 gate; decision 6 (all projects
  private); the E3 checker in dispatch/narration.py.
- **Second blocker surfaced:** every watched project is `public: false`, so
  a publishable digest today is EMPTY BY CONSTRUCTION. The E4 gate's other
  half ("a day-cycle lands on the website") cannot be met until at least
  one project is flagged public — independent of the website target. Filed
  as an open question; NOT resolved by guessing which projects are safe to
  publish, which is exactly the call an agent must not make for a human.
- **Alternatives rejected:** (a) filtering inside `render.py` — the renderer
  is used by the PRIVATE ops view too, which should keep showing
  everything; filtering belongs to the publish path, not the renderer.
  (b) A ratification that names only a date — it would carry over to edited
  content, defeating the gate; binding to a content hash is what makes a
  post-approval swap detectable. (c) Implementing a plausible transport
  (git push to a docs/ dir, etc.) — that would be inventing the answer to
  an open question; `bin/publish` exits 3 instead.
- **Verify:** full, exit 0; 84 unit tests (14 new, all adversarial: private
  leakage, all-private empty publish, ungrounded narration, unratified
  publish, post-approval narration/facts/private-project swaps, hash
  re-stamp laundering, stale-date ratification). Live CLI run also shows
  refuse -> ratify -> clear -> tamper -> refuse, and the rendered page
  containing zero private project names.
- **Open questions:** the website target (transport) and which projects may
  be public — both human calls, both now explicit in the ROADMAP. Also
  unbuilt: the production narrator runtime (hook-free subagent, decision 9)
  and auto-publish criteria (deliberately deferred).
