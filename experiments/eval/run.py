"""Score one submission on one dataset in the kit's format, in-process, with the
organisers' own scoring functions. One run at a time (file lock) because the
models share a small GPU; concurrent runs would silently lose members.

  .venv/bin/python experiments/eval/run.py <submission_dir> <dataset_dir> [--phase 1|2] [--tag note]

<dataset_dir> holds respondents.parquet and schema.json. Prints the submission's
own log lines, then one line:  SKILL <exact skill> (+/- se) <seconds>s ...
and appends a row to experiments/eval/results.csv.
"""
import argparse, csv, fcntl, importlib.util, json, os, sys, time, traceback
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "starter-kit"))
import score as S
from make_sandbox import load_config

ap = argparse.ArgumentParser()
ap.add_argument("submission"); ap.add_argument("dataset")
ap.add_argument("--schema"); ap.add_argument("--phase", type=int, default=1); ap.add_argument("--tag", default="")
a = ap.parse_args()
config = load_config(os.path.join(ROOT, "starter-kit", "config.yml"))
floor = config["scoring"]["floor"]
schema = json.load(open(a.schema or os.path.join(a.dataset, "schema.json")))
schema.setdefault("gated_value", config["gated_value"])
frame, cells, truth = S.sample_rows(schema, S.load_frames(a.dataset, schema), a.phase)
ref = S.marginal_reference(schema, frame, cells, truth, floor)
spec = importlib.util.spec_from_file_location("sub", os.path.join(a.submission, "main.py"))
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
row = {"when": time.strftime("%Y-%m-%d %H:%M:%S"), "submission": os.path.basename(a.submission.rstrip("/")),
       "dataset": os.path.basename(a.dataset.rstrip("/")), "phase": a.phase, "tag": a.tag,
       "n_visible": len(frame) - len({c[1] for c in cells}), "n_hidden": len({c[1] for c in cells}),
       "n_cells": len(cells)}
with open(os.path.join(ROOT, "experiments", "eval", ".lock"), "w") as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    t0 = time.time()
    try:
        vec = mod.predict(frame.copy(), schema)
        row["seconds"] = round(time.time() - t0, 1)
        S.check(schema, vec, cells)
        res = S.score(schema, config, S.floored(vec, schema, cells, floor), truth, cells, ref)
        row.update(status="PASS", skill=round(res["skill"], 4), std_error=round(res["std_error"] / ref, 4))
        print("SKILL %.4f (+/- %.4f) %.0fs  %s on %s" % (res["skill"], res["std_error"] / ref,
                                                        row["seconds"], row["submission"], row["dataset"]))
    except Exception as exc:
        row.update(status="FAIL", seconds=round(time.time() - t0, 1), skill="", std_error="",
                   tag=(a.tag + " " + repr(exc))[:300])
        traceback.print_exc(); print("FAIL %s on %s: %r" % (row["submission"], row["dataset"], exc))
path = os.path.join(ROOT, "experiments", "eval", "results.csv")
fields = ["when", "submission", "dataset", "phase", "status", "skill", "std_error", "seconds",
          "n_visible", "n_hidden", "n_cells", "tag"]
new = not os.path.exists(path)
with open(path, "a", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=fields)
    if new: w.writeheader()
    w.writerow(row)
