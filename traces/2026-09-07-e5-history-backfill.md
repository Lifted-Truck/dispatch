# e5-history-backfill — the collector run backward over git history

- **Queue item:** ROADMAP E5 — History backfill + rollups (added 2026-09-07
  at the human's request: "a historical scan of all the progress made over
  the past several months"). Range and granularity chosen by the human:
  June 2026 → now, weekly rollups. Recorded with decision 14.
- **Why:** live collection is a delta against a ledger, so nothing before
  E1 went live (2026-07-10) had ever been collected, and the daily digest
  cannot show an arc. Git history is the record; the same FACTS schema,
  renderer, narrator and checker can consume a day reconstructed from it.
- **What was built:** `dispatch/history.py` (one `git log` per repo per
  source — never per day; commits by committer date in the commit's own
  timezone, traces by add-commit date, lessons by LIBRARY `added:`, phase
  closures by ROADMAP `CLOSED` markers, dated decisions; quiet days
  explicit; `LIMITS` names what history cannot give); `dispatch/rollup.py`
  (pure ISO-week bucketing) + `dispatch/rollup_render.py` (shared theme);
  `bin/backfill`, `bin/rollup`. Outputs are ordinary `dispatch-facts.1`
  documents under `history/` (gitignored) with `(backfill: …)` in every
  fact's evidence — no schema bump (decision 14).
- **Evidence (E5 gate):**
  - Replay: two backfills over the real roster, 99 days × 67 projects,
    `diff -rq` byte-identical. ~5 s wall clock.
  - Reconcile: for six real repos, shown + truncated commits == an
    independent `git rev-list --count` over the window, exactly — including
    HYPERSAW (1,198 commits, 54 truncated) and Tonality (556). Fixture test
    forces truncation (55 commits on one day) and asserts the same identity.
  - No verify fact in any backfilled day; every fact `inferred`; leak scan
    of the output: zero machine-absolute paths.
  - Rollup golden render byte-stable (`tests/golden/fixture-rollup.html`).
  - Fleet totals June 1 → Sep 7: 3,549 commits, 416 traces, 221 lessons,
    8 phase closures; peak week of Aug 10 at 556 commits; 4 fully quiet days.
- **Bug caught by the gate, before it shipped:** the trace parser returned
  nothing on every repo (rollup showed traces = 0 fleet-wide). Cause:
  Python's `str.splitlines()` treats `\x1e` — the record-separator byte used
  as the per-commit date marker — as a line boundary, so the marker was
  split onto its own empty line and never matched. Fixed with `split("\n")`
  and a comment naming the trap; the commit parser had only survived
  because `\x1f` is not in that set. The failing unit test and the
  suspicious zero in the real rollup pointed at the same line.
- **One-off explained, not papered over:** dispatch's own trace count read
  15 from a naive `git` grep vs 14 from the backfill; the difference is
  `traces/README.md`, which the collector excludes by design. Excluding it
  in the oracle gives 14 = 14.
- **Alternatives rejected:** an optional `basis` field on `dispatch-facts.1`
  (would reopen decision 8's freeze for something `evidence` + the output
  directory already say); reading each repo's tree at a historical rev
  (`git show rev:path`) for lessons/phases — more faithful for files that
  are later edited, but LIBRARY entries carry their own `added:` dates and
  CLOSED markers their own dates, so HEAD suffices for E5; noted as the
  upgrade path if a rewrite ever moves a date.
- **Verify:** full, exit 0, 101 tests.
- **Open questions:** whether backfilled days should be narrated (the
  narrator + checker accept them unchanged; cost is one model call per
  day); E4's two human questions are unchanged.
