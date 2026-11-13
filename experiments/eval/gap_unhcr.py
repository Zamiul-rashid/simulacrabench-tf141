"""Where does a submission lose against the best possible answer on a fabricated
UNHCR-like dataset?  The dataset is regenerated from its builder (same seed), so the
true generating probabilities are known for every hidden cell:

  oracle_given : P(answer | GIVEN columns)                         -- no household link
  oracle_link  : P(answer | GIVEN, the visible interview of the same household)

The gap between the submission and each oracle is split by household type (hidden row
has / has no visible interview of the same household) and by question type.  Every
number is in skill points, and the parts add up to the total gap.

  .venv/bin/python experiments/eval/gap_unhcr.py <submission_dir> [--phase 1] [--dataset unhcr_full]
"""
import argparse, importlib, importlib.util, json, os, sys, time
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "starter-kit"))
sys.path.insert(0, os.path.join(ROOT, "experiments", "datasets", "builders"))
import score as S
from make_sandbox import load_config
import unhcr_gen as U

ap = argparse.ArgumentParser()
ap.add_argument("submission"); ap.add_argument("--phase", type=int, default=1)
ap.add_argument("--dataset", default="unhcr_full"); ap.add_argument("--seed", type=int, default=103)
ap.add_argument("--draws", type=int, default=1000)
a = ap.parse_args()
ddir = os.path.join(ROOT, "experiments", "datasets", a.dataset)
cache = os.path.join(ROOT, "experiments", "eval", "gap_cache")
os.makedirs(cache, exist_ok=True)
FLOOR = U.FLOOR


def oracle(meta, phase, M, chunk=60, seed=123):
    """Same computation as unhcr_gen.ceiling, but returns the per-cell arrays."""
    W, G, A, Y, roles, src, hh = (meta[k] for k in ("W", "G", "A", "Y", "roles", "src_row", "hh"))
    vis = roles == 0 if phase == 1 else roles <= 1
    hid = np.flatnonzero(roles == (1 if phase == 1 else 2))
    P = len(W.targets)
    K = np.array([len(W.vals[t]) + (1 if W.items[t].get("gate") else 0) for t in W.targets])
    Ycode = np.where(Y < 0, K[None, :] - 1, Y)
    ref_lp = np.zeros((len(hid), P))
    for j in range(P):
        cnt = np.bincount(Ycode[vis, j], minlength=K[j]) + 0.5
        p = FLOOR + (1 - K[j] * FLOOR) * cnt / cnt.sum()
        ref_lp[:, j] = np.log(p[Ycode[hid, j]])
    link = np.full(len(hid), -1)
    by_hh = {}
    for i in np.flatnonzero(vis):
        by_hh.setdefault(hh[i], []).append(i)
    for k, i in enumerate(hid):
        cand = by_hh.get(hh[i], [])
        if cand:
            orig = [c for c in cand if src[c] < 0]
            link[k] = (orig or cand)[0]
    rng = np.random.default_rng(seed)
    lp_g, lp_t = np.zeros((len(hid), P)), np.zeros((len(hid), P))
    for lo in range(0, len(hid), chunk):
        rows = hid[lo:lo + chunk]
        Gr = np.repeat(G[rows], M, axis=0)
        truth = np.repeat(Ycode[rows], M, axis=0)
        for mode in ("g", "t"):
            sel = link[lo:lo + chunk] >= 0
            if mode == "t":
                if not sel.any():
                    lp_t[lo:lo + chunk] = lp_g[lo:lo + chunk]; continue
                lk = np.maximum(link[lo:lo + chunk], 0)
                sr = meta["same_resp"]
                same = np.repeat(np.where(src[rows] >= 0, sr[rows], True) & sr[lk], M)
                _, Ys = W.simulate(Gr, rng, src=np.repeat(A[lk], M, axis=0), stab=W.stability(same, meta["cfg"]))
            else:
                _, Ys = W.simulate(Gr, rng)
            Yc = np.where(Ys < 0, K[None, :] - 1, Ys)
            hit = (Yc == truth).reshape(len(rows), M, P).sum(1)
            p = FLOOR + (1 - K[None, :] * FLOOR) * (hit + 0.1) / (M + 0.1 * K[None, :])
            if mode == "g":
                lp_g[lo:lo + chunk] = np.log(p)
            else:
                lp_t[lo:lo + chunk] = np.where(sel[:, None], np.log(p), lp_g[lo:lo + chunk])
    gated = np.array([bool(W.items[t].get("gate")) for t in W.targets])
    not_asked = Y[hid] < 0
    return dict(lp_g=lp_g, lp_t=lp_t, ref=ref_lp, link=link, K=K, gated=gated, not_asked=not_asked,
                truth=Ycode[hid], targets=np.array(W.targets))


