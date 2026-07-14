# portable-facts — stop leaking absolute paths; untrack generated outputs

- **Queue item:** unqueued: security-audit finding relayed by the human
  (absolute local filepaths in the repo). Recorded as ROADMAP decision 7.
- **Why:** The collector persisted sweep's machine-absolute project paths
  (`/Users/<user>/...`) into FACTS, and the FACTS/digest outputs were
  git-tracked toward a public remote — leaking username + directory layout.
  Root cause: `dispatch/facts.py` echoed `project["path"]` into the record.
- **Evidence consulted:** git remote (`github.com/Lifted-Truck/dispatch`)
  and push state (`origin/main` at df6211e — the three collector/renderer
  commits are UNPUSHED; leak never left this machine); `grep -c /Users/`
  in facts/2026-07-10.json = 43 (digest = 0, renderer never showed path);
  distillery/ROADMAP.md:132 — the "absolute vs repo-relative" question is
  still OPEN there, NOT a ratified ruling, so the relayed "adopt distillery's
  ruling" premise was corrected: dispatch adopts the principle and records
  its own decision. Confirmed no code reads `path` back off a FACTS record
  (only facts.py:83 wrote it; renderer uses `name`).
- **Alternatives rejected:** (a) relativize path to a repo/ecosystem root —
  the roster spans multiple roots (`~/Documents/Claude/*` plus
  `~/Documents/Tonality`, etc.), so "repo-relative to one root" is
  ill-defined; `name` already is the portable id, so keeping a second path
  field is redundant. Dropped it instead (Reduce, never invent).
  (b) Rewrite unpushed local history now to purge the old blobs — correct
  and clean while unpushed, but it is a history-rewriting git op; charter
  gates that behind explicit human approval, so it is offered, not done.
- **Verify:** full, exit 0; 32 unit tests incl. new
  `test_facts_carry_no_absolute_path` and unchanged golden renders
  (renderer never used `path`, so goldens held). Regenerated
  facts/2026-07-10.json + digest with the fix: `grep -c /Users/` = 0 in both.
- **Open questions:** history rewrite of the 3 unpushed commits (human's
  call — see decision 7); distillery's own absolute-vs-relative question
  remains theirs to close (writes-stay-home; not touched here).
