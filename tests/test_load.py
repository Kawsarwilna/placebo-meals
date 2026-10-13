import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from load import load_food, load_glucose, load_hr


def write(tmp_path, pid, name, text):
    folder = tmp_path / pid
    folder.mkdir(exist_ok=True)
    (folder / f"{name}_{pid}.csv").write_text(text)


def test_hr_minute_format_is_averaged_per_minute(tmp_path):
    write(tmp_path, "001", "HR", "datetime, hr\n2/13/20 15:29,80\n2/13/20 15:29,90\n2/13/20 15:30,70\n")
    hr = load_hr("001", tmp_path)
    assert list(hr.index) == [pd.Timestamp("2020-02-13 15:29"), pd.Timestamp("2020-02-13 15:30")]
    assert list(hr) == [85, 70]


def test_hr_iso_format(tmp_path):
    write(tmp_path, "002", "HR", "datetime, hr\n2020-02-21 09:19:16,60\n2020-02-21 09:19:50,62\n")
    hr = load_hr("002", tmp_path)
    assert hr.loc[pd.Timestamp("2020-02-21 09:19")] == 61


def test_glucose_keeps_only_numeric_readings(tmp_path):
    header = "Index,Timestamp (YYYY-MM-DDThh:mm:ss),Event Type,Glucose Value (mg/dL)\n"
    rows = "1,,FirstName,\n2,2020-02-13 17:23:32,EGV,61.0\n3,2020-02-13 17:28:32,EGV,Low\n"
    write(tmp_path, "001", "Dexcom", header + rows)
    glucose = load_glucose("001", tmp_path)
    assert list(glucose) == [61.0]


def test_food_log_with_header(tmp_path):
    header = "date,time,time_begin,time_end,logged_food,amount,unit,searched_food,calorie,total_carb,dietary_fiber,sugar,protein,total_fat\n"
    row = "2020-02-14,07:10:00,2020-02-14 07:10:00,,Standard Breakfast,0.75,cup,Frosted Flakes,110.0,26.0,,10.0,1.0,\n"
    write(tmp_path, "001", "Food_Log", header + row)
    food = load_food("001", tmp_path)
    assert food.loc[0, "food"] == "Standard Breakfast"
    assert food.loc[0, "calories"] == 110.0
    assert food.loc[0, "carbs"] == 26.0


def test_food_log_without_header(tmp_path):
    row = "2020-02-22,10:30:00,2020-02-22 10:30:00,Chicken Nuggets,8.0,piece,Chicken Nuggets,393.0,19.0,0.1,20.0\n"
    write(tmp_path, "003", "Food_Log", row)
    food = load_food("003", tmp_path)
    assert food.loc[0, "time"] == pd.Timestamp("2020-02-22 10:30")
    assert food.loc[0, "calories"] == 393.0
    assert food.loc[0, "carbs"] == 19.0
