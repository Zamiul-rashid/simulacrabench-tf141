"""Helpers for the real_wb_*.py builders (World-Bank-like real survey data).

Differences from _realkit:
  * gates are declared per item (parent + rule) or chosen from a short list of
    candidate parents by the observed answer rates, never searched over all items;
  * a gated item's blank cell becomes NA_GATED only when the gate says the
    question was not put to the respondent; a blank cell of an eligible
    respondent is ordinary item non-response ("Not answered"), so drop-out and
    routing stay distinguishable, as in the World Bank file;
  * option lists keep their natural order for ordered scales (the schema lists
    `values` in that order), nominal lists are sorted by frequency;
  * a source larger than two samples is cut into disjoint random samples of
    N_ROWS = 6927 rows (5195 / 520 / 1212 after the usual role draw).
"""
import json, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _realkit as K

GATED = K.GATED
NA = "Not answered"
NOT_ASKED = "Not asked"
N_ROWS = 6927


def samples(n_source, k, seed):
    """k disjoint random index sets of N_ROWS rows each."""
    perm = np.random.default_rng(seed).permutation(n_source)
    assert k * N_ROWS <= n_source, (k, n_source)
    return [np.sort(perm[i * N_ROWS:(i + 1) * N_ROWS]) for i in range(k)]


def clean(s):
    """Raw answers as stripped strings, blanks as NaN."""
    s = s.astype(object).where(s.notna(), np.nan)
    s = s.map(lambda v: v if not isinstance(v, str) else (v.strip() or np.nan))
    return s


def num_label(v):
    """1.0 -> '1', 'x' -> 'x'."""
    if isinstance(v, float) and float(v).is_integer():
        return str(int(v))
    return str(v)


def band_num(x, edges, labels):
    """Numeric series -> ordered band strings; NaN stays NaN. Bands are (lo, hi]."""
    v = pd.to_numeric(x, errors="coerce")
    b = pd.cut(v, edges, labels=labels, right=True)
    return b.astype(object).where(b.notna(), np.nan)


def tick(yes, answered, index):
    """Select-all tick: 'Yes' / 'No' when the block was answered, NaN otherwise."""
    out = pd.Series(np.nan, index=index, dtype=object)
    out[np.asarray(answered)] = "No"
    out[np.asarray(answered) & np.asarray(yes)] = "Yes"
    return out


def rule_gate(raw, asked):
    """raw: answers with NaN for blank; asked: boolean eligibility.
    blank & asked -> NA; blank & not asked -> GATED; answers kept."""
    out = raw.astype(object).copy()
    blank = out.isna()
    out[blank & asked] = NA
    out[blank & ~asked] = GATED
    return out


def rate_gate(raw, parent, min_ratio=0.25, max_out=0.10, min_cover=0.003, exclude=(NA, GATED)):
    """Choose S = parent levels whose answer rate is at least `min_ratio` of the
    best level's rate. Accept the gate when some substantive level (not in
    `exclude`) falls outside S, levels outside S hold >= `min_cover` of rows and
    their answer rate is <= `max_out`. min_cover is the share of rows at substantive levels outside S. Returns (S, out_rate) or None."""
    ans = raw.notna()
    rates = ans.groupby(parent).mean()
    cnt = parent.value_counts()
    rates = rates[cnt.reindex(rates.index) >= 5]
    if rates.empty or rates.max() == 0:
        return None
    S = [v for v in rates.index if rates[v] >= min_ratio * rates.max()]
    out = ~parent.isin(S)
    subst_out = [v for v in rates.index if v not in S and v not in exclude]
    if not subst_out or parent.isin(subst_out).mean() < min_cover:
        return None
    out_rate = float(ans[out].mean())
    if out_rate > max_out:
        return None
    return sorted(map(str, S)), out_rate


def finish(raw, gated_asked=None, na=NA):
    """Ungated item: blanks -> `na`. Gated item (asked mask given): rule_gate."""
    if gated_asked is None:
        return raw.astype(object).where(raw.notna(), na)
    return rule_gate(raw, gated_asked)


def write(name, df, given, predict, questions, gates, orders, description, seed):
    """Write experiments/datasets/real_<name>/ via _realkit.write_dataset, then
    put option lists into natural order. gates: {item: (parent, S)};
    orders: {item: [levels in natural order]} (levels missing from the data are
    dropped; levels present but not listed go to the end, 'Not answered' last)."""
    frame, schema, _ = K.write_dataset(name, df, given, predict, questions, gates, description, seed)
    tail = [NOT_ASKED, "Other", "Prefer not to say", NA]
    for k, rec in schema["items"].items():
        vals = rec["values"]
        if k in orders:
            o = [v for v in orders[k] if v in vals]
            rest = [v for v in vals if v not in o]
        else:
            vc = frame[k].value_counts()
            o = [v for v in vc.index if v in vals and v not in tail]
            rest = [v for v in vals if v not in o]
        rest = [v for v in rest if v not in tail] + [v for v in tail if v in rest]
        rec["values"] = o + rest
        assert sorted(rec["values"]) == sorted(vals), k
    path = os.path.join(K.DATASETS, "real_" + name, "schema.json")
    with open(path, "w") as fh:
        json.dump(schema, fh, indent=1, ensure_ascii=False)
    return frame, schema


