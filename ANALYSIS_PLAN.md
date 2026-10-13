# Analysis plan

I wrote these rules before running the comparisons they govern. They first lived in CLAUDE.md, and these commits show when each one went in:

- [7dd1bbe](https://github.com/Kawsarwilna/placebo-meals/commit/7dd1bbe): main rules, before any heart rate result.
- [6c878eb](https://github.com/Kawsarwilna/placebo-meals/commit/6c878eb): movement check, before running it.
- [a6bd0e2](https://github.com/Kawsarwilna/placebo-meals/commit/a6bd0e2): still-threshold outcome, before any heart rate result from the movement check.

I later moved the rules into this file and edited the wording. The rules match those commits.

## Data and clocks

- **Heart rate:** per-minute means from the wristband.
- **Clocks:** the wristband, the Dexcom and the food log all use local time. Every included participant's heart rate bottoms out between 3 and 7 am.

## Meals and placebo moments

- **Meals:** food items logged within 30 minutes of each other form one meal.
- **Clean window:** the person ate nothing from 2 hours before to 3 hours after the moment. Meals and placebo moments follow the same rule.
- **Placebo moments:**
  - 5 per clean meal, drawn with a fixed seed from a 5-minute grid of food-free times.
  - Each one is on a different date from its meal, within 60 minutes of the meal's clock time.

## Scores

- **Peak:** the highest value from 0 to 180 minutes after the moment, minus the mean of the 30 minutes before.
- **Average** ("sustained" in the code): the mean from 30 to 120 minutes after, minus the same baseline.
- **Coverage:** each window needs 2/3 of its expected samples. Heart rate comes every minute and glucose every 5 minutes.
- **Positive control:** the same scores on glucose. If meal times and sensor clocks line up, glucose rises after real meals and stays flat after placebo moments.

## Inclusion

A participant needs at least 3 clean meals with valid heart rate and glucose windows. This rule drops 015, whose food log and glucose recording don't overlap.

## Summary

- **Per participant:** mean real-meal response minus mean placebo response. Also the chance that a real meal outscores a placebo moment (AUC).
- **Across participants:** the median, the count of positive differences and a Wilcoxon signed-rank test.
- **Sensitivity check:** repeat the summary without participants whose glucose check fails, meaning their real-meal glucose rise minus placebo rise is at or below 0. With the first placebo draw, those were 012 and 016. After the correction below, 012 is the one left. I set this rule after the glucose check and before looking at heart rate.

## Movement check

- **Movement per minute:** the standard deviation of wrist acceleration magnitude (g) within the minute, from the 32 Hz accelerometer.
  - A minute needs 2/3 of its samples to count.
  - `src/motion.py` streams the raw files, keeps this summary and discards the raw data.
- **Movement-removed heart rate:**
  - One linear model per person predicts per-minute heart rate from three inputs: movement now, mean movement over the previous 5 minutes and mean movement over the 10 minutes before that.
  - The model uses minutes at least 3 hours after any logged food, so a meal effect can't leak into it.
  - The adjusted heart rate is what the model leaves over. It gets the same scores and the same placebo comparison.
- **Still periods:**
  - A minute is still when movement stays below `STILL_THRESHOLD` in `src/movement.py`.
  - A window is still when at least 80% of its minutes are still, both in the 30 minutes before and from 30 to 120 minutes after.
  - The eating period (0 to 30 minutes) may include movement, since eating moves the wrist.
  - The outcome is the heart rate average, with the glucose peak in the same windows as a check.
- **Inclusion:** at least 2 meals and 2 placebo moments per person in each comparison.
- **Threshold choice:**
  - Candidates: 0.01, 0.02, 0.03, 0.05, 0.075 and 0.1 g.
  - Pick the lowest that leaves at least 8 participants with 2 or more still meals and 2 or more still placebo moments.
  - The choice looks at window counts and ignores heart rate and glucose values.
- **Threshold outcome:**
  - No candidate met the minimum. At 0.1 g, 7 participants qualified and 27 of 167 meals passed.
  - I report the still-period comparison at 0.1 g, labeled exploratory.
  - The movement-removed comparison uses every window and is the main movement result.

## Correction

- **Repeated placebo moments.**
  - The first version drew placebo moments for each meal independently, so 30% of placebo windows reused a moment already drawn for another meal.
  - The sampler now uses each moment once, which gives 504 distinct placebo moments instead of 644 windows.
  - The conclusions held. A real meal outscored a placebo moment 85% of the time for glucose (84% before), 49% for heart rate peak (45%) and 49% for heart rate average (49%).
  - The movement-removed average weakened from p = 0.07 to p = 0.28.

## Decisions made after seeing results

- **AUC across people:** I report the median to match the other medians. The mean leads to the same conclusions, and `results/metrics.json` has both.
- **Exploratory checks:** these came after the main results, and the README labels them exploratory:
  - the 5-minute smoothed peak
  - the large-meal check
  - 10 random draws of placebo moments
  - lunch and dinner (11:00 to 21:00)
  - leaving out moments that started while the person lay still (movement below 0.01 g for 80% of the baseline)
- **Dropped question:** I had planned to ask how many repeats of the same meal a stable personal response needs. I dropped it because 3 standard breakfasts passed the clean-window rule, too few to work with.
