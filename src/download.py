"""Download the BIG IDEAs files this project needs from PhysioNet into data/.

Usage:
    python src/download.py           # HR, Dexcom, Food_Log (~250 MB)
    python src/download.py --extra   # also TEMP and EDA (~2.5 GB more)
"""

import hashlib
import sys
import urllib.request
from pathlib import Path

BASE_URL = "https://physionet.org/files/big-ideas-glycemic-wearable/1.1.3/"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PARTICIPANTS = [f"{i:03d}" for i in range(1, 17)]
CORE = ["HR", "Dexcom", "Food_Log"]
EXTRA = ["TEMP", "EDA"]


def load_checksums():
    text = urllib.request.urlopen(BASE_URL + "SHA256SUMS.txt", timeout=60).read().decode()
    sums = {}
    for line in text.splitlines():
        if line.strip():
            digest, name = line.split(maxsplit=1)
            sums[name.strip()] = digest
    return sums


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(name, expected):
    dest = DATA_DIR / name
    if dest.exists() and sha256(dest) == expected:
        print(f"ok   {name}")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    urllib.request.urlretrieve(BASE_URL + name, tmp)
    if sha256(tmp) != expected:
        tmp.unlink()
        raise RuntimeError(f"checksum mismatch: {name}")
    tmp.rename(dest)
    print(f"got  {name}")


def main():
    kinds = CORE + (EXTRA if "--extra" in sys.argv else [])
    sums = load_checksums()
    names = ["Demographics.csv"] + [f"{p}/{k}_{p}.csv" for p in PARTICIPANTS for k in kinds]
    for name in names:
        fetch(name, sums[name])


if __name__ == "__main__":
    main()
