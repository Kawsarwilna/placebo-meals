import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from movement import adjust_hr, minutes_since_food, still_fraction


def test_minutes_since_food():
    food = pd.Series(pd.to_datetime(["2020-02-14 07:00", "2020-02-14 12:00"]))
    times = pd.DatetimeIndex(["2020-02-14 06:00", "2020-02-14 08:00", "2020-02-14 13:30"])
    since = minutes_since_food(times, food)
    assert np.isinf(since[0])
    assert list(since[1:]) == [60, 90]


def test_adjusted_hr_removes_movement_driven_heart_rate():
    rng = np.random.default_rng(0)
    index = pd.date_range("2020-02-14 00:00", periods=3000, freq="1min")
    movement = pd.Series(rng.uniform(0, 0.3, len(index)), index=index)
    hr = 60 + 100 * movement + rng.normal(0, 1, len(index))
    adjusted, r2 = adjust_hr(hr, movement, pd.Series(pd.to_datetime(["2020-02-13 00:00"])))
    assert r2 > 0.8
    assert adjusted.std() < 1.5


def test_still_fraction():
    index = pd.date_range("2020-02-14 07:00", periods=90, freq="1min")
    movement = pd.Series([0.01] * 60 + [0.3] * 30, index=index)
    t = pd.Timestamp("2020-02-14 07:00")
    assert still_fraction(movement, t, 0, 60, threshold=0.05) == 1.0
    assert still_fraction(movement, t, 30, 90, threshold=0.05) == 0.5
    assert np.isnan(still_fraction(movement, t, 60, 180, threshold=0.05))
