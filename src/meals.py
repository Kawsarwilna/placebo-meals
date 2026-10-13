"""Turn food log items into meals and pick meals and placebo moments with clean windows."""

import numpy as np
import pandas as pd

MEAL_GAP_MIN = 30
CLEAN_BEFORE_MIN = 120
CLEAN_AFTER_MIN = 180


def group_meals(food, gap_min=MEAL_GAP_MIN):
    """Items logged within `gap_min` minutes of the previous item form one meal."""
    food = food.sort_values("time")
    meal_id = (food["time"].diff() > pd.Timedelta(minutes=gap_min)).cumsum()
    meals = food.groupby(meal_id).agg(
        time=("time", "first"),
        end=("time", "last"),
        calories=("calories", "sum"),
        carbs=("carbs", "sum"),
        items=("food", list),
    )
    meals["standard_breakfast"] = meals["items"].apply(
        lambda items: any("standard breakfast" in str(item).lower() for item in items)
    )
    return meals.reset_index(drop=True)


def food_free(times, eating_times, before=CLEAN_BEFORE_MIN, after=CLEAN_AFTER_MIN, ignore=None):
    """For each time t, True if nothing was eaten in [t - before, t + after].

    `ignore` is an optional (start, end) pair per time whose own items don't count,
    so a meal can be checked against everything except itself.
    """
    eating = np.sort(eating_times.to_numpy())
    result = []
    for i, t in enumerate(times):
        lo, hi = t - pd.Timedelta(minutes=before), t + pd.Timedelta(minutes=after)
        nearby = eating[(eating >= lo) & (eating <= hi)]
        if ignore is not None:
            start, end = ignore[i]
            nearby = nearby[(nearby < start) | (nearby > end)]
        result.append(len(nearby) == 0)
    return np.array(result, dtype=bool)


def clean_meals(meals, food):
    """Meals with nothing else eaten in the 2 h before or the 3 h after they start."""
    keep = food_free(meals["time"], food["time"], ignore=list(zip(meals["time"], meals["end"])))
    return meals[keep].reset_index(drop=True)


def placebo_times(meal_times, food, start, end, per_meal=5, max_clock_diff_min=60, step_min=5, seed=0):
    """Pick placebo moments matched to each meal's time of day.

    Candidates are times on a `step_min` grid between `start` and `end` that are
    food free (same rule as clean meals), on a different date than the meal, and
    within `max_clock_diff_min` of the meal's clock time.
    """
    rng = np.random.default_rng(seed)
    grid = pd.Series(pd.date_range(start.ceil(f"{step_min}min"), end, freq=f"{step_min}min"))
    grid = grid[food_free(grid, food["time"])]
    grid_minutes = grid.dt.hour * 60 + grid.dt.minute

    rows = []
    for meal_index, t in enumerate(meal_times):
        meal_minutes = t.hour * 60 + t.minute
        diff = (grid_minutes - meal_minutes).abs()
        diff = np.minimum(diff, 1440 - diff)
        options = grid[(diff <= max_clock_diff_min) & (grid.dt.date != t.date())]
        chosen = options.sample(n=min(per_meal, len(options)), random_state=rng) if len(options) else options
        rows += [{"meal_index": meal_index, "time": c} for c in chosen]
    return pd.DataFrame(rows, columns=["meal_index", "time"])
