"""Measure both impacts in a 60 FPS verify_door Movie Maker capture."""
import argparse
import json
import math
from pathlib import Path
import subprocess
import wave

import numpy as np
from scipy.signal import correlate, resample_poly

RATE = 48000


def measure(movie, log, original):
    record, = [json.loads(line.removeprefix("HMO1_DOOR_QA ")) for line in
               log.read_text().splitlines() if line.startswith("HMO1_DOOR_QA ")]
    if record["failures"]:
        raise ValueError(f"Scene test failed: {record['failures']}")
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(movie), "-map", "0:a:0",
                                  "-ac", "2", "-ar", str(RATE), "-f", "s16le", "pipe:1"])
    mix = np.frombuffer(raw, dtype="<i2").reshape(-1, 2).astype(np.float64) / 32768
    with wave.open(str(original), "rb") as wav:
        if (wav.getframerate(), wav.getnchannels(), wav.getsampwidth()) != (22050, 1, 1):
            raise ValueError("Expected the original mono 22050 Hz 8-bit DOORLAND recording.")
        sample = np.frombuffer(wav.readframes(wav.getnframes()), dtype=np.uint8).astype(float) - 128
    template = resample_poly(sample, 320, 147)[:int(0.13 * RATE)]
    result = {}
    for shot in record["shots"]:
        onsets = []
        for event in shot["events"]:
            expected = round(event["movie"] * RATE / 60)
            start = expected - RATE // 10
            window = mix[start:expected + 3 * RATE // 10].mean(axis=1)
            corr = correlate(window, template, mode="valid", method="fft")
            pos = int(np.argmax(corr))
            match = window[pos:pos + len(template)]
            similarity = np.dot(match, template) / (np.linalg.norm(match) * np.linalg.norm(template))
            if not similarity > 0.7:
                raise ValueError(f"No matching impact in {shot['name']} at cue {event['cue']}")
            onsets.append(start + pos)
        if len(onsets) != 2 or abs((onsets[1] - onsets[0]) - 22400) > 1:
            raise ValueError(f"Incorrect audio onset spacing in {shot['name']}: {onsets}")
        isolated = mix[onsets[0]:onsets[0] + int(0.4 * RATE)]
        left, right = np.sqrt(np.mean(isolated ** 2, axis=0))
        if min(left, right) <= 0:
            raise ValueError("Silent channel")
        result[shot["name"]] = {
            "spacing_at_48k": onsets[1] - onsets[0],
            "left_minus_right_db": round(20 * math.log10(left / right), 3),
            "rms_dbfs": round(20 * math.log10(np.sqrt((left ** 2 + right ** 2) / 2)), 3),
        }
    if not (result["left"]["left_minus_right_db"] > 1 and result["right"]["left_minus_right_db"] < -1
            and abs(result["centre"]["left_minus_right_db"]) < 0.1
            and result["far"]["rms_dbfs"] < result["centre"]["rms_dbfs"] - 3):
        raise ValueError(f"Spatial check failed: {result}")
    peak = np.abs(mix).max()
    if not 0 < peak < 32767 / 32768:
        raise ValueError("Silent or clipped capture")
    return {"sample_rate": RATE, "shots": result, "peak_dbfs": round(20 * math.log10(peak), 3)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("movie", "log", "original_wav"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    print(json.dumps(measure(args.movie, args.log, args.original_wav), indent=2))
