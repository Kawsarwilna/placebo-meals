import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from response import window_response


def minute_series(start, values):
    index = pd.date_range(start, periods=len(values), freq="1min")
    return pd.Series(values, index=index, dtype=float)


def test_flat_then_bump():
    values = [70] * 30 + [70] * 30 + [80] * 60 + [70] * 90
    series = minute_series("2020-02-14 06:30", values)
    r = window_response(series, pd.Timestamp("2020-02-14 07:00"), step_min=1)
    assert r["baseline"] == 70
    assert r["peak"] == 10
    assert r["time_to_peak"] == 30
    assert r["sustained"] == np.mean([80] * 60 + [70] * 31) - 70


def test_missing_data_gives_nan():
    series = minute_series("2020-02-14 06:30", [70] * 60)
    r = window_response(series, pd.Timestamp("2020-02-14 07:00"), step_min=1)
    assert np.isnan(r["peak"])
