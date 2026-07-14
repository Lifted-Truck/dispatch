# history-rewrite — purged leaked-path blobs from unpushed local history

- **Queue item:** unqueued: completes the security remediation in
  [2026-07-13-portable-facts.md](2026-07-13-portable-facts.md); ROADMAP
  decision 7 history-rewrite option, human-approved 2026-07-13.
- **Why:** `facts/2026-07-10.json` carried the local username in three
  local commits. The going-forward leak was already fixed (decision 7);
  this removes the blobs from history entirely while the branch is still
  unpushed (`origin/main` at df6211e), so they never reach the public
  remote even in history.
- **What was done:** `git filter-branch --index-filter` over `df6211e..HEAD`
  removed `facts/2026-07-10.json` and `digests/2026-07-10.html` from every
  commit, then the backup refs were dropped and objects gc-pruned. The
  final tree is byte-identical to before the rewrite (both files were
  already untracked at the tip; `git diff` old..new HEAD is empty) —
  only intermediate history changed.
- **Commit SHA remapping** (prior traces cite the OLD SHAs, which are now
  gone; this entry is the bridge — old traces are append-only, not edited):
  - `8f94a27` → `5a17791` (E1 collector)
  - `f537f4a` → `a8cdfc0` (E1 close + verify extend)
  - `13f6a17` → `8434b59` (E2 renderer)
  - `8b8ae29` → `703032f` (security: portable FACTS)
  - base `df6211e` unchanged.
- **Evidence consulted:** full-range leak scan (`git grep <username>`
  per commit) before AND after — the file was the sole offender before,
  zero hits after; purged blob `e2364f64` confirmed unreachable
  (`git cat-file -e` fails post-gc); `./verify full` green on the rewritten
  tree.
- **Alternatives rejected:** soft-reset + re-commit (loses the per-phase
  commit structure and messages); `git filter-repo` (not installed);
  leaving history as-is (rejected by the human — clean now while unpushed
  is cheap).
- **Verify:** full, exit 0, on the rewritten HEAD (recorded in
  .harness/last-verify.json after commit).
- **Open questions:** none. When these commits are first pushed, the public
  remote receives only the clean history.
- **Redaction note:** an earlier draft of this trace spelled the literal
  OS username in the scan-command description; it was replaced with
  `<username>` and the tip commit amended so no username string survives in
  any tracked object (verified by a full object-store scan).
