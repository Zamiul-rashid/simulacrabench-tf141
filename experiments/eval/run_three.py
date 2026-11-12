"""Rehearse the hosted run: import a submission ONCE, then call predict() for several
datasets in turn inside the same process, as the organisers' orchestrator does, and
score each with their functions. Shows the total wall-clock from import to the last
return, which is what the 900 s / 3600 s limit applies to.

  .venv/bin/python experiments/eval/run_three.py <submission_dir> <phase> <tag> <dataset> <dataset> ...

Appends one row per dataset to experiments/eval/results.csv (tag gets the call order).
"""
import csv, importlib.util, json, os, sys, time, traceback
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "starter-kit"))
import score as S
from make_sandbox import load_config

sub, phase, tag, names = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4:]
config = load_config(os.path.join(ROOT, "starter-kit", "config.yml"))
floor = config["scoring"]["floor"]
jobs = []
for name in names:
    d = os.path.join(ROOT, "experiments", "datasets", name)
    schema = json.load(open(os.path.join(d, "schema.json")))
    schema.setdefault("gated_value", config["gated_value"])
    frame, cells, truth = S.sample_rows(schema, S.load_frames(d, schema), phase)
    jobs.append((name, schema, frame, cells, truth, S.marginal_reference(schema, frame, cells, truth, floor)))

t_import = time.time()
spec = importlib.util.spec_from_file_location("sub", os.path.join(sub, "main.py"))
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
rows, skills = [], []
for k, (name, schema, frame, cells, truth, ref) in enumerate(jobs):
    row = {"when": time.strftime("%Y-%m-%d %H:%M:%S"), "submission": os.path.basename(sub.rstrip("/")),
           "dataset": name, "phase": phase, "tag": "%s call%d_of_%d" % (tag, k + 1, len(jobs)),
           "n_visible": len(frame) - len({c[1] for c in cells}), "n_hidden": len({c[1] for c in cells}),
           "n_cells": len(cells)}
    t0 = time.time()
    try:
        vec = mod.predict(frame.copy(), schema)
        row["seconds"] = round(time.time() - t0, 1)
        S.check(schema, vec, cells)
        res = S.score(schema, config, S.floored(vec, schema, cells, floor), truth, cells, ref)
        row.update(status="PASS", skill=round(res["skill"], 4), std_error=round(res["std_error"] / ref, 4))
        skills.append(res["skill"])
        print("SKILL %.4f (+/- %.4f) %.0fs  %s on %s (call %d, %.0fs since import)" % (
            res["skill"], res["std_error"] / ref, row["seconds"], row["submission"], name, k + 1,
            time.time() - t_import), flush=True)
    except Exception as exc:
        row.update(status="FAIL", seconds=round(time.time() - t0, 1), skill="", std_error="",
                   tag=(row["tag"] + " " + repr(exc))[:300])
        traceback.print_exc(); print("FAIL %s on %s: %r" % (row["submission"], name, exc), flush=True)
    rows.append(row)
print("TOTAL %.0fs from import to last return; mean skill %s" % (
    time.time() - t_import, "%.4f" % (sum(skills) / len(skills)) if len(skills) == len(jobs) else "n/a"), flush=True)
path = os.path.join(ROOT, "experiments", "eval", "results.csv")
fields = ["when", "submission", "dataset", "phase", "status", "skill", "std_error", "seconds",
          "n_visible", "n_hidden", "n_cells", "tag"]
with open(path, "a", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=fields)
    for row in rows:
        w.writerow(row)