def stats(frame, schema, orders, given_parents):
    """Numbers for the README / hand-off table."""
    it = schema["items"]
    pred = [k for k, r in it.items() if r["class"] == "PREDICT"]
    given = [k for k, r in it.items() if r["class"] == "GIVEN"]
    ag = K.gate_agreement(frame, schema)
    ks = [len(it[k]["values"]) + (1 if it[k]["gate"] else 0) for k in pred]
    na = float(np.mean([(frame[k] == NA).mean() for k in pred]))
    gated = float(np.mean([(frame[k] == GATED).mean() for k in pred]))
    on_given = sum(1 for k in ag if it[k]["gate"]["parent"] in given)
    def is_ord(k):
        subst = [v for v in orders.get(k, []) if v not in (NA, NOT_ASKED, "Other")]
        return len(subst) > 2 and not set(subst) <= {"No", "Yes"}
    ordered = sum(1 for k in pred if is_ord(k))
    kd = pd.Series(ks).value_counts().sort_index()
    return {"rows": len(frame), "given": len(given), "predict": len(pred), "gated": len(ag),
            "gates_on_given": on_given,
            "gate_agree_median": float(np.median(list(ag.values()))) if ag else None,
            "gate_agree_min": min(ag.values()) if ag else None,
            "gate_agree_max": max(ag.values()) if ag else None,
            "not_answered_share": round(na, 4), "na_gated_share": round(gated, 4),
            "ordered_predict_items": ordered,
            "K_predict": {"min": min(ks), "median": float(np.median(ks)), "max": max(ks),
                          "2-3": int(sum(2 <= k <= 3 for k in ks)), "4-7": int(sum(4 <= k <= 7 for k in ks)),
                          "8-12": int(sum(8 <= k <= 12 for k in ks)), "13+": int(sum(k >= 13 for k in ks))},
            "split": schema["split"]}, ag


def readme(name, title, source, licence, citation, done, frame, schema, st, ag, resemblance):
    it = schema["items"]
    given = [k for k, r in it.items() if r["class"] == "GIVEN"]
    L = ["# real_%s — %s" % (name, title), "",
         "Built by `experiments/datasets/builders/%s` (raw files in `experiments/datasets/raw/`)." % source["builder"], "",
         "- **Source:** %s" % source["url"],
         "- **Licence / terms:** %s" % licence,
         "- **Citation:** %s" % citation, "",
         "## Shape", "",
         "| rows | GIVEN | PREDICT | gated | gates on a GIVEN column | gate agreement median (min-max) | Not answered (mean share over PREDICT) | NA_GATED (mean share) | ordered PREDICT items | split train/dev/test |",
         "|---|---|---|---|---|---|---|---|---|---|",
         "| %d | %d | %d | %d | %d | %s (%s-%s) | %.3f | %.3f | %d | %d / %d / %d |" % (
             st["rows"], st["given"], st["predict"], st["gated"], st["gates_on_given"],
             st["gate_agree_median"], st["gate_agree_min"], st["gate_agree_max"],
             st["not_answered_share"], st["na_gated_share"], st["ordered_predict_items"],
             st["split"]["n_train"], st["split"]["n_dev"], st["split"]["n_test"]), "",
         "Option counts of PREDICT items (NA_GATED included for gated items): %s." % json.dumps(st["K_predict"]), "",
         "## What was done", ""] + ["- " + d for d in done] + [
         "- Every cell is a string; no NaN. A gated item's cell is `NA_GATED` when the gate rule says the question was not put to the respondent and the cell is blank; a blank cell of an eligible respondent is `Not answered` (drop-out / item non-response). Answers given despite the rule are kept, which is why agreement can be below 1.",
         "- Roles drawn at random with a fixed seed (75 / 7.5 / 17.5 %), rows permuted before delivery.",
         "- Validated with the organisers' `load_schema`, `load_frames` and `sample_rows` (phases 1 and 2).", "",
         "## Resemblance to the World Bank file", "", resemblance, "",
         "## Gates", "",
         "| item | parent | parent is GIVEN | observed_if | agreement |", "|---|---|---|---|---|"]
    for k, a in sorted(ag.items(), key=lambda t: t[1]):
        g = it[k]["gate"]
        S = ", ".join(g["observed_if"])
        L.append("| %s | %s | %s | %s | %.4f |" % (k, g["parent"], "yes" if g["parent"] in given else "no",
                                                   S if len(S) < 160 else S[:157] + "...", a))
    L.append("")
    return "\n".join(L)
