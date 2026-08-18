# wire-kit-gates — the vendored leak gate was never sourced; now it runs

- **Queue item:** unqueued: instruction relayed by the human from the
  autonomous resident (their Decision 65). Charter-gated file (`./verify`),
  so the human relaying it IS the authorization.
- **Why:** dispatch carried the kit-owned gates at `.kit/kit-gates.sh` but
  `./verify` never sourced them. Confirmed before acting, not assumed:
  `grep -n 'kit-gates\|kit_integrity\|leak_gate' verify` returned NOTHING.
  So the leak gate — the one that stops machine-absolute home paths reaching
  a public remote — has never run in this repo. Vendoring a gate without
  sourcing it is worse than not having it: the file's presence reads as
  coverage.
- **What changed:** `./verify` now sources `.kit/kit-gates.sh` immediately
  after `HARNESS_DIR` is set, with a HARD EXIT when the file is unreadable
  (a degraded run that skips the leak gate is exactly the blind-gate trap);
  `fast()` calls `kit_integrity` and `leak_gate` alongside the existing
  project checks. Every pre-existing project gate is kept. Also commits the
  pending kit 2.5.0 sync (`.kit/MANIFEST` + `.kit/kit-gates.sh`), which was
  sitting uncommitted in the tree and which `kit_integrity` hashes.
- **Proofs (all three, because they come apart):**
  1. `./verify fast` green — exit 0, 87 tests.
  2. `grep -c 'kit/kit-gates.sh' verify` = 3 (>= 1 required).
  3. It FIRES: with a planted file containing a machine-absolute home path,
     `./verify fast` exited 1 and named the planted file in its output;
     removing the file returned verify to green. The planted path is
     deliberately not reproduced here — quoting it would trip the same gate
     in any public repo this trace lands in.
- **Latent trap found (not fixed here):** `.kit/kit-gates.sh` also defines
  `record()`, and `./verify` defines its own. Today the two are
  BYTE-IDENTICAL, so sourcing order is behaviourally irrelevant — but the
  local copy shadows the kit's (it is defined after the source line), so a
  future kit change to `record()` would be silently ignored by this repo.
  Flagged rather than changed: deleting the local duplicate is a separate
  concern from wiring the gates, and the instruction was explicitly minimal.
- **Evidence consulted:** the relayed instruction; `.kit/kit-gates.sh`
  (`leak_gate` at line 54, `kit_integrity` at line 106); `.kit/MANIFEST`
  (kit_version 2.5.0); both `record()` definitions, compared directly.
- **Alternatives rejected:** (a) a soft skip when `.kit/` is absent — the
  instruction is right that a missing kit must be a hard exit; a skipped
  check reads green and is the failure this whole gate guards against.
  (b) Deleting the duplicate `record()` while here — out of scope, and
  bundling it would hide the gate wiring in a larger diff.
- **Verify:** full, exit 0, 87 tests, with the gates now running.
- **Open questions:** the duplicate `record()` (above) wants a decision;
  E4's two human questions are unchanged.
