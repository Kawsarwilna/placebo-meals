import hashlib
import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from motion import HashingStream, summarize_stream


def test_stream_is_hashed_and_summarized_per_minute():
    text = (
        "datetime, acc_x, acc_y, acc_z\n"
        "2020-02-13 15:28:50.000000,0.0,0.0,64.0\n"
        "2020-02-13 15:28:50.031250,0.0,0.0,64.0\n"
        "2020-02-13 15:29:00.000000,0.0,0.0,64.0\n"
        "2020-02-13 15:29:00.031250,0.0,0.0,128.0\n"
    ).encode()
    hashing = HashingStream(io.BytesIO(text))
    buffered = io.BufferedReader(hashing)
    summary = summarize_stream(buffered)
    buffered.read()

    assert hashing.sha.hexdigest() == hashlib.sha256(text).hexdigest()
    assert list(summary["time"]) == [pd.Timestamp("2020-02-13 15:28"), pd.Timestamp("2020-02-13 15:29")]
    assert list(summary["samples"]) == [2, 2]
    assert summary.loc[0, "movement"] == 0
    assert np.isclose(summary.loc[1, "movement"], 0.5)
