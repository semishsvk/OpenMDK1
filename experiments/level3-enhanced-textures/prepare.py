"""Stage the BF11AK experiment from a private, read-only HMO1 asset directory."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory

from PIL import Image, __version__ as pillow_version

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
BASE = REPO / "recovered/2026-10-09/slice-AK/project"
SCALE = 4


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def upscale_tile(image):
    """Give Lanczos its three-pixel neighbourhood across both UV repeat edges."""
    width, height = image.size
    pad = 3
    wrapped = Image.new("RGB", (width + 2 * pad, height + 2 * pad))
    for y in (-height, 0, height):
        for x in (-width, 0, width):
            wrapped.paste(image, (pad + x, pad + y))
    # The box selects exactly the central tile. Pillow samples its wrapped border.
    return wrapped.resize((width * SCALE, height * SCALE), Image.Resampling.LANCZOS,
                          box=(pad, pad, pad + width, pad + height))


def prepare(source, output):
    source = source.resolve(strict=True)
    output = output.resolve()
    if output.exists() or output.is_relative_to(source) or output.is_relative_to(REPO):
        raise ValueError("Choose a new private directory outside the input and checkout.")
    pins = json.loads((HERE / "inputs.json").read_text())
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=output.parent, prefix=".openmdk-textures-") as temporary:
        stage = Path(temporary) / "project"
        (stage / "textures").mkdir(parents=True)
        (stage / "enhanced").mkdir()
        enhanced = {}
        for relative, expected in pins.items():
            target = stage / relative
            shutil.copyfile(source / relative, target)
            if sha256(target) != expected:
                raise ValueError(f"Input differs from the BF11AK snapshot: {relative}")
            if target.suffix != ".png":
                continue
            result = stage / "enhanced" / target.name
            with Image.open(target) as image:
                if image.mode != "RGB":
                    raise ValueError(f"Expected opaque RGB artwork: {relative}")
                upscale_tile(image).save(result, compress_level=9)
                enhanced[target.stem] = {
                    "source_sha256": expected, "output_sha256": sha256(result),
                    "source_size": list(image.size),
                    "output_size": [v * SCALE for v in image.size],
                }
            # Keep disk storage lossless and supply the chain used by the 3D sampler.
            (result.with_suffix(".png.import")).write_text(
                '[remap]\nimporter="texture"\ntype="CompressedTexture2D"\n'
                '[params]\ncompress/mode=0\nmipmaps/generate=true\ndetect_3d/compress_to=0\n')
        for name in ("main.gd", "collision.gd", "portal.gd", "activation.gd"):
            shutil.copyfile(BASE / name, stage / name)
        for name in ("project.godot", "main.tscn", "enhanced_slice.gd", "gate_lamps.gdshader"):
            shutil.copyfile(HERE / name, stage / name)
        manifest = {"recipe": "periodic-lanczos-4x", "pillow": pillow_version, "textures": enhanced}
        (stage / "enhanced/manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        # Windows rename is exclusive. On POSIX reserve the target before replacing
        # the *empty directory we created*, so two prepares cannot both publish.
        if os.name == "nt":
            stage.rename(output)
        else:
            output.mkdir()
            try:
                os.replace(stage, output)
            except OSError:
                output.rmdir()
                raise
    return enhanced


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Private BF11AK project with hmo1.json and textures/")
    parser.add_argument("output", type=Path, help="New private Godot project directory")
    args = parser.parse_args()
    textures = prepare(args.source, args.output)
    print(f"Prepared {len(textures)} 4x textures in {args.output}")
