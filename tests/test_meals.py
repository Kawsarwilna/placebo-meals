import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from meals import clean_meals, group_meals, placebo_times


def food_log(rows):
    return pd.DataFrame(
        [(pd.Timestamp(t), name, kcal, carbs) for t, name, kcal, carbs in rows],
        columns=["time", "food", "calories", "carbs"],
    )


def test_items_close_together_form_one_meal():
    food = food_log([
        ("2020-02-14 07:10", "Standard Breakfast", 110, 26),
        ("2020-02-14 07:10", "Milk", 120, 9),
        ("2020-02-14 12:30", "Salad", 286, 14),
    ])
    meals = group_meals(food)
    assert len(meals) == 2
    assert meals.loc[0, "calories"] == 230
    assert meals.loc[0, "standard_breakfast"]
    assert not meals.loc[1, "standard_breakfast"]


def test_meal_with_snack_soon_after_is_not_clean():
    food = food_log([
        ("2020-02-14 07:00", "Breakfast", 300, 40),
        ("2020-02-14 08:30", "Snack", 100, 10),
        ("2020-02-14 13:00", "Lunch", 500, 50),
    ])
    meals = group_meals(food)
    clean = clean_meals(meals, food)
    assert list(clean["time"]) == [pd.Timestamp("2020-02-14 13:00")]


def test_placebo_moments_are_not_reused_across_meals():
    food = food_log([
        ("2020-02-14 12:00", "Lunch", 500, 50),
        ("2020-02-15 12:00", "Lunch", 500, 50),
    ])
    placebos = placebo_times(
        [pd.Timestamp("2020-02-14 12:00"), pd.Timestamp("2020-02-15 12:00")], food,
        start=pd.Timestamp("2020-02-14 00:00"), end=pd.Timestamp("2020-02-19 00:00"),
        per_meal=20,
    )
    assert placebos["time"].is_unique


def test_placebos_are_food_free_on_other_days_at_similar_clock_time():
    food = food_log([
        ("2020-02-14 12:00", "Lunch", 500, 50),
        ("2020-02-15 07:00", "Breakfast", 300, 30),
        ("2020-02-15 19:00", "Dinner", 600, 60),
        ("2020-02-16 18:00", "Dinner", 600, 60),
    ])
    placebos = placebo_times(
        [pd.Timestamp("2020-02-14 12:00")], food,
        start=pd.Timestamp("2020-02-14 00:00"), end=pd.Timestamp("2020-02-17 00:00"),
        per_meal=3,
    )
    assert len(placebos) == 3
    for t in placebos["time"]:
        assert t.date() != pd.Timestamp("2020-02-14").date()
        assert abs((t.hour * 60 + t.minute) - 12 * 60) <= 60
        gaps = (food["time"] - t).abs()
        assert (gaps > pd.Timedelta(minutes=120)).all()
