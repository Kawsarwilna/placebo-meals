import numpy as np
import pandas as pd

from load import DATA_DIR

MOTION_DIR = DATA_DIR / "motion"
SAMPLES_PER_MINUTE = 32 * 60
FIT_MIN_SINCE_FOOD = 180
FEATURES = ["now", "last_5", "last_6_15"]
# No candidate kept 8 participants (see ANALYSIS_PLAN.md), so the still-period
# check uses the loosest one and counts as exploratory.
STILL_THRESHOLD = 0.1  # g
STILL_SHARE = 0.8
MIN_STILL_PARTICIPANTS = 8


def load_movement(pid, motion_dir=MOTION_DIR):
    df = pd.read_csv(motion_dir / f"Motion_{pid}.csv", parse_dates=["time"])
    df = df[df["samples"] >= SAMPLES_PER_MINUTE * 2 / 3]
    return df.set_index("time")["movement"]


def movement_features(movement):
    # heart rate lags movement, so the model also sees the previous 15 minutes
    m = movement.asfreq("1min")
    return pd.DataFrame({
        "now": m,
        "last_5": m.shift(1).rolling(5, min_periods=3).mean(),
        "last_6_15": m.shift(6).rolling(10, min_periods=6).mean(),
    })


def minutes_since_food(times, food_times):
    food = np.sort(food_times.to_numpy())
    idx = np.searchsorted(food, times.to_numpy(), side="right") - 1
    since = np.full(len(times), np.inf)
    has_food = idx >= 0
    since[has_food] = (times.to_numpy()[has_food] - food[idx[has_food]]) / np.timedelta64(1, "m")
    return since


def adjust_hr(hr, movement, food_times):
    # Fit only on minutes well after any food, so a meal effect can't leak into the model.
    # Returns the residual heart rate and the fit's R squared.
    data = movement_features(movement).join(hr.rename("hr"), how="inner").dropna()
    fit = data[minutes_since_food(data.index, food_times) >= FIT_MIN_SINCE_FOOD]
    design = np.column_stack([np.ones(len(fit)), fit[FEATURES].to_numpy()])
    coef, *_ = np.linalg.lstsq(design, fit["hr"].to_numpy(), rcond=None)
    predicted_fit = design @ coef
    r2 = 1 - np.sum((fit["hr"] - predicted_fit) ** 2) / np.sum((fit["hr"] - fit["hr"].mean()) ** 2)
    predicted = np.column_stack([np.ones(len(data)), data[FEATURES].to_numpy()]) @ coef
    return (data["hr"] - predicted).rename("hr_adjusted"), float(r2)


def still_fraction(movement, t, start_min, end_min, threshold):
    window = movement[t + pd.Timedelta(minutes=start_min): t + pd.Timedelta(minutes=end_min) - pd.Timedelta(seconds=1)]
    if len(window) < (end_min - start_min) * 2 / 3:
        return np.nan
    return float((window < threshold).mean())
