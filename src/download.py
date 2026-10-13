"""Download the BIG IDEAs files this project needs from PhysioNet into data/.

Usage:
    python src/download.py           # HR, Dexcom, Food_Log (~250 MB)
    python src/download.py --extra   # also TEMP and EDA (~2.5 GB more)
"""

import hashlib
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE_URL = "https://physionet.org/files/big-ideas-glycemic-wearable/1.1.3/"
# PhysioNet's AWS mirror is much faster but only has v1.1.2. Files from it are
# kept only if they match the v1.1.3 checksums; otherwise we fall back to BASE_URL.
MIRROR_URL = "https://physionet-open.s3.amazonaws.com/big-ideas-glycemic-wearable/1.1.2/"
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
        print(f"ok   {name}", flush=True)
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    for url in (MIRROR_URL, BASE_URL):
        try:
            urllib.request.urlretrieve(url + name, tmp)
        except urllib.error.HTTPError:
            continue
        if sha256(tmp) == expected:
            tmp.rename(dest)
            print(f"got  {name}", flush=True)
            return
    tmp.unlink(missing_ok=True)
    raise RuntimeError(f"no copy matching the v1.1.3 checksum: {name}")


def main():
    kinds = CORE + (EXTRA if "--extra" in sys.argv else [])
    sums = load_checksums()
    names = ["Demographics.csv"] + [f"{p}/{k}_{p}.csv" for p in PARTICIPANTS for k in kinds]
    # PhysioNet throttles each connection, so download several files at once.
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda name: fetch(name, sums[name]), names))


if __name__ == "__main__":
    main()
