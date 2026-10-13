"""Stream the wrist accelerometer files and keep only a per-minute movement summary.

The raw ACC files are about 13 GB in total, so they are never stored. Each file is
streamed once, checked against the published v1.1.3 checksum and reduced to one row
per minute in data/motion/. A summary is only written once its checksum matches.

Usage:
    python src/motion.py
"""

import hashlib
import io
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from download import BASE_URL, MIRROR_URL, load_checksums
from load import DATA_DIR, PARTICIPANTS

MOTION_DIR = DATA_DIR / "motion"
E4_UNITS_PER_G = 64.0
CHUNK_ROWS = 1_000_000


class HashingStream(io.RawIOBase):
    """Passes bytes through while computing their SHA-256."""

    def __init__(self, raw):
        self.raw = raw
        self.sha = hashlib.sha256()

    def readable(self):
        return True

    def readinto(self, buffer):
        data = self.raw.read(len(buffer))
        buffer[: len(data)] = data
        self.sha.update(data)
        return len(data)


def minute_sums(chunk):
    """Per-minute sample count and sums of acceleration magnitude (g) and its square."""
    magnitude = np.sqrt(chunk["x"] ** 2 + chunk["y"] ** 2 + chunk["z"] ** 2) / E4_UNITS_PER_G
    sums = pd.DataFrame({
        "minute": chunk["time"].str.slice(0, 16),
        "samples": 1,
        "sum": magnitude,
        "sum_sq": magnitude ** 2,
    })
    return sums.groupby("minute").sum()


def summarize_stream(stream):
    """Read an ACC csv from a binary stream; return one row per minute with the movement SD."""
    reader = pd.read_csv(
        stream, header=0, names=["time", "x", "y", "z"], chunksize=CHUNK_ROWS,
        dtype={"time": str, "x": "float32", "y": "float32", "z": "float32"},
    )
    totals = pd.concat([minute_sums(chunk) for chunk in reader]).groupby(level=0).sum()
    mean = totals["sum"] / totals["samples"]
    variance = (totals["sum_sq"] / totals["samples"] - mean ** 2).clip(lower=0)
    return pd.DataFrame({
        "time": pd.to_datetime(totals.index, format="%Y-%m-%d %H:%M"),
        "samples": totals["samples"].to_numpy(),
        "movement": np.sqrt(variance).to_numpy(),
    })


def stream_one(name, expected, dest):
    for url in (MIRROR_URL, BASE_URL):
        with urllib.request.urlopen(url + name, timeout=120) as response:
            hashing = HashingStream(response)
            buffered = io.BufferedReader(hashing, buffer_size=1 << 20)
            summary = summarize_stream(buffered)
            buffered.read()
        if hashing.sha.hexdigest() == expected:
            summary.to_csv(dest, index=False)
            return
    raise RuntimeError(f"no copy matching the v1.1.3 checksum: {name}")


def main():
    MOTION_DIR.mkdir(parents=True, exist_ok=True)
    sums = load_checksums()
    started = time.time()

    def work(pid):
        name = f"{pid}/ACC_{pid}.csv"
        dest = MOTION_DIR / f"Motion_{pid}.csv"
        if dest.exists():
            print(f"ok   {name}", flush=True)
            return
        stream_one(name, sums[name], dest)
        print(f"got  {name} ({(time.time() - started) / 60:.1f} min)", flush=True)

    with ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(work, PARTICIPANTS))


if __name__ == "__main__":
    main()
