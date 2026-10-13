import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from stats import auc, per_participant


def test_auc_extremes():
    assert auc([5, 6, 7], [1, 2, 3]) == 1.0
    assert auc([1, 2, 3], [5, 6, 7]) == 0.0
    assert auc([1, 2], [1, 2]) == 0.5


def test_per_participant_difference():
    table = pd.DataFrame({
        "pid": ["001"] * 5,
        "kind": ["meal", "meal", "placebo", "placebo", "placebo"],
        "score": [10.0, 12.0, 1.0, 2.0, 3.0],
    })
    per = per_participant(table, "score")
    assert per.loc[0, "difference"] == 11.0 - 2.0
    assert per.loc[0, "auc"] == 1.0