opath = os.path.join(cache, "oracle_%s_p%d.npz" % (a.dataset, a.phase))
if os.path.exists(opath):
    O = dict(np.load(opath, allow_pickle=False))
else:
    cfg_mod = importlib.import_module(a.dataset)
    t0 = time.time()
    frame_b, meta = U.build(a.dataset, dict(U.WORLD, **cfg_mod.CFG), a.seed)
    stored = pd.read_parquet(os.path.join(ddir, "respondents.parquet"))
    assert stored.shape == frame_b.shape and (stored.astype(str).to_numpy() == frame_b.astype(str).to_numpy()).all(), \
        "regenerated data differs from the stored dataset"
    O = oracle(meta, a.phase, a.draws)
    np.savez(opath, **O)
    print("oracle computed in %.0fs" % (time.time() - t0), flush=True)

name = os.path.basename(a.submission.rstrip("/"))
ppath = os.path.join(cache, "ours_%s_%s_p%d.npy" % (name, a.dataset, a.phase))
if os.path.exists(ppath):
    ours = np.load(ppath)
else:
    config = load_config(os.path.join(ROOT, "starter-kit", "config.yml"))
    schema = json.load(open(os.path.join(ddir, "schema.json"))); schema.setdefault("gated_value", config["gated_value"])
    frame, cells, truth = S.sample_rows(schema, S.load_frames(ddir, schema), a.phase)
    spec = importlib.util.spec_from_file_location("sub", os.path.join(a.submission, "main.py"))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    vec = S.floored(mod.predict(frame.copy(), schema), schema, cells, config["scoring"]["floor"])
    n_hid, P = O["lp_g"].shape
    items = [c[2] for c in cells]
    assert len(cells) == n_hid * P and items[:P] == list(O["targets"]), "cell order differs from the builder's"
    opts = {t: S.options_for(schema, t) for t in set(items)}
    ours = np.array([np.log(v[opts[t].index(y)]) for v, y, t in zip(vec, truth, items)]).reshape(n_hid, P)
    idx = np.array([opts[t].index(y) for y, t in zip(truth, items)]).reshape(n_hid, P)
    assert (idx == O["truth"]).all(), "truth differs from the builder's"
    np.save(ppath, ours)

ref, lp_g, lp_t = O["ref"], O["lp_g"], O["lp_t"]
N = ref.size; R = -ref.mean()
linked = (O["link"] >= 0)[:, None] & np.ones_like(ref, bool)
gated = O["gated"][None, :] & np.ones_like(ref, bool)
na = O["not_asked"]
sk = lambda lp: 1 + lp.mean() / R
print("\n%s on %s phase %d: %d hidden rows (%.0f%% with a visible interview of the same household), %d questions"
      % (name, a.dataset, a.phase, ref.shape[0], 100 * (O["link"] >= 0).mean(), ref.shape[1]))
print("skill: ours %.4f | best possible from GIVEN %.4f | best possible with household link %.4f"
      % (sk(ours), sk(lp_g), sk(lp_t)))
pts = lambda x, m: x[m].sum() / (N * R)                    # skill points contributed by cells in mask m
groups = [("linked household, ungated question", linked & ~gated),
          ("linked household, gated, was asked", linked & gated & ~na),
          ("linked household, gated, not asked", linked & gated & na),
          ("no link, ungated question", ~linked & ~gated),
          ("no link, gated, was asked", ~linked & gated & ~na),
          ("no link, gated, not asked", ~linked & gated & na)]
