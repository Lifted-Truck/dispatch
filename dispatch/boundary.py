"""Boundary module — the ONLY file that knows about the provider (autonomous).

Loads the canonical ecosystem registry and the shared sweep primitive from
the paths pinned in watch.json (INTEGRATIONS rule 1: one seam file).
Everything downstream consumes normalized project dicts and hash values.

Degrade policy: this project has no meaningful local fallback for the
ecosystem roster or the sweep primitive — a missing provider artifact is a
visible, named failure (ProviderError), never a silent guess.

Pins (INTEGRATIONS rule 4): registry schema `ecosystem-registry.0`,
status contract `status.1` — both recorded in watch.json and checked here.
"""

import importlib.util
import json
import os


class ProviderError(RuntimeError):
    """A pinned provider artifact is missing or off-contract."""


def _expand(path):
    return os.path.abspath(os.path.expanduser(path))


def load_watch(path):
    """Read and sanity-check this repo's watch config (the protected allowlist layer)."""
    try:
        with open(path) as f:
            cfg = json.load(f)
    except (OSError, ValueError) as exc:
        raise ProviderError("cannot read watch config %s: %s" % (path, exc))
    if cfg.get("schema") != "dispatch-watch.1":
        raise ProviderError("watch config %s is not schema dispatch-watch.1" % path)
    return cfg


def load_sweep(cfg):
    """Import the shared sweep primitive from its pinned path."""
    spath = _expand(cfg["sweep_module"])
    if not os.path.isfile(spath):
        raise ProviderError(
            "sweep primitive not found at %s (pinned in watch.json; "
            "see autonomous/kit/sweep/)" % spath
        )
    spec = importlib.util.spec_from_file_location("autonomous_sweep", spath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_registry(cfg):
    """Read the canonical ecosystem roster and check the schema pin."""
    rpath = _expand(cfg["registry"])
    try:
        with open(rpath) as f:
            reg = json.load(f)
    except (OSError, ValueError) as exc:
        raise ProviderError("cannot read registry %s: %s" % (rpath, exc))
    pin = cfg.get("registry_schema_pin", "ecosystem-registry.0")
    if reg.get("schema") != pin:
        raise ProviderError(
            "registry %s has schema %r; this consumer pins %r — "
            "review the upstream change before bumping the pin in watch.json"
            % (rpath, reg.get("schema"), pin)
        )
    return reg


def resolve_projects(cfg):
    """Roster -> ordered project dicts with this consumer's flags layered on.

    Returns (sweep_module, projects). Each project dict carries name, path,
    group (from the roster, via sweep.resolve) plus `public` — a dispatch
    policy flag layered here, never stored upstream (registry semantics /
    status.1 contract: a project cannot flag itself into publication).
    """
    sweep = load_sweep(cfg)
    registry = load_registry(cfg)
    default_public = bool(cfg.get("defaults", {}).get("public", False))
    overrides = cfg.get("projects", {})
    projects = []
    for proj in sweep.resolve(registry):
        flags = overrides.get(proj["name"], {})
        proj = dict(proj)
        proj["public"] = bool(flags.get("public", default_public))
        projects.append(proj)
    return sweep, projects


def per_file_hashes(sweep, path, targets):
    """{target: hash16} for each target that exists, via the shared primitive."""
    hashes = {}
    for target in targets:
        h = sweep.content_hash(path, [target])
        if h is not None:
            hashes[target] = h
    return hashes
