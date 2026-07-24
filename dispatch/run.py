"""Collection orchestration: one run = enumerate roster, observe each repo,
assemble the day's FACTS document, roll the ledger.

Ledger semantics (`dispatch-ledger.1`): facts for a date are always diffed
against the DAY-START snapshot, so re-running within the same day
regenerates the same file (grown by any new activity) instead of erasing
the morning's facts — idempotent, cumulative, byte-identical on replay.
The first run of a new date rolls day_start forward to the previous run's
latest snapshot.
"""

import json
import os

from . import boundary, facts, probe, snapshot, status

LEDGER_SCHEMA = "dispatch-ledger.1"


def _empty_ledger():
    return {"schema": LEDGER_SCHEMA, "date": None, "day_start": {}, "latest": {}}


def load_ledger(path):
    if not os.path.exists(path):
        return _empty_ledger()
    with open(path) as f:
        ledger = json.load(f)
    if ledger.get("schema") != LEDGER_SCHEMA:
        raise ValueError("%s is not schema %s" % (path, LEDGER_SCHEMA))
    return ledger


def day_start_for(ledger, date):
    if ledger["date"] is None:
        return {}
    if date == ledger["date"]:
        return ledger["day_start"]
    if date > ledger["date"]:
        return ledger["latest"]
    raise ValueError(
        "collection date %s precedes ledger date %s — refusing to run backwards"
        % (date, ledger["date"])
    )


def collect(watch_path, ledger, date):
    """One deterministic pass. Returns (facts_doc, snapshot_doc, new_ledger).

    Two renderings of one collection: FACTS (the day's delta) and SNAPSHOT
    (standing state of every project) come from the same observations, so
    the roster is walked once.
    """
    cfg = boundary.load_watch(watch_path)
    sweep, projects = boundary.resolve_projects(cfg)
    day_start = day_start_for(ledger, date)

    def hasher(path, targets):
        return boundary.per_file_hashes(sweep, path, targets)

    observed = []
    for proj in projects:
        obs = probe.observe(
            proj["path"],
            date,
            day_start.get(proj["name"]),
            hasher,
            status.validate,
        )
        observed.append(dict(proj, surfaces=sweep.derive_status(proj["path"]), obs=obs))

    doc = facts.build(date, observed, day_start)
    board = snapshot.build(date, observed)
    new_ledger = {
        "schema": LEDGER_SCHEMA,
        "date": date,
        "day_start": day_start,
        "latest": facts.new_ledger_entries(observed),
    }
    return doc, board, new_ledger


def run(watch_path, ledger_path, date, out_dir, update_ledger=True,
        snapshot_dir=None):
    """Collect and write artifacts. Returns the FACTS file path.

    The snapshot is written only when `snapshot_dir` is given — the library
    stays explicit; the CLI supplies the default location.
    """
    ledger = load_ledger(ledger_path)
    doc, board, new_ledger = collect(watch_path, ledger, date)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, date + ".json")
    with open(out_path, "w") as f:
        f.write(facts.serialize(doc))
    if snapshot_dir:
        os.makedirs(snapshot_dir, exist_ok=True)
        with open(os.path.join(snapshot_dir, date + ".json"), "w") as f:
            f.write(facts.serialize(board))
    if update_ledger:
        os.makedirs(os.path.dirname(ledger_path) or ".", exist_ok=True)
        with open(ledger_path, "w") as f:
            json.dump(new_ledger, f, indent=2, sort_keys=True)
            f.write("\n")
    return out_path
