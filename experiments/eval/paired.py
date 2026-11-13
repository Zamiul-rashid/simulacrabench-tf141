"""Paired comparison of two runs on the same dataset and phase, cell by cell.

  python experiments/eval/paired.py A.npz B.npz [--by-column COLUMN --dataset DIR --phase N]

A.npz / B.npz come from run.py --dump. Prints skill(A) - skill(B) with a standard error that
resamples whole respondents (the organisers' cluster_std_error), so it accounts for the
many cells one respondent contributes. With --by-column, also prints A's skill per level of
a GIVEN column of the hidden respondents (for example a country).
"""
import argparse, json, os, sys
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "starter-kit"))
import score as S

ap = argparse.ArgumentParser()
ap.add_argument("a"); ap.add_argument("b", nargs="?")
ap.add_argument("--by-column"); ap.add_argument("--dataset"); ap.add_argument("--phase", type=int, default=1)
args = ap.parse_args()
A = np.load(args.a)
R = float(A["reference"])
print("A: %s  skill %.4f  (%d cells)" % (os.path.basename(args.a), 1 + A["logp"].mean() / R, A["logp"].size))
if args.b:
    B = np.load(args.b)
    assert (A["respondent"] == B["respondent"]).all() and (A["item"] == B["item"]).all(), "different cells"
    d = (A["logp"] - B["logp"]) / R
    se = S.cluster_std_error(d, A["respondent"], draws=2000, seed=0)
    print("B: %s  skill %.4f" % (os.path.basename(args.b), 1 + B["logp"].mean() / R))
    print("A - B: %+.4f  (respondent-clustered se %.4f, z %.1f)" % (d.mean(), se, d.mean() / se if se else float("nan")))
if args.by_column:
    schema = json.load(open(os.path.join(args.dataset, "schema.json")))
    from make_sandbox import load_config
    schema.setdefault("gated_value", load_config(os.path.join(ROOT, "starter-kit", "config.yml"))["gated_value"])
    frame, cells, truth = S.sample_rows(schema, S.load_frames(args.dataset, schema), args.phase)
    level = dict(zip(frame["respondent_id"].astype(str), frame[args.by_column].astype(str)))
    lv = np.array([level[r] for r in A["respondent"]])
    print("skill of A by %s (hidden respondents):" % args.by_column)
    for v in sorted(set(lv)):
        m = lv == v
        print("  %-28s %6d respondents  skill %.4f" % (v[:28], len(set(A["respondent"][m])), 1 + A["logp"][m].mean() / R))
