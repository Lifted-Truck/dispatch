# website-integration-spec — provider spec for the site that will publish digests

- **Queue item:** unqueued: human request (2026-08-28, resumed 2026-09-02) —
  a requirements sheet for the agent designing the website, describing the
  data it must be ready to assimilate. E4-adjacent: the site is E4's
  consumer, and the transport is still an open question.
- **Why:** INTEGRATIONS §2 says a provider publishes an `INTEGRATION.md`
  spec and consumers design against it. dispatch is the provider here; the
  website is the consumer. Writing the sheet as that spec (rather than a
  loose memo) makes it the durable contract the transport decision will
  later plug into.
- **What was written:** `INTEGRATION.md` — the three JSON payloads and the
  narration Markdown, a data dictionary for every fact kind, the rendering
  requirements per payload, seven presentation invariants (no withheld
  names, never strip citations, refuse `narration_ok:false`, quiet days
  render, fact ids are anchors, hash on the page, no re-derivation), scale
  and cadence, open questions in both directions, and in-repo sample
  payloads. Aesthetics deliberately unprescribed — the human already has
  the concept.
- **Evidence consulted:** the emitted shapes, read from the code and from
  real output rather than memory — `facts/2026-08-18.json` (top-level and
  record keys, kinds seen), `snapshots/2026-08-18.json` (summary shape),
  `dispatch/facts.py` (every `fact(kind, …)` call site → the full kind
  table), `dispatch/publish.py` (bundle + ratification shapes),
  `dispatch/snapshot.py` (staleness buckets). Leak self-check on the file:
  zero machine-absolute paths.
- **Alternatives rejected:** a memo in `jobs-temporary` (not versioned, not
  the contract the transport will bind to); embedding a mandated look (the
  human owns the aesthetic; the spec describes data and invariants only).
- **Verify:** full, exit 0, 87 tests.
- **Open questions:** delivery target and which projects go public
  (unchanged, both the human's); the designer's answers on archive shape and
  citation rendering.
