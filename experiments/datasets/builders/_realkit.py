"""Shared helpers for the real_*.py builders: banding, level capping, gate
inference, role assignment and writing a dataset in the competition format.

Conventions used by every builder:
  * every cell is a string; SKIP marks a cell the instrument did not put to the
    respondent (it becomes NA_GATED when a gate is accepted for the item, or an
    ordinary "Not asked" level when no single parent explains it);
  * item non-response is an ordinary level ("Don't know", "Refused", "No response").
"""
import json, os
import numpy as np, pandas as pd

GATED = "NA_GATED"
SKIP = "__SKIP__"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATASETS = os.path.join(ROOT, "experiments", "datasets")
RAW = os.path.join(DATASETS, "raw")


def cap_levels(s, k, other="Other", keep=()):
    """Keep the k most frequent levels (plus `keep`), fold the rest into `other`."""
    vc = s.value_counts()
    top = set(vc.index[:k]) | set(keep)
    return s.where(s.isin(top), other)


def cap_rare(s, min_share=0.01, min_count=10, other="Other", keep=(SKIP,)):
    """Fold levels rarer than min_share of the answered rows (or < min_count rows)
    into `other`; levels in `keep` are never folded and do not count as answered."""
    ans = s[~s.isin(keep)]
    vc = ans.value_counts()
    thr = max(min_count, min_share * len(ans))
    rare = [v for v in vc.index if vc[v] < thr]
    if len(rare) <= 1:
        return s
    return s.where(~s.isin(rare), other)


def band(x, edges, labels):
    """Cut a numeric series into ordered string bands; NaN stays NaN."""
    out = pd.cut(pd.to_numeric(x, errors="coerce"), edges, labels=labels, right=True)
    return out.astype(object).where(out.notna(), np.nan)


def quantile_band(x, q=5, prefix="Q"):
    v = pd.to_numeric(x, errors="coerce")
    r = pd.qcut(v.rank(method="first"), q, labels=["%s%d" % (prefix, i + 1) for i in range(q)])
    return r.astype(object).where(v.notna(), np.nan)


def infer_gates(df, order, max_parent_levels=60, min_agree=0.6, min_skip=0.01,
                not_asked="Not asked", parents_before_only=False, allowed_parents=None):
    """For every column of `order` holding SKIP cells, find the item p and value
    set S maximising agreement of (cell != SKIP) with (p in S), where S is the set
    of parent values at which most rows hold an answer. Parents may sit anywhere
    in `order` (source files are not always in questionnaire order) unless
    `parents_before_only`; a parent whose accepted gate chain already leads back to
    the item is skipped, so the gate graph has no cycles.

    Mutates df: an accepted item's SKIP cells become GATED; a rejected item's (no
    parent reaches `min_agree`, or SKIP rarer than `min_skip`) become the ordinary
    level `not_asked`. S is rewritten in final values (a parent's SKIP becomes
    GATED or `not_asked`).
    Returns ({item: (parent, S, agreement)}, {item: best agreement or None}).
    """
    pos = {c: i for i, c in enumerate(order)}
    codes = {p: pd.factorize(df[p]) for p in order}
    skips = {p: (df[p] == SKIP).to_numpy() for p in order}
    accepted, rejected = {}, {}
    def chain(p):
        seen = set()
        while p in accepted and p not in seen:
            seen.add(p); p = accepted[p][0]
            yield p
    for item in order:
        skip = (df[item] == SKIP).to_numpy()
        if not skip.any():
            continue
        if skip.mean() < min_skip:
            rejected[item] = None; continue
        obs = ~skip
        best = (-1.0, None, None)
        cands = order[:pos[item]] if parents_before_only else [p for p in order if p != item]
        for p in cands:
            if allowed_parents is not None and p not in allowed_parents:
                continue
            c, uniq = codes[p]
            if len(uniq) > max_parent_levels or len(uniq) < 2:
                continue
            if item in set(chain(p)):
                continue
            if np.array_equal(skips[p], skip):
                continue            # co-routed sibling, not a routing parent
            tot = np.bincount(c, minlength=len(uniq)); hit = np.bincount(c, weights=obs, minlength=len(uniq))
            inS = hit / np.maximum(tot, 1) > 0.5
            if not inS.any() or inS.all():
                continue
            agree = float(np.mean(obs == inS[c]))
            closer = best[1] is not None and abs(pos[p] - pos[item]) < abs(pos[best[1]] - pos[item])
            if agree > best[0] + 1e-12 or (abs(agree - best[0]) <= 1e-12 and closer):
                best = (agree, p, [u for u, f in zip(uniq, inS) if f])
        if best[1] is not None and best[0] >= min_agree:
            accepted[item] = (best[1], best[2], round(best[0], 4))
        else:
            rejected[item] = round(best[0], 4) if best[1] else None
    for item in order:
        if item in accepted:
            df[item] = df[item].where(df[item] != SKIP, GATED)
        elif item in rejected:
            df[item] = df[item].where(df[item] != SKIP, not_asked)
    final = {}
    for item, (p, S, ag) in accepted.items():
        fill = GATED if p in accepted else not_asked
        final[item] = (p, sorted(str(fill if v == SKIP else v) for v in S), ag)
    return final, rejected