print("\n%-38s %7s %9s %9s %9s %11s %11s" % ("group", "cells", "ours", "GIVEN", "link", "gap->GIVEN", "gap->link"))
for label, m in groups:
    print("%-38s %6.1f%% %9.4f %9.4f %9.4f %11.4f %11.4f" % (
        label, 100 * m.mean(), pts(ours - ref, m), pts(lp_g - ref, m), pts(lp_t - ref, m),
        pts(lp_g - ours, m), pts(lp_t - ours, m)))
print("%-38s %6.1f%% %9.4f %9.4f %9.4f %11.4f %11.4f" % (
    "all", 100.0, pts(ours - ref, ref == ref), pts(lp_g - ref, ref == ref), pts(lp_t - ref, ref == ref),
    pts(lp_g - ours, ref == ref), pts(lp_t - ours, ref == ref)))
print("(columns ours / GIVEN / link: skill points earned over the crowd marginal; gaps: points we are short)")
# Uncertainty: resample hidden respondents (rows) with replacement; each group's gap is a sum of
# per-row contributions, so a row bootstrap gives its standard error. The oracle itself is a
# Monte Carlo estimate (a.draws simulations per row, +0.1 smoothing), so it is slightly pessimistic.
rng = np.random.default_rng(0)
n_rows = ref.shape[0]
def row_pts(x, m):
    return np.where(m, x, 0.0).sum(1) / (N * R)
named = groups + [("all", ref == ref)]
contrib = {lab: (row_pts(lp_g - ours, m), row_pts(lp_t - ours, m)) for lab, m in named}
B = 1000
idx = rng.integers(0, n_rows, size=(B, n_rows))
print("\nbootstrap over %d hidden rows (B=%d): gap -> GIVEN-only and gap -> link, with standard errors" % (n_rows, B))
for lab, _ in named:
    g, t = contrib[lab]
    print("%-38s %9.4f (se %.4f) %9.4f (se %.4f)" % (lab, g.sum(), g[idx].sum(1).std(ddof=1), t.sum(), t[idx].sum(1).std(ddof=1)))
lk = (O["link"] >= 0)
for lab, m in (("rows with a visible same-household row", lk), ("rows without", ~lk)):
    g = row_pts(lp_g - ours, np.ones_like(ref, bool))[m]
    print("%-38s gap -> GIVEN-only %.4f (se %.4f)" % (lab, g.sum(), np.array([g[rng.integers(0, len(g), len(g))].sum() for _ in range(B)]).std(ddof=1)))
per = pd.DataFrame({"item": O["targets"], "K": O["K"], "gated": O["gated"],
                    "gap_given": (lp_g - ours).sum(0) / (N * R), "gap_link": (lp_t - ours).sum(0) / (N * R),
                    "ours": (ours - ref).sum(0) / (N * R), "best_given": (lp_g - ref).sum(0) / (N * R)})
per = per.sort_values("gap_given", ascending=False)
out = os.path.join(ROOT, "experiments", "eval", "gap_%s_%s_p%d.csv" % (name, a.dataset, a.phase))
per.to_csv(out, index=False)
print("\nper-question gap to the GIVEN-only best: median %.5f, max %.5f, share of questions above 0: %.2f"
      % (per.gap_given.median(), per.gap_given.max(), (per.gap_given > 0).mean()))
print("\nquestions where we are furthest below the GIVEN-only best (skill points):")
print(per.head(15).to_string(index=False, float_format=lambda v: "%.4f" % v))
print("\ngap to GIVEN-only best by number of options:")
for lo, hi in ((2, 3), (4, 6), (7, 10), (11, 99)):
    m = (per.K >= lo) & (per.K <= hi)
    print("  %2d-%2d options: %3d questions, gap %.4f, we earn %.4f of a possible %.4f"
          % (lo, hi, m.sum(), per.gap_given[m].sum(), per.ours[m].sum(), per.best_given[m].sum()))
print("saved", out)
