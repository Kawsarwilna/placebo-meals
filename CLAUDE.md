# placebo-meals

A placebo test for wearable meal responses, run on public data.

**Main question:** does heart rate after a real meal differ from heart rate after a random "placebo" moment in the same person's day?

**Second question:** how many repeats of the same meal does it take before one person's meal response is stable?

## Data

- **Source:** BIG IDEAs Lab Glycemic Variability and Wearable Device Data, PhysioNet v1.1.3. License: Open Data Commons Attribution 1.0.
- **Citations:** Cho et al. 2026 (doi:10.13026/aw6y-fc44) and Bent et al. 2021, npj Digital Medicine 4:89.
- **Contents:** 16 adults aged 35 to 65, each recorded for 8 to 10 days with an Empatica E4 wristband, a Dexcom G6 glucose monitor and a food log. A standardized breakfast was eaten every other day.
- **Storage:** raw files go in `data/`, which is gitignored. Never commit raw data.
- **Files to use:**
  - Core: `HR_xxx.csv`, `Dexcom_xxx.csv`, `Food_Log_xxx.csv` (about 250 MB in total).
  - Stretch only: `TEMP_xxx.csv`, `EDA_xxx.csv` (about 2.5 GB).
  - Never download `ACC`, `BVP` or `IBI`.
- **Known quirks:**
  - HR timestamps have minute resolution, with about 60 rows per minute.
  - Dexcom files start with metadata rows.
  - The food log has one row per food item, not one row per meal.

## Rules

- Every number in `README.md` comes from a script. `src/report.py` renders `README.md` from `README.template.md` using `results/metrics.json`. Never type numbers by hand.
- Wellness framing only:
  - No diagnostic language.
  - No medical or dosing advice.
  - No claims about any specific device.
- Don't name or evaluate any company's product or code.
- Label anything simulated as simulated.
- Unit of analysis is the participant. Summarize within each person first, then across people.
- If a model is ever trained:
  - Use a classical baseline first.
  - Split by participant (leave-one-participant-out), never by meal or time window.
- Writing style:
  - US English, no em dashes.
  - Avoid "excited to," "passionate about," "leverage" and "dive into."
- Code style:
  - Simple, readable Python using pandas, numpy, scipy and matplotlib.
  - Comments only where something needs explaining.
- Get a rough end-to-end version working first, then improve it.

## Commands

- Setup: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
- Download: `.venv/bin/python src/download.py`
- Tests: `.venv/bin/python -m pytest -q`
- Full run: `.venv/bin/python run_all.py`

## Git

- Use `/usr/bin/git`. The git binary in `/usr/local/bin` is broken on this machine.
- Make a small commit after each working step and push often. The repo is public.

## Analysis decisions

Update this list as decisions are made:

- **HR resolution:** per-minute means.
- **Meal response (peak):** max HR from 0 to 180 min after the meal, minus mean HR in the 30 min before.
- **Meal response (sustained):** mean HR from 30 to 120 min after the meal, minus mean HR in the 30 min before.
- **Positive control:** the glucose rise after real meals vs placebo moments. It confirms that meal times and sensor clocks line up.
- **Clocks:** wristband, Dexcom and food log are all local time. Every participant's heart rate is lowest between 3 and 7 am.
- **Meals:** food items logged within 30 min of each other form one meal.
- **Clean window:** nothing else eaten from 2 h before to 3 h after the moment. Same rule for meals and placebos.
- **Placebos:** 5 per clean meal, from a 5-min grid of food-free times, on a different date, within 60 min of the meal's clock time. Fixed seed.
- **Coverage:** each window needs at least 2/3 of its expected samples (heart rate is per minute, glucose every 5 min).
- **Inclusion:** a participant needs at least 3 clean meals with valid heart rate and glucose windows. This drops 015, whose food log and glucose don't overlap.
- **Main summary:** per participant, mean real-meal response minus mean placebo response. Across participants: median, how many are positive, and a Wilcoxon signed-rank test. Also the per-participant chance that a real meal outscores a placebo (AUC).
- **Sensitivity check:** repeat the main summary without participants whose glucose check fails, meaning real-meal glucose rise minus placebo rise is at or below 0. That is 012 and 016. This was decided after the glucose check and before looking at heart rate.
- These rules were fixed before looking at any heart rate results.

### Movement check (added later, written before running it)

- **Movement per minute:** the standard deviation of wrist acceleration magnitude (g) within the minute, from the 32 Hz accelerometer. Only minutes with at least 2/3 of their samples count. Raw ACC files are streamed and summarized, never stored (`src/motion.py`).
- **Movement-removed heart rate:**
  - Fit a linear model per person: per-minute heart rate on three inputs, which are movement now, mean movement over the previous 5 minutes and mean movement over the 10 minutes before that.
  - Fit it only on minutes at least 3 h after any logged food, so a meal effect can't leak into it.
  - The adjusted heart rate is the residual. Run the same peak and average scores and the same placebo comparison on it.
- **Still periods:**
  - A minute is still when movement is below the threshold `STILL_THRESHOLD` in `src/movement.py`.
  - A window counts as still when at least 80% of its minutes are still, both in the 30 min before and from 30 to 120 min after. The eating period itself (0 to 30 min) isn't required to be still, because eating moves the wrist.
  - Scores: the raw heart rate average (30 to 120 min) as the outcome, with the glucose peak in the same windows as a check.
- **Inclusion:** the usual rule, at least 2 meals and 2 placebos per person for each comparison.
- **Threshold choice:** the threshold is picked from the movement data alone, before any heart rate comparison is run. Candidates are 0.01, 0.02, 0.03, 0.05, 0.075 and 0.1 g. Pick the lowest one that leaves at least 8 participants with at least 2 still meals and 2 still placebo moments. Only window counts are looked at to make this choice, never heart rate or glucose values.
