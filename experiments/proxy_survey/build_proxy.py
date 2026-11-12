"""Turn a real public survey into a dataset in the competition's format.

Source: OpenML `kdd_internet_usage` (the 1997 GVU internet-user survey; 10,108
people, all-categorical). Demographics become GIVEN, every other question
becomes PREDICT. No gates: this proxy tests the conditional model only.
"""
import json, os
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
raw = pd.read_parquet(os.path.join(HERE, "data", "kdd_internet_usage_raw.parquet"))
raw = raw.replace({"nan": "Missing", "None": "Missing"}).fillna("Missing")

def top(series, k):
    keep = series.value_counts().index[:k]
    return series.where(series.isin(keep), "Other")

age = pd.to_numeric(raw["Age"], errors="coerce")
raw["Age"] = pd.cut(age, [-1, 20, 25, 30, 40, 50, 200],
                    labels=["<=20", "21-25", "26-30", "31-40", "41-50", "51+"]).astype(str)
raw["Country"] = top(raw["Country"], 45)            # 46 levels, like the governorate
raw["Primary_Language"] = top(raw["Primary_Language"], 10)
raw["Actual_Time"] = top(raw["Actual_Time"], 20)

GIVEN = ["Age", "Gender", "Country", "Major_Geographical_Location",
         "Education_Attainment", "Household_Income", "Major_Occupation",
         "Marital_Status", "Race", "Primary_Language"]
PREDICT = [c for c in raw.columns if c not in GIVEN]

rng = np.random.default_rng(20261110)
order = rng.permutation(len(raw))
n_train, n_dev = 7500, 2000
role = np.empty(len(raw), dtype=object)
role[order[:n_train]] = "TRAIN"
role[order[n_train:n_train + n_dev]] = "DEV"
role[order[n_train + n_dev:]] = "TEST"

frame = raw[GIVEN + PREDICT].astype(object).fillna("Missing").astype(str).astype(object)
frame.insert(0, "respondent_id", ["P%05d" % i for i in range(len(raw))])
frame["role"] = role

items = {}
for name in GIVEN + PREDICT:
    items[name] = {"question": name.replace("_", " "),
                   "class": "GIVEN" if name in GIVEN else "PREDICT",
                   "values": sorted(frame[name].unique()), "gate": None}
schema = {"dataset": {"n_rows": len(frame), "version": "proxy",
                      "description": "GVU 1997 internet-user survey (OpenML kdd_internet_usage)"},
          "items": items,
          "split": {"n_train": n_train, "n_dev": n_dev,
                    "n_test": len(raw) - n_train - n_dev},
          "gated_value": "NA_GATED"}

out = os.path.join(HERE, "proxy")
os.makedirs(out, exist_ok=True)
frame.to_parquet(os.path.join(out, "respondents.parquet"))
json.dump(schema, open(os.path.join(out, "schema.json"), "w"), indent=1)
ks = [len(items[p]["values"]) for p in PREDICT]
print("rows", len(frame), "GIVEN", len(GIVEN), "PREDICT", len(PREDICT),
      "binary", sum(k == 2 for k in ks), "multi", sum(k > 2 for k in ks), "max K", max(ks))
