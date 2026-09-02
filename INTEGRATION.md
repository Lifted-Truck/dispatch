# dispatch → website: integration spec (requirements for the site)

*Provider spec, per INTEGRATIONS.md §2. dispatch is the provider; the website
is a consumer. This tells the site's designer what data arrives, what it means,
and which invariants the presentation must not break. Aesthetics are entirely
the site's call — nothing here prescribes a look.*

*Last verified against the code: 2026-09-02 (schemas `dispatch-facts.1`,
`dispatch-snapshot.1`, `dispatch-staged.1`).*

---

## 0. The one-paragraph model

Every day dispatch watches ~66 development projects and produces **facts** — a
deterministic, structured record of what happened (commits, phase changes,
test-gate results, new decisions, new traces), each with a stable id like
`F0007`. An AI narrator writes a short prose digest **over those facts only**,
and every sentence of that prose cites the fact ids it rests on. A checker
rejects any prose that cites a fact that doesn't exist or makes an uncited
claim. A human then ratifies the exact bundle (bound to a content hash), and
only then is it publishable. The site receives that ratified bundle.

Two consequences the design should internalise:

1. **The citations are the product, not clutter.** `[F0007]` in the prose is
   provenance: the reader can follow it to the fact and the fact to its
   evidence. Render it as an affordance (link, hover, sidenote, footnote —
   your choice); never strip it.
2. **Absence is always explicit.** A quiet day is a record that says "quiet",
   not a missing page. Private projects are counted, not vanished. Design the
   empty and quiet states as first-class, because they will be common.

---

## 1. The payloads (what arrives)

Three JSON documents plus one Markdown file, all dated, all file-based, one
set per day. Every JSON carries a `schema` field — **pin it and refuse
unknown values**; dispatch bumps the number rather than silently changing a
shape.

| Payload | Schema | Cadence | What it is |
|---|---|---|---|
| **Staged bundle** | `dispatch-staged.1` | daily | THE publishable unit: filtered facts + narration + checks + hash |
| **Snapshot** | `dispatch-snapshot.1` | daily | standing state of every project (for a portfolio/status board) |
| **Ratification** | `dispatch-ratification.1` | per bundle | the human's approval, bound to the bundle hash |
| Narration | Markdown | daily | also embedded in the bundle as a string; the file is a convenience |

The site should treat the **bundle** as its input for the digest page and the
**snapshot** as its input for any "where is everything" board. The raw daily
FACTS file (`dispatch-facts.1`) also exists but the bundle already contains
the public-filtered subset of it, so the site never needs the raw file.

Delivery mechanics (which directory/repo/API) are an open question on
dispatch's side — see §7. Assume "dated files appear somewhere".

---

## 2. The staged bundle (`dispatch-staged.1`) — digest page input

```jsonc
{
  "schema": "dispatch-staged.1",
  "date": "2026-07-01",                 // ISO date; the digest's identity
  "hash": "3813862d4dec1d41",           // 16-hex content hash of facts+narration
  "facts": { ...dispatch-facts.1 document, PUBLIC projects only... },
  "narration": "## Daily Digest — 2026-07-01\n\n...markdown with [F0001] cites...",
  "checks": {
    "narration_ok": true,               // false => this bundle must never be shown
    "fabricated": [],                   // fact ids cited that don't exist
    "uncited_sentences": []             // sentences with no citation
  },
  "publishable_projects": ["alpha"],    // names that appear in facts
  "withheld": ["beta", "gamma", "delta"] // private projects: COUNT these, never list them publicly
}
```

**Rendering requirements**

- Show the **date** prominently; it is the page's identity and the archive key.
- Render **`narration`** as Markdown. Headings are the narrator's structure
  (executive-brief voice: a one-line cited headline, then themed sections
  such as *Shipped*, *Red / stalled*, *Quiet* — names vary day to day, so
  style by heading level, not by heading text).
- Turn every citation token `[F0007]` or `[F0007, F0012]` into an affordance
  that resolves to the fact record(s) in `facts` (§3). Keep the token visible
  in some form; a footnote number is fine if it round-trips to the id.
