"""Per-cell breakdown of a submission's vectors on a fabricated unhcr_* dataset.

  .venv/bin/python experiments/datasets/builders/unhcr_analyze.py <dataset> <phase> <vectors.json> [...]

The vectors are what predict() returned (JSON list of lists, canonical cell order),
e.g. dumped by a thin wrapper around the submission. The dataset's generator state is
rebuilt deterministically from its builder (same seed), so each cell can be tagged with
what was planted: gated / ungated item, truth NA_GATED or not, hidden row with a visible
interview of the same household, item group, size of the visible branch. Also prints the
Monte Carlo ceiling (true P(y | GIVEN)) on the same groups.
"""
import importlib
import os
import json
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import unhcr_gen as U  # noqa: E402

SEEDS = {"unhcr_noisygates": 101, "unhcr_repeats": 102, "unhcr_full": 103,
         "unhcr_small_branches": 104, "unhcr_edge": 105, "unhcr_panel": 106,
         "unhcr_additive": 101}


def rebuild(name):
    mod = importlib.import_module(name)
    cfg = getattr(mod, "CFG", None)
    if cfg is None:
        cfg = dict(noisy_gates=True)
    frame, meta = U.build(name, dict(U.WORLD, **cfg), SEEDS[name])
    disk = pd.read_parquet(os.path.join(U.OUT_ROOT, name, "respondents.parquet"))
    assert disk.equals(frame.astype(disk.dtypes.to_dict())), "rebuild differs from disk"
    return meta


def cell_logp(meta, vectors, phase):
    W, Y, roles = meta["W"], meta["Y"], meta["roles"]
    hid = np.flatnonzero(roles == (1 if phase == 1 else 2))
    P = len(W.targets)
    K = np.array([len(W.vals[t]) + (1 if W.items[t].get("gate") else 0) for t in W.targets])
    Yc = np.where(Y < 0, K[None, :] - 1, Y)
    # canonical order: rows in file order (hidden role), items in schema order
    order = [n for n, r in meta["schema"]["items"].items() if r["class"] in ("GIVEN", "PREDICT")]
    pidx = [W.tix[n] for n in order if n in W.tix]
    assert len(vectors) == len(hid) * P
    lp = np.zeros((len(hid), P))
    c = 0
    for a in range(len(hid)):
        for j in pidx:
            v = np.asarray(vectors[c], float)
            v = v / v.sum()
            v = U.FLOOR + (1 - K[j] * U.FLOOR) * v
            lp[a, j] = np.log(v[Yc[hid[a], j]])
            c += 1
    return hid, lp


def ref_logp(meta, phase):
    W, Y, roles = meta["W"], meta["Y"], meta["roles"]
    vis = roles == 0 if phase == 1 else roles <= 1
    hid = np.flatnonzero(roles == (1 if phase == 1 else 2))
    K = np.array([len(W.vals[t]) + (1 if W.items[t].get("gate") else 0) for t in W.targets])
    Yc = np.where(Y < 0, K[None, :] - 1, Y)
    out = np.zeros((len(hid), len(W.targets)))
    for j in range(len(W.targets)):
        cnt = np.bincount(Yc[vis, j], minlength=K[j]) + 0.5
        p = U.FLOOR + (1 - K[j] * U.FLOOR) * cnt / cnt.sum()
        out[:, j] = np.log(p[Yc[hid, j]])
    return out


def groups(meta, phase):
    W, Y, roles, hh = meta["W"], meta["Y"], meta["roles"], meta["hh"]
    vis = roles == 0 if phase == 1 else roles <= 1
    hid = np.flatnonzero(roles == (1 if phase == 1 else 2))
    vis_hh = set(hh[vis])
    linked = np.array([hh[i] in vis_hh for i in hid])
    gated = np.array([bool(W.items[t].get("gate")) for t in W.targets])
    asked_vis = np.array([(Y[vis, j] >= 0).sum() for j in range(len(W.targets))])
    sec = np.array([t.split("_")[0] for t in W.targets])
    return dict(linked=linked, gated=gated, asked_vis=asked_vis, sec=sec,
                truth_na=Y[hid] < 0)


def report(name, phase, dumps, M=500):
    meta = rebuild(name)
    ref = ref_logp(meta, phase)
    R = -ref.mean()
    g = groups(meta, phase)
    cg = U.ceiling(meta, phase=phase, M=M) if M else None
    rows = []
    lps = {}
    for path in dumps:
        with open(path) as fh:
            vec = json.load(fh)
        _, lp = cell_logp(meta, vec, phase)
        lps[os.path.basename(path)] = lp
    def sk(lp, mask):
        return 1 + lp[mask].mean() / -ref[mask].mean() if mask.any() else np.nan
    n, P = ref.shape
    full = np.ones((n, P), bool)
    masks = {"all": full,
             "gated items": np.tile(g["gated"], (n, 1)),
             "ungated items": np.tile(~g["gated"], (n, 1)),
             "truth NA_GATED": g["truth_na"],
             "truth answered (gated items)": ~g["truth_na"] & np.tile(g["gated"], (n, 1)),
             "rows with visible same-household row": np.tile(g["linked"][:, None], (1, P)),
             "rows without": np.tile(~g["linked"][:, None], (1, P)),
             "items with <60 visible asked rows": np.tile((g["asked_vis"] < 60)
                                                          & g["gated"], (n, 1))}
    for s in sorted(set(g["sec"])):
        masks["section " + s] = np.tile(g["sec"] == s, (n, 1))
    for k, m in masks.items():
        row = {"group": k, "share_of_R": -ref[m].sum() / -ref.sum(), "cells": int(m.sum())}
        for nm, lp in lps.items():
            row[nm] = sk(lp, m)
        rows.append(row)
    df = pd.DataFrame(rows)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 20)
    print("%s phase %d: R=%.4f; overall skills %s" % (name, phase, R, {
        k: round(1 + v.mean() / R, 4) for k, v in lps.items()}))
    if cg:
        print("ceiling:", {k: round(float(v), 3) for k, v in cg.items()})
    print(df.round(3).to_string(index=False))
    # worst items for the last submission
    if lps:
        nm, lp = list(lps.items())[-1]
        loss = (lp - ref).sum(0) / -ref.sum()   # contribution to skill (negative = loss)
        W = meta["W"]
        idx = np.argsort(loss)[:10]
        print("items where %s loses most skill vs the marginal:" % nm)
        for j in idx:
            print("  %-40s %+.4f  (visible asked %d)" % (W.targets[j], loss[j], g["asked_vis"][j]))
    return df


if __name__ == "__main__":
    report(sys.argv[1], int(sys.argv[2]), sys.argv[3:], M=int(os.environ.get("CEIL_M", "500")))
