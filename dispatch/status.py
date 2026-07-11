"""Validator for the pinned STATUS surface contract, `status.1`.

Canonical schema: autonomous/kit/contracts/status.md (dispatch-001 response).
Stdlib-only, deterministic. validate() returns a list of error strings —
empty means the document conforms; a non-empty list is the visible reason a
project falls back to the inferred path.
"""

import re

SCHEMA_ID = "status.1"

_REQUIRED = ("schema", "project", "ts", "quiet")
_VERIFY_REQUIRED = ("target", "exit", "git", "ts")
_LESSON_RE = re.compile(r"^L\d{4}$")


def _check_str(doc, key, errors, where=""):
    if key in doc and not isinstance(doc[key], str):
        errors.append("%s%s must be a string" % (where, key))


def validate(doc):
    """status.1 conformance errors for a parsed JSON document (empty = valid)."""
    if not isinstance(doc, dict):
        return ["document is not a JSON object"]
    errors = []
    for key in _REQUIRED:
        if key not in doc:
            errors.append("missing required field: %s" % key)
    if "schema" in doc and doc["schema"] != SCHEMA_ID:
        errors.append("schema is %r, expected %r" % (doc["schema"], SCHEMA_ID))
    _check_str(doc, "project", errors)
    _check_str(doc, "ts", errors)
    _check_str(doc, "recent_since", errors)
    if "quiet" in doc and not isinstance(doc["quiet"], bool):
        errors.append("quiet must be a boolean")

    phase = doc.get("roadmap_phase")
    if phase is not None:
        if not isinstance(phase, dict):
            errors.append("roadmap_phase must be an object")
        else:
            for key in ("id", "title"):
                if key not in phase:
                    errors.append("roadmap_phase missing required field: %s" % key)
                else:
                    _check_str(phase, key, errors, "roadmap_phase.")
            gate = phase.get("gate_state")
            if gate is not None and gate not in ("open", "green"):
                errors.append("roadmap_phase.gate_state must be 'open' or 'green'")

    verify = doc.get("last_verify")
    if verify is not None:
        if not isinstance(verify, dict):
            errors.append("last_verify must be an object")
        else:
            for key in _VERIFY_REQUIRED:
                if key not in verify:
                    errors.append("last_verify missing required field: %s" % key)
            if "exit" in verify and not isinstance(verify["exit"], int):
                errors.append("last_verify.exit must be an integer")
            for key in ("target", "git", "ts"):
                _check_str(verify, key, errors, "last_verify.")

    recent = doc.get("recent")
    if recent is not None:
        if not isinstance(recent, dict):
            errors.append("recent must be an object")
        else:
            _validate_recent(recent, errors)
    return errors


def _validate_recent(recent, errors):
    commits = recent.get("commits")
    if commits is not None:
        if not isinstance(commits, list):
            errors.append("recent.commits must be an array")
        else:
            for i, commit in enumerate(commits):
                if not isinstance(commit, dict):
                    errors.append("recent.commits[%d] must be an object" % i)
                    continue
                for key in ("hash", "subject"):
                    if key not in commit:
                        errors.append("recent.commits[%d] missing %s" % (i, key))
    for key in ("decisions", "traces"):
        items = recent.get(key)
        if items is not None and (
            not isinstance(items, list)
            or any(not isinstance(x, str) for x in items)
        ):
            errors.append("recent.%s must be an array of strings" % key)
    lessons = recent.get("lessons")
    if lessons is not None:
        if not isinstance(lessons, list) or any(
            not isinstance(x, str) or not _LESSON_RE.match(x) for x in lessons
        ):
            errors.append("recent.lessons must be an array of ids matching L\\d{4}")
