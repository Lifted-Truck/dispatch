# narrator-runtime — the production narrator: no shell, file deliverable

- **Queue item:** ROADMAP E4 (narrator runtime wiring); closes the owed item
  from decision 9. Recorded as decision 12.
- **Why:** decision 9 logged that FOUR general-purpose narrator subagents ran
  `./verify` despite an explicit no-tools instruction, and that the harness
  Stop gate consumed their final messages — the narration had to be
  retrieved by a follow-up message every time. Instruction was not working;
  the fix had to be structural.
- **What was built:** `.claude/agents/narrator.md` — a dedicated agent with
  `tools: Write` only (no Bash, so `./verify` is not merely discouraged but
  impossible) and `model: sonnet` (doctrine's scoped-execution tier, pinned
  explicitly, never inherited). `narrator.build_prompt(..., out_path=)` adds
  file-delivery instructions; `bin/narrate --out-path` emits that form.
- **Diagnosis (evidence):** `.claude/hooks/stop-gate.sh` fires on BOTH `Stop`
  and `SubagentStop` and tests `.harness/dirty` — a PROJECT-level flag set by
  the PARENT session's edits (`posttool-dirty.sh`). So a subagent that edits
  nothing is gated for the lead's uncommitted work, and the only remedy it
  has is to run the oracle. That is the whole mechanism.
- **Proof:** with the tree deliberately left dirty so the gate WOULD fire, a
  subagent given the file-delivery prompt used exactly one tool (the Write),
  its chat message was consumed by hook-response text, and the narration file
  arrived intact — 14 citations, all grounded, `bin/check-narration` exit 0.
  Under the old message-delivery design that message WAS the deliverable and
  would have been lost.
- **Limitation, stated:** the `narrator` agent TYPE could not be exercised
  here — agent definitions load at session start, so spawning it failed with
  "agent type not found". Its frontmatter was validated against the existing
  agents (same keys as verifier.md) and the file-delivery MECHANISM was
  proven with a general-purpose agent, but the no-Bash restriction itself is
  unexercised until a fresh session. Do not treat it as verified.
- **Alternatives rejected:** (a) scoping the Stop gate so `SubagentStop`
  ignores the parent's dirty flag — defensible (it is a false positive, and
  the parent is still gated at its own Stop), but it is a GATE EDIT requiring
  human approval, and the file-delivery design made it unnecessary. Not
  weakening a gate we no longer need to weaken is the better outcome.
  (b) A no-tools narrator relying on its final message — that is precisely
  the design that kept failing.
- **Verify:** full, exit 0; 86 unit tests (2 new, covering file-delivery vs
  message-delivery prompts).
- **Open questions:** confirm the `narrator` agent type resolves in a fresh
  session (first real run will tell); E4's two blockers (website target,
  which projects may be public) are unchanged.
