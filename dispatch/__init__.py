"""dispatch — deterministic daily-progress collector (E1).

No model calls anywhere in this package (charter invariant: facts before
prose). Wall-clock reads live only in the CLI adapter (bin/collect); every
function here is a pure-or-IO-deterministic transform of its inputs.
"""
