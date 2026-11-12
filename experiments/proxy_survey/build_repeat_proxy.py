"""A second stand-in: the same real survey, plus simulated repeat interviews.

3,000 people get a second row: same household-style facts and mostly the same
answers (12% of answers redrawn at random), but three respondent-level GIVEN
columns (Age, Gender, Marital_Status) redrawn, as if another household member
answered. Purpose: check that a general similarity model benefits when a
dataset contains repeat respondents, without being told which rows they are.
"""
import json, os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
schema = json.load(open(os.path.join(HERE, "proxy", "schema.json")))
df = pd.read_parquet(os.path.join(HERE, "proxy", "respondents.parquet")).astype(object)
items = schema["items"]
given = [n for n in items if items[n]["class"] == "GIVEN"]
targets = [n for n in items if items[n]["class"] == "PREDICT"]
rng = np.random.default_rng(11)
base = df.iloc[rng.choice(len(df), 3000, replace=False)].copy()
for c in ["Age", "Gender", "Marital_Status"]:
    base[c] = rng.permutation(df[c].to_numpy())[:len(base)]
for t in targets:
    redraw = rng.random(len(base)) < 0.12
    base.loc[redraw, t] = rng.choice(df[t].to_numpy(), int(redraw.sum()))
out = pd.concat([df, base], ignore_index=True).sample(frac=1.0, random_state=5).reset_index(drop=True)
out["respondent_id"] = ["Q%05d" % i for i in range(len(out))]
n = len(out); n_train, n_dev = int(0.74 * n), int(0.19 * n)
out["role"] = ["TRAIN"] * n_train + ["DEV"] * n_dev + ["TEST"] * (n - n_train - n_dev)
schema["split"] = {"n_train": n_train, "n_dev": n_dev, "n_test": n - n_train - n_dev}
schema["dataset"]["n_rows"] = n
dst = os.path.join(HERE, "proxy_repeat"); os.makedirs(dst, exist_ok=True)
out.to_parquet(os.path.join(dst, "respondents.parquet"))
json.dump(schema, open(os.path.join(dst, "schema.json"), "w"), indent=1)
print("rows", n, "train", n_train, "dev", n_dev)
