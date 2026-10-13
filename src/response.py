"""Score how a signal changes after a moment in time (a meal or a placebo moment)."""

import numpy as np
import pandas as pd

PRE_MIN = 30
POST_MIN = 180
SUSTAINED_FROM_MIN = 30
SUSTAINED_TO_MIN = 120
MIN_COVERAGE = 2 / 3


def window_response(series, t, step_min):
    """Change in `series` after time t, relative to the 30 minutes before.

    peak:      highest value in the 3 h after, minus the baseline
    sustained: mean from 30 to 120 min after, minus the baseline
    Returns NaNs when either window has less than 2/3 of its expected samples.
    """
    minute = pd.Timedelta(minutes=1)
    pre = series[t - PRE_MIN * minute: t - pd.Timedelta(seconds=1)]
    post = series[t: t + POST_MIN * minute]
    sustained = series[t + SUSTAINED_FROM_MIN * minute: t + SUSTAINED_TO_MIN * minute]
    enough = (
        len(pre) >= MIN_COVERAGE * PRE_MIN / step_min
        and len(post) >= MIN_COVERAGE * POST_MIN / step_min
    )
    if not enough:
        return {"baseline": np.nan, "peak": np.nan, "sustained": np.nan, "time_to_peak": np.nan}
    baseline = pre.mean()
    return {
        "baseline": baseline,
        "peak": post.max() - baseline,
        "sustained": sustained.mean() - baseline,
        "time_to_peak": (post.idxmax() - t) / minute,
    }


def responses(series, times, step_min):
    return pd.DataFrame([window_response(series, t, step_min) for t in times])
