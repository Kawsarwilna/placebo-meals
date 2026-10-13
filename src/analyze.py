"""Build the table of real-meal and placebo windows with their heart rate and glucose responses."""

import pandas as pd

from load import PARTICIPANTS, load_food, load_glucose, load_hr
from meals import clean_meals, group_meals, placebo_times
from response import responses

MIN_MEALS = 3


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
    out.insert(0, "pid", pid)
    return out


def all_windows():
    table = pd.concat([participant_windows(pid) for pid in PARTICIPANTS], ignore_index=True)
    table = table.dropna(subset=["hr_peak", "glucose_peak"]).reset_index(drop=True)
    meal_counts = table[table["kind"] == "meal"].groupby("pid").size()
    included = meal_counts[meal_counts >= MIN_MEALS].index
    return table[table["pid"].isin(included)].reset_index(drop=True)
