"""Real multi-country attitudes survey with a COVID-19 vaccine module and documented
skip codes: Afrobarometer Round 8 merged file, restricted to the Round 8 part-2
countries (fieldwork 2021-2022), which carry the COVID-19 module (information,
lockdown, relief, trust in government vaccine safety, likelihood of getting
vaccinated, "prayer more effective than vaccine").

Skip logic is documented in the data: codes labelled "Not applicable ..." (routed
past) and "Not asked in this country" become the gate sentinel when a gate is
inferred for the item; "Missing", "Refused", "Don't know" stay ordinary levels.

Source: https://www.afrobarometer.org/wp-content/uploads/2023/03/
        afrobarometer_release-dataset_merge-34ctry_r8_en_2023-03-01.sav
        (codebook: .../2025/07/R8_Merge-Codebook_28May24.final_.pdf)
Terms: Afrobarometer data are "free for you to use" (afrobarometer.org/data);
cite Afrobarometer Data, Round 8, 34 countries, 2019-2022, www.afrobarometer.org.
"""
import json, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _realkit as K

NAME = "afrobarometer_r8"
SEED = 20261114
N_ROWS = 20000
SAV = os.path.join(K.RAW, "afrobarometer", "official", "afrobarometer_release-dataset_merge-34ctry_r8_en_2023-03-01.sav")

GIVEN_SRC = ["COUNTRY", "REGION", "URBRUR", "AGE_v2_UN", "Q101", "Q97", "Q98A", "Q2", "Q96B"]
DROP_PREFIX = ("RESPNO", "COUNTRY_", "COUNTRY.", "URBRUR_COND", "EA_", "NOCALL", "PREVINT", "THISINT",
               "DATEINTR", "STRTIME", "ENDTIME", "LENGTH", "Q1", "Q15D", "Q81", "Q91B", "Q99", "Q100", "Q102", "Q103", "Q106", "Q107", "Q108", "Q110", "withinwt", "Combinwt", "EDUC_COND",
               "RELIG_COND", "Q15", "Q16", "Q17", "Q18", "Q46", "Q47", "Q57", "Q58", "Q59", "Q60", "Q61",
               "Q62", "Q63", "Q64", "Q65", "Q66", "Q67", "Q69", "Q70", "Q71", "R1.", "R2.", "R3.", "R4.", "R5.", "R6.", "R7.", "R8part", "AGE_", "LivedPoverty")


def main():
    import pyreadstat
    df, meta = pyreadstat.read_sav(SAV, apply_value_formats=False)
    df = df[df.R8part == 2].reset_index(drop=True)
    df = df.sample(n=min(N_ROWS, len(df)), random_state=SEED).reset_index(drop=True)
    vl, ql = meta.variable_value_labels, meta.column_names_to_labels

    def labelled(c, skip_na=True):
        labs = vl.get(c, {})
        def f(v):
            if pd.isna(v):
                return K.SKIP
            l = labs.get(v)
            if l is None:
                return str(int(v)) if float(v).is_integer() else str(v)
            ll = l.lower()
            if skip_na and (ll.startswith("not applicable") or ll.startswith("not asked")):
                return K.SKIP
            code = int(v) if float(v).is_integer() else v
            return "%s. %s" % (code, " ".join(l.split()))
        return df[c].map(f)

    out = pd.DataFrame(index=df.index); q = {}
    for c in GIVEN_SRC:
        s = labelled(c, skip_na=False).replace(K.SKIP, "Missing")
        if c == "REGION":
            s = K.cap_levels(df.COUNTRY.map(lambda v: vl["COUNTRY"].get(v, str(v))) + ": " + s, 49)
        elif c in ("Q98A", "Q2", "Q96B"):
            s = K.cap_levels(s, 20 if c != "Q96B" else 12)
        out[c] = s; q[c] = ql.get(c) or c
    given = list(GIVEN_SRC)
    predict = []
    for c in df.columns:
        if c in GIVEN_SRC or c.startswith(DROP_PREFIX) or c.endswith("OTHER"):
            continue
        s = labelled(c)
        if c in ("Q35B", "Q35D"):         # suggested min / max age: numeric, band
            num = pd.to_numeric(df[c], errors="coerce")
            ok = (num >= 18) & (num <= 120)
            b = K.band(num.where(ok), [17, 30, 35, 40, 45, 50, 60, 70, 120],
                       ["18-30", "31-35", "36-40", "41-45", "46-50", "51-60", "61-70", "71+"])
            s = s.where(~ok, b)
        if (s != K.SKIP).mean() < 0.03:
            continue
        s = K.cap_rare(s.astype(str), 0.01)
        if s[s != K.SKIP].nunique() < 2:
            continue
        out[c] = s; predict.append(c); q[c] = ql.get(c) or c
    for c in ["DemandDemo", "SupplyDemo"]:
        if c in predict:
            q[c] = "Derived index: " + q[c]
    acc, rej = K.infer_gates(out, given + predict)
    gates = {k: (p, S) for k, (p, S, a) in acc.items()}
    desc = ("Afrobarometer Round 8 (merged release 2023-03-01), face-to-face interviews with adults in the "
            "Round 8 part-2 countries (fieldwork 2021-2022, which carry the COVID-19 module), random subsample "
            "of %d respondents in %d countries. One row per respondent. Covers economic conditions, lived "
            "poverty, democracy and governance, trust in institutions and leaders (including religious and "
            "traditional leaders), corruption, public services, media, COVID-19 (information, lockdown, "
            "relief, trust in vaccine safety, likelihood of vaccination), household assets and services. "
            "Cells the source codes 'Not applicable' (routed past) or 'Not asked in this country' carry the "
            "gate sentinel when a gate was inferred for the item (best single item and value set; not a "
            "constraint the rows satisfy exactly), otherwise the ordinary level 'Not asked'. 'Missing', "
            "'Refused' and 'Don't know' are ordinary levels. Levels under 1%% of answers are folded into "
            "'Other'." % (len(out), out.COUNTRY.nunique()))
    frame, schema, _ = K.write_dataset(NAME, out, given, predict, q, gates, desc, SEED,
                                       strata=out.COUNTRY.to_numpy())
    K.validate(NAME)
    s, ag = K.summary(frame, schema)
    info = {"summary": s,
            "gates": {k: {"parent": acc[k][0], "observed_if": acc[k][1], "agreement": ag[k]} for k in acc},
            "rejected_gates_best_agreement": rej}
    json.dump(info, open(os.path.join(K.DATASETS, "real_" + NAME, "build_info.json"), "w"), indent=1)
    print(json.dumps({"summary": s, "n_rejected": len(rej)}, indent=1))


if __name__ == "__main__":
    main()
