"""Per-question skill of a submission on a dataset, next to the best possible (if recorded).

  .venv/bin/python experiments/eval/by_item.py <submission_dir> <dataset_dir> [--phase N]
Skill per question = 1 + mean log score / that question's own marginal surprisal.
"""
import argparse, fcntl, importlib.util, json, os, sys
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "starter-kit"))
import score as S
from make_sandbox import load_config
ap = argparse.ArgumentParser(); ap.add_argument("submission"); ap.add_argument("dataset"); ap.add_argument("--phase", type=int, default=1)
a = ap.parse_args()
config = load_config(os.path.join(ROOT, "starter-kit", "config.yml")); floor = config["scoring"]["floor"]
schema = json.load(open(os.path.join(a.dataset, "schema.json"))); schema.setdefault("gated_value", config["gated_value"])
frame, cells, truth = S.sample_rows(schema, S.load_frames(a.dataset, schema), a.phase)
spec = importlib.util.spec_from_file_location("sub", os.path.join(a.submission, "main.py"))
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
with open(os.path.join(ROOT, "experiments", "eval", ".lock"), "w") as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    vec = S.floored(mod.predict(frame.copy(), schema), schema, cells, floor)
items = [c[2] for c in cells]
opts = {t: S.options_for(schema, t) for t in set(items)}
lp = np.array([np.log(v[opts[t].index(y)]) for v, y, t in zip(vec, truth, items)])
vis = frame[~frame[list(opts)].isna().any(axis=1)]
ref = {}
for t in opts:
    cnt = vis[t].value_counts(); w = np.array([cnt.get(o, 0) + 0.5 for o in opts[t]]); p = floor + (1 - len(w) * floor) * w / w.sum()
    ref[t] = dict(zip(opts[t], np.log(p)))
r = np.array([ref[t][y] for y, t in zip(truth, items)])
d = pd.DataFrame({"item": items, "lp": lp, "ref": r}).groupby("item").agg(lp=("lp", "mean"), ref=("ref", "mean"))
d["share_of_R"] = d["ref"] / d["ref"].sum()
d["skill"] = 1 - d["lp"] / d["ref"]
d["K"] = [len(opts[t]) for t in d.index]
d["gate_parent"] = [(schema["items"][t].get("gate") or {}).get("parent", "") for t in d.index]
cpath = os.path.join(a.dataset, "ceiling.json")
if os.path.exists(cpath):
    c = json.load(open(cpath))["phases"].get(str(a.phase), {}).get("by_item_skill_share")
    if c: d["ceiling_share"] = pd.Series(c)
print("overall skill %.4f" % (1 - lp.mean() / r.mean()))
out = os.path.join(ROOT, "experiments", "eval", "by_item_%s_%s_p%d.csv" % (os.path.basename(a.submission.rstrip("/")), os.path.basename(a.dataset.rstrip("/")), a.phase))
d.to_csv(out); print("saved", out)
