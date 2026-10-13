"""Readers for heart rate, glucose and food logs.

HR timestamps are "2/13/20 15:29" for some participants and ISO for others.
Food_Log_003 has no header row and 11 columns instead of 14.
"""

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PARTICIPANTS = [f"{i:03d}" for i in range(1, 17)]


def parse_times(values):
    values = values.astype(str).str.strip()
    if "/" in values.iloc[0]:
        return pd.to_datetime(values, format="%m/%d/%y %H:%M")
    return pd.to_datetime(values, format="ISO8601")


def load_hr(pid, data_dir=DATA_DIR):
    df = pd.read_csv(data_dir / pid / f"HR_{pid}.csv")
    df.columns = ["time", "hr"]
    minute = parse_times(df["time"]).dt.floor("min")
    return df["hr"].groupby(minute).mean().rename("hr").rename_axis("time")


def load_glucose(pid, data_dir=DATA_DIR):
    df = pd.read_csv(data_dir / pid / f"Dexcom_{pid}.csv")
    df = df[df["Event Type"] == "EGV"]
    time = parse_times(df["Timestamp (YYYY-MM-DDThh:mm:ss)"])
    glucose = pd.to_numeric(df["Glucose Value (mg/dL)"], errors="coerce").to_numpy()
    series = pd.Series(glucose, index=pd.DatetimeIndex(time), name="glucose")
    return series.dropna().sort_index().rename_axis("time")


def load_food(pid, data_dir=DATA_DIR):
    raw = pd.read_csv(data_dir / pid / f"Food_Log_{pid}.csv", header=None, dtype=str)
    if raw.iloc[0, 0] == "date":
        raw = raw.iloc[1:]
    if raw.shape[1] == 14:
        food_col, cal_col, carb_col = 4, 8, 9
    elif raw.shape[1] == 11:
        food_col, cal_col, carb_col = 3, 7, 8
    else:
        raise ValueError(f"unexpected food log layout for {pid}: {raw.shape[1]} columns")
    food = pd.DataFrame({
        "time": parse_times(raw[2]),
        "food": raw[food_col].str.strip(),
        "calories": pd.to_numeric(raw[cal_col], errors="coerce"),
        "carbs": pd.to_numeric(raw[carb_col], errors="coerce"),
    })
    return food.sort_values("time").reset_index(drop=True)