- Show the **hash** somewhere discoverable (footer/colophon). It is how a
  published page is traced back to the ratification that approved it.
- Show **withheld** as a count only ("3 projects not shown" / "private work
  omitted"). The names in that array are for the site owner's private view,
  never for the public page.
- If `checks.narration_ok` is `false`, the bundle is **not publishable** — the
  site should refuse it loudly in whatever build step consumes it, not render
  it with a warning.

---

## 3. Facts (`dispatch-facts.1`) — the evidence layer inside the bundle

```jsonc
{
  "schema": "dispatch-facts.1",
  "date": "2026-07-01",
  "quiet_day": false,                   // true => every project below is quiet
  "projects": [
    {
      "name": "alpha",                  // portable id; groups look like "synthetic-worlds/Wend"
      "group": null,                    // or the group name, e.g. "synthetic-worlds"
      "public": true,                   // always true inside a bundle (already filtered)
      "quiet": false,                   // no activity since the last collection
      "source": "inferred",             // "declared" | "inferred"  (see below)
      "status_surface": "absent",       // "declared" | "invalid" | "absent"
      "surfaces": {"git": true, "verify": true, ...},   // which harness files exist
      "facts": [ ...fact records... ]
    }
  ]
}
```

**Fact record** — every one has this shape:

```jsonc
{
  "id": "F0004",          // stable within the day; the citation target
  "project": "alpha",
  "kind": "commit",       // one of the kinds below
  "data": { ... },        // kind-specific, see table
  "source": "inferred",   // "declared" (read from the project's own STATUS surface)
                          // | "inferred" (derived from git / file conventions)
  "evidence": "git log"   // the artifact it came from (a path or a source name)
}
```

**Fact kinds and their `data`** (this is the full set; design a treatment for each):

| kind | data | meaning / suggested treatment |
|---|---|---|
| `commit` | `hash`, `subject`, `basis` | a commit landed; monospace hash + subject |
| `phase` | `id`, `title`, optional `gate_state` (`open`/`green`) | the project's current roadmap phase |
| `verify` | `target`, `exit` (0 = green), `git`, `ts` | test-gate result; **exit 0 is the only green** |
| `trace` | `file` | a provenance entry was written |
| `decision` | `number` | a numbered decision was recorded |
| `lesson` | `id` (e.g. `L0042`) | a durable lesson was logged |
| `library` | `changed: true` | the lessons file changed (no detail) |
| `quiet` | `{}` or `declared_ts` | nothing changed — render as a calm state, not an error |
| `baseline` | `traces`, `decisions` (counts) | first time dispatch saw this project |
| `commits_truncated` | `dropped`, `cap` | more commits than shown; say "+N more" |
| `changed` | `detail` | something moved but nothing above captured it |
| `status_invalid` | `errors[]` | the project's status file is malformed — a warning state |

**`source` / `status_surface`** — every fact is either *declared* (the
project published its own machine-readable status) or *inferred* (dispatch
derived it from git and file conventions). Today **100% of facts are
inferred** (no project emits a status file yet); the site should still carry
the distinction — a subtle badge is enough — because it will flip over time
and the honesty of "inferred" is part of the brand.

---

## 4. Snapshot (`dispatch-snapshot.1`) — portfolio / status board input

One record per watched project, whether or not it moved today. Sorted
freshest-first upstream.

```jsonc
{
  "schema": "dispatch-snapshot.1",
  "date": "2026-08-18",
  "summary": {
    "projects": 66, "declared": 0, "phase_known": 3,
    "verify_green": 20, "verify_red": 4, "verify_unknown": 42, "stale": 5
  },
  "projects": [
    {
      "name": "synthetic-worlds/HYPERSAW", "group": "synthetic-worlds",
      "public": false,                     // NOT pre-filtered — the site MUST filter on this
      "source": "inferred", "status_surface": "absent",
      "phase": {"id": "E4", "title": "Publish pipeline"} | null,
      "verify": {"target": "fast", "exit": 0, "git": "abc1234", "state": "green"} | null,
      "stale_days": 0 | null,              // days since last commit; null = no git
      "staleness": "active" | "recent" | "idle" | "stale" | "unknown",
      "harness": ["git", "verify", "roadmap", ...]   // which harness surfaces exist
    }
  ]
}
```

**Rendering requirements**

- **Filter on `public` yourself.** Unlike the bundle, the snapshot is the
  owner's private ops view and includes every project. A public board shows
  only `public: true` rows and may show "N private projects not listed".
- Staleness buckets are defined upstream: `active` ≤ 1 day, `recent` ≤ 7,
  `idle` ≤ 30, `stale` > 30, `unknown` = no commits. Encode them in form
  (colour/weight), not just text.
- `phase: null` and `verify: null` are common and honest ("no roadmap
  phase", "never run"). Design the null states; don't invent placeholders.
- `summary` is pre-computed for a stat row; it counts ALL projects, so
  recompute it after filtering if the public board shows stats.

---

## 5. Ratification (`dispatch-ratification.1`)

```jsonc
{ "schema": "dispatch-ratification.1", "hash": "3813862d4dec1d41",
  "date": "2026-07-01", "approver": "julian", "ts": "2026-08-12T12:00:00Z" }
```

The site does not need to display this, but a build step **should verify
`ratification.hash == bundle.hash`** before publishing the page — a bundle
edited after approval fails that check by design. Display of the approval
(e.g. "ratified 12 Aug") is optional and tasteful.

---

## 6. Invariants the presentation must not break

1. **Never show a name from `withheld`, or a snapshot row with
   `public: false`, on a public page.** Counts are fine; names are not.
2. **Never strip or reflow citations** such that a claim loses its fact id.
3. **Never render a bundle whose `checks.narration_ok` is false.**
4. **Quiet days render.** `quiet_day: true` (or a narration that is mostly
   `quiet` facts) is a designed state: calm, explicit, not an empty page.
5. **Preserve fact ids as anchors** (`#F0007` or equivalent) so a citation
   is linkable and a reader can deep-link a fact.
6. **The hash appears on the page.** It is the publish identity.
7. **Do not re-derive facts, fetch from the repos, or embellish prose.**
   Everything the page says comes from the bundle; the site is a renderer.

---

## 7. Scale, cadence, and the open questions on dispatch's side

- **Scale:** 66 projects watched; a typical active day carries 100–130 facts
  across the roster and a narration of ~150–250 words with ~10–15 citations.
  Quiet days are frequent. Names include a `group/child` form.
- **Cadence:** one bundle per date, regenerated deterministically (re-running
  the same day yields byte-identical files); a re-ratified day replaces the
  earlier bundle.
- **Open on dispatch's side (you may assume answers, we will adapt):**
  - *Delivery target* — which repo/directory/API receives the files.
  - *Which projects are public* — today every project is `public: false`,
    so a real bundle currently has zero publishable projects. Expect the
    first real digests to be small.
- **Questions for the designer to answer back:**
  - Archive/index: do you want a per-day archive page, a per-project page, or
    both? (Both are derivable from the payloads above.)
  - Citation rendering: inline link, hover card, or footnotes?
  - Do you want the pre-rendered reference HTML (`digests/<date>.html`,
    self-contained, no external assets) as a fallback, or JSON+Markdown only?

---

## 8. Sample payloads (in this repo, always current)

| Sample | Path |
|---|---|
| Facts, active day (4 projects, every kind) | `tests/fixtures/facts/fixture-day.json` |
| Facts, quiet day | `tests/fixtures/facts/quiet-day.json` |
| Narration that passes the checker (14 cites) | `tests/fixtures/narration/brief-clean.md` |
| Narration the checker REJECTS (for the refuse path) | `tests/fixtures/narration/fabricated.md`, `uncited.md` |
| Snapshot | `tests/fixtures/snapshots/fixture-board.json` |
| Reference renders (a look, not a mandate) | `tests/golden/fixture-day.html`, `quiet-day.html`, `fixture-board.html` |

To produce a staged bundle from the samples: `bin/stage tests/fixtures/facts/fixture-day.json tests/fixtures/narration/brief-clean.md --out <dir>`.
