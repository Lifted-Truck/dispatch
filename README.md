# dispatch

**The daily progress publisher**: watches every development project in
parallel, and at the end of each day renders a styled progress summary for
publication to the owner's website. Deterministic collection, AI narration,
human-gated publishing.

*Part of the autonomous-paradigm ecosystem. Standards, doctrine, and the
ecosystem roadmap live in [autonomous](https://github.com/Lifted-Truck/autonomous)
(`~/Documents/Claude/autonomous/`) — this project executes; that repo governs.*

*Last verified current: 2026-07-24 (E0–E2 closed; E2b portfolio board built,
awaiting ratification; E3 narration is next).*

## The pipeline

```
watched repos ──collect──▶ FACTS (structured, deterministic)
 traces/, DECISIONS.md,      commits, phase transitions, verify
 ROADMAP status, git log     results, decisions made, new lessons
                                  │
                             AI narration (prose FROM facts —
                             never facts from prose)
                                  ▼
                             STYLED DIGEST (static HTML/page)
                                  │
                             human ratifies ──▶ publish to website
                             (auto-publish is EARNED, later)
```

**The split that keeps it honest:** collection is deterministic code reading
externalized state (traces, decision logs, git history — the harness's
stigmergy paying off for a public audience). The model writes *narrative over
collected facts*; it never asserts a fact the collector didn't produce. Every
claim in a digest is traceable to a collected artifact.

## Boundaries

- **Reads** watched repos only — never commits to them (writes-stay-home,
  INTEGRATIONS policy). The watch registry is an explicit allowlist.
- **Publishing is outward-facing** and therefore human-gated per digest until
  the format is stable and trusted; auto-publish is a ROADMAP decision, not a
  drift.
- Depends on autonomous for the **STATUS surface contract** — our intake
  brief (autonomous/integrations/dispatch/brief.md) specifies what
  machine-readable status every project should expose. Until that ships,
  we **degrade visibly**: collect from git history + file conventions alone
  and mark digest sections derived from inference rather than declared
  status.
- Shares SCAN mechanics (hash ledger, skip-unchanged) with the audit loop
  and distillery — consume the shared primitive when it exists; don't fork it.

## Where to start

1. Read [ROADMAP.md](ROADMAP.md) — phases E0–E4 with gates. E0–E2 are
   closed; E2b (portfolio board) awaits ratification. The daily loop:
   - `./bin/collect` — writes `facts/<date>.json` (the day's delta) and
     `snapshots/<date>.json` (standing state); ledger in `state/`.
   - `./bin/render facts/<date>.json` — the daily digest page.
   - `./bin/roundup snapshots/<date>.json` — the cross-project board.

   All three are deterministic and self-contained; generated outputs are
   gitignored (decision 7).
2. Read [CLAUDE.md](CLAUDE.md) §Domain for invariants and protected paths.
3. Our brief against the standards repo:
   `autonomous/integrations/dispatch/brief.md`.
4. [project.manifest.json](project.manifest.json) — spin-up survey answers
   (provisional — confirm with the human at E0 gate).
