"""How much the repeat households are worth on real_cps_panel (phase 2: TRAIN+DEV
visible, TEST scored). Uses the private household key written by the builder.

  marginal        crowd marginal (skill 0 by construction; sanity check)
  oracle_link     lam * one-hot(the household's other-wave answer) + (1-lam) * marginal
                  when that row is visible, else marginal (needs the hidden key)
  given_match     same, but the partner is found without the key: the visible rows of
                  the other wave whose GIVEN columns (all but wave) equal the held-out
                  row's; used only when exactly one such row exists
"""
import json, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _realkit as K

name = sys.argv[1] if len(sys.argv) > 1 else "cps_panel"
d = os.path.join(K.DATASETS, "real_" + name)
schema = json.load(open(os.path.join(d, "schema.json")))
f = pd.read_parquet(os.path.join(d, "respondents.parquet"))
key = pd.read_parquet(os.path.join(K.RAW, "cps", "household_key_%s.parquet" % name))
f = f.merge(key, on="respondent_id")
it = schema["items"]
given = [k for k, r in it.items() if r["class"] == "GIVEN"]
pred = [k for k, r in it.items() if r["class"] == "PREDICT"]
opts = {k: list(it[k]["values"]) + (["NA_GATED"] if it[k].get("gate") else []) for k in pred}
vis = f[f.role.isin(["TRAIN", "DEV"])]
hid = f[f.role == "TEST"]
EPS = 1e-3


def score(P):            # P: {item: (n_hidden, K) array}; returns skill vs marginal
    ll = []; llm = []
    for k in pred:
        K_ = len(opts[k]); idx = {o: i for i, o in enumerate(opts[k])}
        y = hid[k].map(idx).to_numpy()
        cnt = vis[k].map(idx).value_counts().reindex(range(K_), fill_value=0).to_numpy() + 0.5
        m = cnt / cnt.sum()
        p = P[k] / P[k].sum(1, keepdims=True)
        ll.append(np.log(EPS + (1 - K_ * EPS) * p[np.arange(len(y)), y]))
        llm.append(np.log(EPS + (1 - K_ * EPS) * m[y]))
    L = np.concatenate(ll).mean(); R = -np.concatenate(llm).mean()
    return 1 + L / R


def build(partner_rows, lam):
    P = {}
    for k in pred:
        K_ = len(opts[k]); idx = {o: i for i, o in enumerate(opts[k])}
        cnt = vis[k].map(idx).value_counts().reindex(range(K_), fill_value=0).to_numpy() + 0.5
        m = cnt / cnt.sum()
        A = np.tile(m, (len(hid), 1))
        for r, prow in enumerate(partner_rows):
            if prow is not None:
                A[r] = (1 - lam) * m
                A[r, idx[prow[k]]] += lam
        P[k] = A
    return P


vis_by_unit = {u: row for u, row in zip(vis.household, vis.to_dict("records"))}
oracle = [vis_by_unit.get(u) for u in hid.household]
gcols = [g for g in given if g != "wave"]
vkey = vis[gcols].astype(str).agg("|".join, axis=1)
groups = {}
for (kk, w), row in zip(zip(vkey, vis.wave), vis.to_dict("records")):
    groups.setdefault((kk, w), []).append(row)
hkey = hid[gcols].astype(str).agg("|".join, axis=1)
gm, n_unique, n_correct = [], 0, 0
for kk, w, u in zip(hkey, hid.wave, hid.household):
    other = [r for (k2, w2) in [(kk, ww) for ww in vis.wave.unique() if ww != w] for r in groups.get((k2, w2), [])]
    if len(other) == 1:
        gm.append(other[0]); n_unique += 1; n_correct += other[0]["household"] == u
    else:
        gm.append(None)
res = {"n_test": len(hid), "test_rows_with_visible_partner": int(sum(o is not None for o in oracle)),
       "given_match_unique": n_unique, "given_match_correct": int(n_correct),
       "marginal": round(score(build([None] * len(hid), 0)), 4)}
for lam in (0.5, 0.8, 0.9, 0.95):
    res["oracle_link_lam%.2f" % lam] = round(score(build(oracle, lam)), 4)
    res["given_match_lam%.2f" % lam] = round(score(build(gm, lam)), 4)
print(json.dumps(res, indent=1))
