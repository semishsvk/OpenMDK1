"""Stage the HMO1 door from the existing private OpenMDK asset import."""
import hashlib
import io
import json
from pathlib import Path

from PIL import Image

MODEL = "model_assets/models/L3_MTO_000_HMO_1_model_0004_XH1_DOOR.json"
ANIMATION = "model_assets/animations/L3_MTO_000_HMO_1_animation_0000_XH1_DOOR.json"
SOUND = "audio_r2/MTO/LEVEL3/HMO_1/0000_DOORLAND.wav"
TEXTURE = "textures_r2/MTO/LEVEL3/HMO_1/0020_XH1_DOOR.png"

INPUTS = {
    MODEL: "243b1d261235454f85c33a61a4b0c2f8c2af68034a024f2bdb3b8d6b81997fe5",
    ANIMATION: "debd6c2dcba41fd39a472bfb5b283924d0a4eb2f2e12cf7784fcbac8a88e3dfb",
    SOUND: "487c306cc13470768351e6981612f2ef9098fbe199644d8206088402df49f627",
    TEXTURE: "6ea1b9703659dbcd24b1bad713813824d54ed514b1f623eadff9262434651937",
}


def prepare_door(import_root: Path, stage: Path):
    inputs = {}
    for relative, expected in INPUTS.items():
        data = (import_root / relative).read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError(f"Unexpected HMO1 door asset: {relative}")
        inputs[relative] = data
    # Use the validated IR from the asset import; the packed retail mesh needs no second decoder.
    model = json.loads(inputs[MODEL])
    anim = json.loads(inputs[ANIMATION])
    track, = anim["tracks"]
    part, = [p for p in model["parts"] if p["name"] == track["name"]]
    if part["vertices"] != track["base_vertices"]:
        raise ValueError("Door mesh and animation have different base poses.")
    deltas = {d["frame"]: d["vertex_deltas_s8"] for d in track["delta_records"]}
    pose = track["base_vertices"]
    frames = [pose]
    for frame in range(1, anim["frame_count"]):
        if frame in deltas:
            pose = [[v + dv * track["scale_f32"] for v, dv in zip(vertex, delta)]
                    for vertex, delta in zip(pose, deltas[frame])]
        frames.append(pose)
    faces = [{"indices": f["vertex_indices"], "material": f["material_s16"], "uv": f["uv_texels"]}
             for f in part["faces"]]
    out = stage / "door"
    out.mkdir()
    (out / "panel.json").write_text(json.dumps({"fps": anim["nominal_fps_from_upstream"],
                                                "frames": frames, "faces": faces},
                                               separators=(",", ":")) + "\n")
    (out / "doorland.wav").write_bytes(inputs[SOUND])
    # Godot may otherwise choose lossy QOA for this short 8-bit PCM recording.
    (out / "doorland.wav.import").write_text(
        '[remap]\nimporter="wav"\ntype="AudioStreamWAV"\n[params]\n'
        'compress/mode=0\nforce/8_bit=true\nedit/trim=false\nedit/normalize=false\n')
    with Image.open(io.BytesIO(inputs[TEXTURE])) as texture:
        texture.convert("RGB").save(out / "panel.png")
