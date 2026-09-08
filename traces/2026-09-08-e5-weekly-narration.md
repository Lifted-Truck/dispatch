# e5-weekly-narration — every week narrated, every sentence grounded

- **Queue item:** ROADMAP E5 (human request 2026-09-08: "sub-agents scrub
  through and summarize the work of each week"). Model choice: Sonnet, the
  tier the narrator is pinned to; Opus offered as a per-week re-run if prose
  reads thin. Recorded with decision 15.
- **What was built:** `history.merge_days` (seven day-documents → one
  `dispatch-facts.1` week document; ids re-sequenced so they are unique
  across the week; the day rides on each fact's evidence string; daily quiet
  facts collapse to one per all-quiet project); a `weekly` voice; a compact
  one-fact-per-line payload for briefs on disk; `bin/weekfacts`;
  `rollup_render.narration_html` (headings, paragraphs, bold, citations —
  deliberately tiny, no Markdown dependency) and `bin/rollup --narrations`,
  which RE-CHECKS every narration against its week's facts at render time.
  `.claude/agents/narrator-file.md` (Read + Write, no shell) for future runs.
- **Evidence:** 15 weeks (Jun 1 → Sep 7) narrated in parallel; final state
  15/15 pass `bin/check-narration` — 7,615 words, 346 citation groups
  (884 cited ids), 0 fabricated ids at any point. First pass: 11 clean, 3
  with exactly one uncited sentence, 1 grounded refusal. Revisions were
  single-sentence and each agent CITED the claim rather than deleting it
  (e.g. "HYPERSAW filed six lessons this week [F0055, F0056, F0107, F0183,
  F0312, F0369]"). Renders clean; leak scan of the page: none.
- **Runtime findings, both recorded in decision 15:**
  1. Inline facts do not scale: the briefs total ~700 KB, and inlining means
     the lead reads them and then re-types them into fifteen spawns. Briefs
     on disk + a pointer prompt kept the facts out of the lead's context.
  2. The Read tool pages by LINE with a size cap. The first briefs put the
     whole week's JSON on one line; the busiest week's narrator (723 facts)
     could read nothing and wrote a grounded refusal — the correct output,
     and exactly the failure the checker would have caught had it guessed.
     Fixed by emitting one fact per line (885 lines, max 562 chars); the
     retry read it in four tool calls and passed with 87 citations.
  3. Every agent honoured "do not run anything after the write" once the
     brief anticipated the Stop hook — the opposite of decision 9's finding,
     and the difference is that the deliverable is a file the hook cannot
     un-write.
- **Deviation, stated:** general-purpose agents (with shell) were used
  because `narrator-file` cannot load mid-session. Accepted for this pass
  because the checker is the fence; not a precedent — the agent definition
  is the fix, and it is in this change.
- **Alternatives rejected:** narrating per DAY (99 model calls for prose
  nobody asked for; weeks were the human's granularity); trusting
  narrations written to disk without re-checking at render time (a stale or
  hand-edited file would otherwise publish unfenced).
- **Verify:** full, exit 0, 104 tests. The rollup golden was regenerated
  once for the `.narr` CSS — a golden created earlier today on this same
  unmerged branch, not a ratified one.
- **Open questions:** E5 ratification (human); whether the narrated history
  should feed the website (INTEGRATION.md already describes the narration
  contract; the week document is the same shape as a day).
