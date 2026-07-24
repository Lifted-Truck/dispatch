"""Repo observation — all reads of a watched repo happen here, read-only.

Deterministic IO: given the same repo state and the same inputs (date,
previous ledger entry), observe() returns the same observation. No model
calls, no wall-clock reads — the collection date is an input.
"""

import json
import os
import re
import subprocess

MAX_COMMITS = 50

# Files whose content changes count as activity (hashed per-file into the
# ledger so the facts layer knows WHICH surface changed).
TARGETS = (
    "ROADMAP.md",
    "DECISIONS.md",
    "STATUS.json",
    ".harness/last-verify.json",
    "LIBRARY.md",
)


def _git(path, args):
    """Run git in `path`; stdout string on success, None on any failure."""
    try:
        result = subprocess.run(
            ["git", "-C", path] + args,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout


def git_head(path):
    out = _git(path, ["rev-parse", "HEAD"])
    return out.strip() if out else None


def _rev_exists(path, rev):
    return _git(path, ["cat-file", "-e", rev + "^{commit}"]) is not None


def git_last_commit_date(path):
    """Date (YYYY-MM-DD) of the most recent commit, or None.

    Committer date in strict ISO form; only the date part is kept — staleness
    is measured in days, and a time-of-day would make the snapshot vary
    within a single collection day.
    """
    out = _git(path, ["log", "-1", "--format=%cI"])
    return out.strip()[:10] if out and out.strip() else None


def git_commits(path, prev_head, date):
    """New commits, newest first: since prev_head when usable, else since
    the collection date's midnight (first sighting / rewritten history).

    Returns (commits, basis, dropped) where basis names which window was
    used — the facts layer surfaces it so a since-midnight window is never
    mistaken for a complete since-last-run delta.
    """
    fmt = "--format=%h%x1f%s"
    if prev_head and _rev_exists(path, prev_head):
        out = _git(path, ["log", fmt, prev_head + "..HEAD"])
        basis = "since-last-run"
    else:
        out = _git(path, ["log", fmt, "--since", date + " 00:00:00"])
        basis = "since-midnight"
    if out is None:
        return [], basis, 0
    lines = [line for line in out.splitlines() if line]
    dropped = max(0, len(lines) - MAX_COMMITS)
    commits = []
    for line in lines[:MAX_COMMITS]:
        chash, _, subject = line.partition("\x1f")
        commits.append({"hash": chash, "subject": subject})
    return commits, basis, dropped


def read_traces(path):
    """Sorted trace filenames, or None when the repo has no traces/ dir."""
    tdir = os.path.join(path, "traces")
    if not os.path.isdir(tdir):
        return None
    return sorted(
        name
        for name in os.listdir(tdir)
        if name.endswith(".md") and name != "README.md"
    )


_DECISION_LINE = re.compile(r"^(\d+)\.\s+\S")
_HEADING = re.compile(r"^#{1,6}\s")


def read_decisions(path):
    """Decision entry numbers, from DECISIONS.md or a ROADMAP 'Decisions'
    section. None when the repo declares decisions nowhere."""
    dpath = os.path.join(path, "DECISIONS.md")
    if os.path.isfile(dpath):
        return _numbered_entries(_read_lines(dpath))
    rpath = os.path.join(path, "ROADMAP.md")
    if os.path.isfile(rpath):
        lines, in_section = _read_lines(rpath), False
        section = []
        for line in lines:
            if _HEADING.match(line):
                in_section = "decision" in line.lower()
            elif in_section:
                section.append(line)
        if section:
            return _numbered_entries(section)
    return None


def _read_lines(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read().splitlines()
    except OSError:
        return []


def _numbered_entries(lines):
    return [m.group(1) for line in lines if (m := _DECISION_LINE.match(line))]


# Phase headings look like `**E1 — Title.**`, and some projects spell the id
# with a leading word (`**Phase C0 — Consolidation.**`) — that prefix is
# stripped so both conventions yield the same id.
_PHASE_MARK = re.compile(r"\*\*(?:Phase\s+)?([A-Za-z]\w*)\s*—\s*(.+?)\.?\*\*")


def read_roadmap_phase(path):
    """Current phase {id, title}, attributed to the most recent phase
    heading when the 'current phase' marker sits on a wrapped line."""
    last = None
    for line in _read_lines(os.path.join(path, "ROADMAP.md")):
        m = _PHASE_MARK.search(line)
        if m:
            last = {"id": m.group(1), "title": m.group(2)}
        if "current phase" in line.lower() and last:
            return last
    return None


def read_verify(path):
    """.harness/last-verify.json verbatim (parsed), or None."""
    try:
        with open(os.path.join(path, ".harness", "last-verify.json")) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def read_status(path, validator):
    """STATUS.json presence/validity per the pinned contract."""
    spath = os.path.join(path, "STATUS.json")
    if not os.path.isfile(spath):
        return {"present": False, "valid": False, "errors": [], "doc": None}
    try:
        with open(spath) as f:
            doc = json.load(f)
    except (OSError, ValueError) as exc:
        return {
            "present": True,
            "valid": False,
            "errors": ["invalid JSON: %s" % exc],
            "doc": None,
        }
    errors = validator(doc)
    return {
        "present": True,
        "valid": not errors,
        "errors": errors,
        "doc": doc if not errors else None,
    }


def observe(path, date, prev_entry, hasher, validator):
    """One read-only pass over a watched repo -> observation dict.

    prev_entry is this project's day-start ledger entry (None on first
    sighting); hasher(path, targets) -> {target: hash16} comes from the
    boundary (shared sweep primitive)."""
    prev_head = (prev_entry or {}).get("git_head")
    head = git_head(path)
    commits, basis, dropped = ([], None, 0)
    if head:
        commits, basis, dropped = git_commits(path, prev_head, date)
    return {
        "git_head": head,
        "last_commit_date": git_last_commit_date(path) if head else None,
        "commits": commits,
        "commits_basis": basis,
        "commits_dropped": dropped,
        "traces": read_traces(path),
        "decisions": read_decisions(path),
        "roadmap_phase": read_roadmap_phase(path),
        "verify": read_verify(path),
        "status": read_status(path, validator),
        "files": hasher(path, TARGETS),
    }


def ledger_entry(obs):
    """The change-detection fingerprint stored per project in the ledger."""
    return {
        "git_head": obs["git_head"],
        "files": obs["files"],
        "traces": obs["traces"] if obs["traces"] is not None else [],
        "decisions": obs["decisions"] if obs["decisions"] is not None else [],
    }
