import json
import os
import subprocess
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

FIXTURES = os.path.join(REPO, "tests", "fixtures")

# The real pinned provider artifact (watch.json pin) — tests fail visibly if
# the provider is absent, matching the boundary's degrade policy.
SWEEP_MODULE = "~/Documents/Claude/autonomous/kit/sweep/sweep.py"


def git(path, *args):
    subprocess.run(
        ["git", "-C", str(path), "-c", "user.name=t", "-c", "user.email=t@example.com"]
        + list(args),
        check=True,
        capture_output=True,
    )


def make_repo(root, name):
    """A minimal harness-shaped fixture repo with one commit."""
    path = root / name
    path.mkdir()
    (path / "ROADMAP.md").write_text(
        "# roadmap\n\n"
        "- **E0 — Charter.** done. **CLOSED**\n"
        "- **E1 — Build the thing.** work. *Gate: g.* **← current phase**\n\n"
        "## Decisions on record\n\n"
        "1. First decision.\n"
    )
    (path / "traces").mkdir()
    (path / "traces" / "2026-01-01-scaffold.md").write_text("trace\n")
    (path / ".harness").mkdir()
    (path / ".harness" / "last-verify.json").write_text(
        '{"target":"fast","exit":0,"git":"abc1234","ts":"2026-01-01T00:00:00Z"}\n'
    )
    git(path, "init", "-q")
    git(path, "add", "-A")
    git(path, "commit", "-q", "-m", "scaffold %s" % name)
    return path


@pytest.fixture
def roster(tmp_path):
    """Two fixture repos + a scratch registry and watch config."""
    alpha = make_repo(tmp_path, "alpha")
    beta = make_repo(tmp_path, "beta")
    registry = tmp_path / "registry.json"
    registry.write_text(
        json.dumps(
            {
                "schema": "ecosystem-registry.0",
                "rules": [{"project": str(alpha)}, {"project": str(beta)}],
            }
        )
    )
    watch = tmp_path / "watch.json"
    watch.write_text(
        json.dumps(
            {
                "schema": "dispatch-watch.1",
                "registry": str(registry),
                "registry_schema_pin": "ecosystem-registry.0",
                "sweep_module": SWEEP_MODULE,
                "defaults": {"public": False},
                "projects": {"alpha": {"public": True}},
            }
        )
    )
    return {
        "watch": str(watch),
        "ledger": str(tmp_path / "state" / "ledger.json"),
        "out": str(tmp_path / "facts"),
        "alpha": alpha,
        "beta": beta,
    }
