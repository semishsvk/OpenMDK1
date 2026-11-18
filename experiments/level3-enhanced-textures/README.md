# HMO1 enhanced textures

Press **F3** while playing the BF11AK HMO1 slice to compare Original and Enhanced.
Original is the startup mode. Pass `-- --enhanced-textures` to start directly
in Enhanced. The experiment extends the recovered slice's regular main scene.
R28 and the C285 Windows build have separate source histories.

## Run the private scene

Use Python 3.9+, Pillow (tested with 13.0.0) and Godot 4 (tested with 4.6.3).
From the checkout root, pass the private BF11AK project directory containing
`hmo1.json` and `textures/`, and a new sibling output directory outside the checkout.

```sh
python -m pip install Pillow==13.0.0
python experiments/level3-enhanced-textures/prepare.py "/path/to/BF11AK/project" "/path/to/private/HMO1-enhanced"
godot --headless --editor --path "/path/to/private/HMO1-enhanced" --import
godot --path "/path/to/private/HMO1-enhanced"
```

The staging command checks the input SHA-256 pins, copies the draw and collision
scripts from `recovered/2026-10-09/slice-AK/project`, and writes a separate Godot
project. Keep generated PNGs, private runtime assets and captures outside Git.
Each enhanced PNG has input and output hashes in `enhanced/manifest.json`.

## Art and runtime scope

All 11 textured surface groups used in HMO1 are covered (192 of 394 triangles).
They include the gate, facade, building panels, edge strips and floor variants.
The 202 palette-coloured triangles keep their existing materials. The bake uses
the decoded RGB artwork at 4× in each dimension, with wrap-aware Lanczos
resampling and lossless PNG storage. Enhanced adds mipmaps and anisotropic
filtering for long sightlines. F3 switches the albedo and sampler on the existing
materials and restores their original resource instances on the return trip.
Replacement resources load together on first activation.

## Verify

After import, run with a display available and the absolute path to the test script:

```sh
godot --path "/path/to/private/HMO1-enhanced" --script "/path/to/checkout/experiments/level3-enhanced-textures/verify.gd" -- --capture-dir "/path/to/private/frames"
```

The test sends F3 through the
viewport, checks every binding and mip chain, and compares rendered pixels before
and after switching. The reference frame comes from the unmodified recovered
scene script. Two views cover the approach and an interior camera facing the gate.

For the recovered 360-tick portal traversal, run the normal scene with
`--fixed-fps 60 -- --portal-smoke --capture-dir <absolute-dir>`. Repeat with
`--enhanced-textures` after the separator and a different capture directory.
Compare the two `smoke.json` files, including the pose and activation trace.
The route uses the historical diagnostic portal approach.

### Observed results on 2026-11-18

Godot 4.6.3 on Linux, Compatibility/llvmpipe, 1280×720. All 11 materials
switched with valid mip chains. Both views returned to byte-identical original
RGBA pixels. The gate view changed 311,388 pixels while Enhanced was active.
Original and Enhanced produced identical 360-tick portal smoke reports,
including 12 trace samples, 300 collision cases and 744 portal cases. Target
Windows 4.7.2 performance and R28 integration are pending.

## Next graphics and audio experiments

| Priority | Experiment | Acceptance in HMO1 |
| --- | --- | --- |
| 1 | Tune floor and edge-strip filtering in motion. Compare the current mip chain and anisotropy at a grazing angle. | Replay the same approach at 1080p and 4K. Inspect shimmer on the far floor and detail on the near edge. Record frame times and texture memory on the target GPU. |
| 2 | In Enhanced/Cinematic, light the gate indicators with a small emissive mask, then try a soft contact shadow beneath Kurt. | Match the silhouettes and HUD in paired frames. Check the indicator lettering remains readable through the scope. |
| 3 | Give the original mono door, machinery and impact samples positional emitters at confirmed source locations. Keep the music on its stereo bus. | Approach, turn away and cross the gate. Compare left/right localization and the trigger tick with the original event trace. |
| 4 | Blend a short metallic reverb at the interior threshold and offer a reduced-dynamics headphone mix. | Check the transition in both directions, peaks on overlapping effects and audibility of the quietest cue under music. |
