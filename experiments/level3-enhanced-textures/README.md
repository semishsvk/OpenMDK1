# HMO1 enhanced textures

Press **F3** while playing the BF11AK HMO1 slice to compare Original and Enhanced.
Original is the startup mode. Pass `-- --enhanced-textures` to start directly
in Enhanced. **F4** switches the four rows of colored gate indicators on and off
in Enhanced. The lighting preference lasts for the session. For a lit startup
use `-- --enhanced-textures --gate-lamps`. The experiment extends the recovered slice's regular main scene.
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
resampling and lossless PNG storage. Enhanced adds mipmaps and 16× anisotropic
filtering for long sightlines. F3 switches the albedo and sampler on the existing
materials and restores their original resource instances on the return trip.
Replacement resources load together on first activation. The optional lamp pass
uses the original yellow and cyan artwork on H1_FRONT. The sign below the
indicators and the other materials use the base renderer.

## Verify

After import, run with a display available and the absolute path to the test script:

```sh
godot --path "/path/to/private/HMO1-enhanced" --script "/path/to/checkout/experiments/level3-enhanced-textures/verify.gd" -- --capture-dir "/path/to/private/frames"
```

The test sends F3 and F4 through the viewport, checks every binding and mip chain, and compares rendered pixels before
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
RGBA pixels. From the same gate camera, lighting the four indicator rows changed 1,398 pixels
inside a 65 × 87 pixel bounding rectangle. Turning them off restored the exact
unlit image. Both Original captures also matched the `8cdf6f4` baseline.
Original, Enhanced and Enhanced with lamps produced identical 360-tick portal smoke reports,
including 12 trace samples, 300 collision cases and 744 portal cases. Target
Windows 4.7.2 performance and R28 integration are pending.

## Floor filtering in motion

Sixteen consecutive camera positions were rendered at 1920×1080 and 3840×2160.
Each run sampled three fixed crops. A separate material-ID pass identified the
near floor, distant floor, and right metal strip. For each crop, compare the
frame-to-frame change in display luma against the same change in a box-averaged
7680×4320 reference. The temporal score is the mean absolute difference of those
changes on pixels that belong to the target material in both frames. Lower is
closer to the reference. These are renderer comparisons, on the 0–255 luma scale.

Distant floor scores with the 8K / 16× reference:

| Output | 4× AF | 8× AF | 16× AF |
| --- | ---: | ---: | ---: |
| 1080p | 3.064 | 1.530 | 0.663 |
| 2160p | 3.188 | 1.511 | 0.462 |

The 8K / 4× reference gave the same ranking. Near-floor and metal-strip scores
tied at each output resolution. The new profile reproduced all 32 winning
captures byte-for-byte. See [both references and all crops](filter_motion_results.csv).

To reproduce on the staged private project, run separate Godot processes for
each AF setting. In `project.godot` under `[rendering]`, set
`textures/default_filters/anisotropic_filtering_level` to 2, 3 or 4 for 4×,
8× or 16×. The Compatibility sampler used the startup setting on the test device.
Use a new absolute capture directory for each run. A small window is sufficient
because the script draws into a full-resolution offscreen viewport.

```sh
godot --path "/path/to/private/HMO1-enhanced" --resolution 128x128 --script "/path/to/checkout/experiments/level3-enhanced-textures/capture_filter_motion.gd" -- 1080 "/path/to/captures/af4-1080"
```

Collect `af{4,8,16}-{1080,2160}`, then `ref4-4320` and `ref16-4320` at
height 4320. For `mask-1080` and `mask-2160`, append `--mask` after the
destination. Restore the chosen profile (setting 4). From the experiment
directory, run `python score_filter_motion.py "/path/to/captures"` with NumPy
and Pillow installed.

## Next graphics and audio experiments

| Priority | Experiment | Acceptance in HMO1 |
| --- | --- | --- |
| 1 | Profile the selected 16× sampler on the target Windows GPU. | Record frame times and texture memory on the same route at 1080p and 4K. |
| 2 | Test the gate lighting through the scope and try a soft contact shadow beneath Kurt. | Check the lettering and match shadow position to floor contact during landing. |
| 3 | Give the original mono door, machinery and impact samples positional emitters at confirmed source locations. Keep the music on its stereo bus. | Approach, turn away and cross the gate. Compare left/right localization and the trigger tick with the original event trace. |
| 4 | Blend a short metallic reverb at the interior threshold and offer a reduced-dynamics headphone mix. | Check the transition in both directions, peaks on overlapping effects and audibility of the quietest cue under music. |
