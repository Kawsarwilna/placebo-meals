import numpy as np
import pandas as pd

PRE_MIN = 30
POST_MIN = 180
SUSTAINED_FROM_MIN = 30
SUSTAINED_TO_MIN = 120
MIN_COVERAGE = 2 / 3


def window_response(series, t, step_min):
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