def assign_roles(n, seed, frac_train=0.75, frac_dev=0.075, strata=None):
    """Roles at random (optionally stratified), returns (role array, counts)."""
    rng = np.random.default_rng(seed)
    role = np.empty(n, dtype=object)
    groups = [np.arange(n)] if strata is None else [np.flatnonzero(strata == g) for g in pd.unique(strata)]
    for idx in groups:
        idx = rng.permutation(idx)
        a = int(round(frac_train * len(idx))); b = a + int(round(frac_dev * len(idx)))
        role[idx[:a]] = "TRAIN"; role[idx[a:b]] = "DEV"; role[idx[b:]] = "TEST"
    counts = {r: int((role == r).sum()) for r in ("TRAIN", "DEV", "TEST")}
    return role, counts


def write_dataset(name, df, given, predict, questions, gates, description, seed,
                  strata=None, version="real-1", extra_cols=None):
    """df: all-string frame (SKIP allowed only in gated items, replaced here).
    gates: {item: (parent, observed_if list)}. Returns (frame, schema)."""
    out = os.path.join(DATASETS, "real_" + name)
    os.makedirs(out, exist_ok=True)
    df = df.reset_index(drop=True).copy()
    rng = np.random.default_rng(seed)
    perm = rng.permutation(len(df))           # rows randomly permuted, as delivered
    df = df.iloc[perm].reset_index(drop=True)
    if extra_cols is not None:
        extra_cols = extra_cols.iloc[perm].reset_index(drop=True)
    st = None if strata is None else np.asarray(strata)[perm]
    role, counts = assign_roles(len(df), seed + 1, strata=st)
    items = {}
    for c in given + predict:
        col = df[c].astype(str)
        assert (col != SKIP).all(), "%s still holds SKIP" % c
        if c not in gates:
            assert (col != GATED).all(), "%s holds NA_GATED but has no gate" % c
        df[c] = col
        vals = sorted(v for v in col.unique() if v != GATED)
        if c in gates:
            par, S = gates[c][0], gates[c][1]
            gate = {"parent": par, "observed_if": list(S)}
        else:
            gate = None
        items[c] = {"question": questions.get(c, c), "class": "GIVEN" if c in given else "PREDICT",
                    "values": vals, "gate": gate}
    for c in given + predict:
        assert df[c].notna().all() and not (df[c] == "nan").any(), c
    frame = df[given + predict].copy()
    frame.insert(0, "respondent_id", ["R%06d" % i for i in range(len(frame))])
    frame["role"] = role
    schema = {"dataset": {"n_rows": int(len(frame)), "version": version, "description": description},
              "items": items,
              "split": {"n_train": counts["TRAIN"], "n_dev": counts["DEV"], "n_test": counts["TEST"]},
              "gated_value": GATED}
    frame.to_parquet(os.path.join(out, "respondents.parquet"), index=False)
    with open(os.path.join(out, "schema.json"), "w") as fh:
        json.dump(schema, fh, indent=1, ensure_ascii=False)
    return frame, schema, extra_cols


def gate_agreement(frame, schema):
    """Agreement of each gate with who actually holds a value, on the written file."""
    res = {}
    for k, r in schema["items"].items():
        g = r.get("gate")
        if not g:
            continue
        obs = frame[k] != GATED
        res[k] = round(float((obs == frame[g["parent"]].isin(g["observed_if"])).mean()), 4)
    return res


def summary(frame, schema, gates_rej=None):
    it = schema["items"]
    given = [k for k, r in it.items() if r["class"] == "GIVEN"]
    pred = [k for k, r in it.items() if r["class"] == "PREDICT"]
    ag = gate_agreement(frame, schema)
    ks = [len(it[k]["values"]) for k in pred]
    s = {"rows": len(frame), "given": len(given), "predict": len(pred), "gated": len(ag),
         "gate_agree_median": float(np.median(list(ag.values()))) if ag else None,
         "gate_agree_min": min(ag.values()) if ag else None,
         "gate_agree_max": max(ag.values()) if ag else None,
         "predict_K_median": float(np.median(ks)), "predict_K_max": max(ks),
         "gated_cell_share": float(np.mean([(frame[k] == GATED).mean() for k in pred])),
         "split": schema["split"]}
    return s, ag


def validate(name):
    """Run the organisers' schema and frame loaders on the written dataset."""
    import sys
    sys.path.insert(0, os.path.join(ROOT, "starter-kit"))
    import score as S
    from make_sandbox import load_config, load_schema
    out = os.path.join(DATASETS, "real_" + name)
    config = load_config(os.path.join(ROOT, "starter-kit", "config.yml"))
    schema = load_schema(os.path.join(out, "schema.json"), config)
    fr = S.load_frames(out, schema)
    for ph in (1, 2):
        S.sample_rows(schema, fr, ph)
    return True


def repeat_share(frame, unit):
    """Share of held-out rows whose other-wave row (same `unit`) is visible:
    phase 1 (DEV held out, TRAIN visible), phase 2 (TEST held out, TRAIN+DEV visible)."""
    f = pd.DataFrame({"unit": np.asarray(unit), "role": frame["role"].to_numpy()})
    out = {}
    for ph, vis, hid in ((1, ("TRAIN",), "DEV"), (2, ("TRAIN", "DEV"), "TEST")):
        visible_units = pd.Series(f.loc[f.role.isin(vis), "unit"]).value_counts()
        h = f[f.role == hid]
        # count of visible rows with the same unit (the row itself is not visible)
        out["phase%d" % ph] = round(float(h.unit.map(visible_units).fillna(0).gt(0).mean()), 4)
    return out
