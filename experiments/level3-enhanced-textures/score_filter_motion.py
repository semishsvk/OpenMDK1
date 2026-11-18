"""Compare private HMO1 crops against display-space box averages of the 8K renders."""
import argparse
from pathlib import Path

import numpy as np
from PIL import Image

FRAME_COUNT = 16
PATCHES = ("near floor", "distant floor", "right strip")


def read_frames(folder, scale):
    frames = []
    for i in range(FRAME_COUNT):
        with Image.open(folder / f"{i:02d}.png") as image:
            if image.size != (128 * scale, 144 * scale):
                raise ValueError(f"Wrong crop dimensions: {image.filename}")
            frames.append(np.asarray(image.convert("RGB")))
    return np.stack(frames)


def luma(frames):
    return frames @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)


def score(root):
    for ref_af in (4, 16):
        ref = luma(read_frames(root / f"ref{ref_af}-4320", 4))
        for height in (1080, 2160):
            scale = height // 1080
            reduction = 4 // scale
            reference = ref.reshape(FRAME_COUNT, 144 * scale, reduction,
                                    128 * scale, reduction).mean(axis=(2, 4))
            ids = read_frames(root / f"mask-{height}", scale)
            for af in (4, 8, 16):
                result = luma(read_frames(root / f"af{af}-{height}", scale))
                for row, patch in enumerate(PATCHES):
                    band = slice(row * 48 * scale, (row + 1) * 48 * scale)
                    color = [0, 255, 0] if row == 2 else [255, 0, 0]
                    valid = (ids[:, band] == color).all(axis=-1)
                    common = valid[1:] & valid[:-1]
                    if valid.mean() < 0.75 or not common.any():
                        raise ValueError(f"Insufficient material coverage: {height} {patch}")
                    residual = result[:, band] - reference[:, band]
                    spatial = np.abs(residual[valid]).mean()
                    temporal = np.abs(np.diff(residual, axis=0)[common]).mean()
                    yield (ref_af, height, af, patch, valid.mean(), spatial, temporal)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("captures", type=Path)
    print("reference_af,height,af,patch,material_coverage,spatial_mae,temporal_delta_mae")
    for ref, h, af, patch, coverage, spatial, temporal in score(parser.parse_args().captures):
        print(f"{ref},{h},{af},{patch},{coverage:.4f},{spatial:.5f},{temporal:.5f}")
