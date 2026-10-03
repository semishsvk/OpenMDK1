# OpenMDK1

OpenRemaster reconstruction project for **MDK (1997)**.

## Repository contract

- `main` is the stable canonical branch.
- Original retail game data are read-only and remain the fidelity authority.
- Reverse engineering is evidence-driven and deterministic.
- Evidence states: `UNKNOWN -> HYPOTHESIS -> STRUCTURAL -> VERIFIED | FALSIFIED | BLOCKED`.
- Runtime/reconstruction outputs must be validated against the original game or a documented runtime oracle before being called authentic.
- Framework integration uses the OpenRemaster Universal IR / adapter contracts; game-specific evidence wins over framework assumptions.
- Disposable caches/build products are not source-of-truth state.

## Current milestone

`OpenMDK1-001 — First Authentic Scene`.

The repository starts intentionally small. Add decoders, IR, runtime reconstruction, tests, and evidence only as they are justified by the authoritative corpus.
