"""Build the table of real-meal and placebo windows with their heart rate and glucose responses."""

import numpy as np
import pandas as pd

from load import PARTICIPANTS, load_food, load_glucose, load_hr
from meals import clean_meals, group_meals, placebo_times
from movement import STILL_THRESHOLD, adjust_hr, load_movement, still_fraction
from response import POST_MIN, PRE_MIN, SUSTAINED_FROM_MIN, SUSTAINED_TO_MIN, responses

MIN_MEALS = 3
CURVE_STEP_MIN = 5
CURVE_MINUTES = np.arange(-PRE_MIN, POST_MIN, CURVE_STEP_MIN)


def participant_windows(pid):
    hr, glucose, food = load_hr(pid), load_glucose(pid), load_food(pid)
    meals = clean_meals(group_meals(food), food)

    # Placebos must fall where all three records overlap; outside the food log
    # period we can't know whether the person ate.
    start = max(hr.index.min(), glucose.index.min(), food["time"].min())
    end = min(hr.index.max(), glucose.index.max(), food["time"].max())
    placebos = placebo_times(meals["time"], food, start, end)

    real = meals[["time", "calories", "carbs", "standard_breakfast"]].assign(
        kind="meal", meal_index=range(len(meals))
    )
    windows = pd.concat([real, placebos.assign(kind="placebo")], ignore_index=True)
    hr_resp = responses(hr, windows["time"], step_min=1).add_prefix("hr_")
    glucose_resp = responses(glucose, windows["time"], step_min=5).add_prefix("glucose_")
    out = pd.concat([windows, hr_resp, glucose_resp], axis=1)
    # Exploratory, not one of the fixed rules: peak after smoothing out one-minute spikes.
    out["hr_peak_smooth"] = responses(hr.rolling("5min").mean(), windows["time"], step_min=1)["peak"]

    movement = load_movement(pid)
    adjusted, r2 = adjust_hr(hr, movement, food["time"])
    adjusted_resp = responses(adjusted, windows["time"], step_min=1)
    out["hr_adj_peak"] = adjusted_resp["peak"]
    out["hr_adj_sustained"] = adjusted_resp["sustained"]
    out["movement_r2"] = r2
    out["still_before"] = [still_fraction(movement, t, -PRE_MIN, 0, STILL_THRESHOLD) for t in windows["time"]]
    out["still_after"] = [
        still_fraction(movement, t, SUSTAINED_FROM_MIN, SUSTAINED_TO_MIN, STILL_THRESHOLD) for t in windows["time"]
    ]
    out.insert(0, "pid", pid)
    return out


def all_windows():
    table = pd.concat([participant_windows(pid) for pid in PARTICIPANTS], ignore_index=True)
    table = table.dropna(subset=["hr_peak", "glucose_peak"]).reset_index(drop=True)
    meal_counts = table[table["kind"] == "meal"].groupby("pid").size()
    included = meal_counts[meal_counts >= MIN_MEALS].index
    return table[table["pid"].isin(included)].reset_index(drop=True)


def lowest_hr_hour(pid):
    """Clock hour with the lowest mean heart rate; overnight if device clocks are local time."""
    hr = load_hr(pid)
    return int(hr.groupby(hr.index.hour).mean().idxmin())


def food_glucose_overlap_hours(pid):
    food, glucose = load_food(pid), load_glucose(pid)
    start = max(food["time"].min(), glucose.index.min())
    end = min(food["time"].max(), glucose.index.max())
    return max((end - start) / pd.Timedelta(hours=1), 0.0)


def event_curve(series, t):
    """Change from the 30-min baseline, in 5-min bins from -30 to +180 min around t."""
    window = series[t - pd.Timedelta(minutes=PRE_MIN): t + pd.Timedelta(minutes=POST_MIN) - pd.Timedelta(seconds=1)]
    relative = (window.index - t) / pd.Timedelta(minutes=1)
    bins = np.floor(relative / CURVE_STEP_MIN) * CURVE_STEP_MIN
    binned = window.groupby(bins).mean().reindex(CURVE_MINUTES)
    return binned - binned[binned.index < 0].mean()


def curves(table):
    """Per participant, the mean event curve for real meals and placebo moments."""
    rows = []
    for pid, windows in table.groupby("pid"):
        hr = load_hr(pid)
        adjusted, _ = adjust_hr(hr, load_movement(pid), load_food(pid)["time"])
        signals = {"hr": hr, "glucose": load_glucose(pid), "hr_adjusted": adjusted}
        for signal, series in signals.items():
            for kind, group in windows.groupby("kind"):
                stacked = np.vstack([event_curve(series, t).to_numpy() for t in group["time"]])
                for minute, change in zip(CURVE_MINUTES, np.nanmean(stacked, axis=0)):
                    rows.append({"pid": pid, "signal": signal, "kind": kind, "minute": minute, "change": change})
    return pd.DataFrame(rows)
