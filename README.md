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

## Current recovered renderer evidence

The durable BF08 winding/culling checkpoint has now been mirrored into GitHub from the persistent Drive artifact `OpenMDK1_BF08_WindingGate_LOCAL.zip`.

Current evidence boundary:

- CPU reference renderer culling A/B test completed.
- In the HMO2 candidate view, `keep_back` is much closer to the no-cull reference than `keep_front`.
- Corpus cross-check across nine normal HMOs shows the opposite-to-current-math-front orientation dominates interior candidate views in 9/9 samples.
- This supports the current runtime-facing winding candidate as **STRUCTURAL**, not VERIFIED.
- Exact original cull state, camera/FOV, GLASS blend/Z-write, MIRRLOW behavior and pixel parity remain open.

See:

- `evidence/BF08ed_culling_AB_audit.json`
- `evidence/BF08ee_corpus_winding_crosscheck.json`
- `evidence/BF08ef_winding_gate_receipt.json`

The next step remains an authentic first-scene reconstruction with original-runtime comparison, not broader speculative format expansion.

## Experimental HMO1 textures

The [HMO1 texture experiment](experiments/level3-enhanced-textures/README.md)
adds a reversible 4× texture mode, gate lighting and an optional spatial
door-impact audition to the recovered BF11AK scene. Its staging
command builds the private project from the owner's decoded assets.
