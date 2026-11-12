"""Real item-level personality questionnaire: Open-Source Psychometrics Project
BIG5 data (c. 2012), the 50-item IPIP Big-Five Factor Markers with a short
demographics block. PREDICT = the 50 items + quintile bands of the five scored
traits (derived, like the World Bank file's score bands). No routed items.

Source: http://openpsychometrics.org/_rawdata/BIG5.zip
Terms: released "for general public edification" on openpsychometrics.org/_rawdata,
anonymous, research consent at collection; no licence named; IPIP items are public domain.
"""
import json, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _realkit as K

NAME = "big5_ipip"
SEED = 20261115
RAW = os.path.join(K.RAW, "big5", "BIG5")
REVERSED = {"E2", "E4", "E6", "E8", "E10", "N2", "N4", "A1", "A3", "A5", "A7", "C2", "C4", "C6", "C8",
            "O2", "O4", "O6"}


def main():
    d = pd.read_csv(os.path.join(RAW, "data.csv"), sep="\t")
    txt = {}
    for line in open(os.path.join(RAW, "codebook.txt"), encoding="utf-8", errors="replace"):
        p = line.rstrip("\n").split("\t")
        if len(p) == 2 and p[0][:1] in "ENACO" and p[0][1:].isdigit():
            txt[p[0]] = p[1].strip()
    out = pd.DataFrame(index=d.index); q = {}
    lab = lambda c, m: d[c].map(lambda v: m.get(int(v), "No response"))
    out["country"] = K.cap_levels(d.country.fillna("(nu").astype(str).replace({"(nu": "Unknown", "(null)": "Unknown"}), 49)
    out["race"] = lab("race", {1: "Mixed Race", 2: "Arctic", 3: "Caucasian (European)", 4: "Caucasian (Indian)",
                               5: "Caucasian (Middle East)", 6: "Caucasian (North African, Other)",
                               7: "Indigenous Australian", 8: "Native American", 9: "North East Asian", 10: "Pacific",
                               11: "South East Asian", 12: "West African, Bushmen, Ethiopian", 13: "Other"})
    out["race"] = K.cap_rare(out["race"], 0.005)
    out["age"] = K.band(d.age.where((d.age >= 13) & (d.age <= 100)), [12, 17, 21, 25, 30, 40, 50, 100],
                        ["13-17", "18-21", "22-25", "26-30", "31-40", "41-50", "51+"]).fillna("No response")
    out["engnat"] = lab("engnat", {1: "Yes", 2: "No"})
    out["gender"] = lab("gender", {1: "Male", 2: "Female", 3: "Other"})
    out["hand"] = lab("hand", {1: "Right", 2: "Left", 3: "Both"})
    out["source"] = lab("source", {1: "Another page on the test website", 2: "Google", 3: "Facebook",
                                   4: "A .edu domain", 5: "Other source", 6: "Other source or no referer"})
    q.update(country="Participant's technical location (ISO country code).", race="Race (drop-down).",
             age="Age.", engnat="Is English your native language?", gender="Gender.",
             hand="What hand do you use to write with?", source="How the participant came to the test (HTTP referer).")
    given = list(out.columns)
    scale = {1: "1. Disagree", 2: "2", 3: "3. Neutral", 4: "4", 5: "5. Agree"}
    predict = []
    for t in "ENACO":
        for i in range(1, 11):
            c = "%s%d" % (t, i)
            out[c] = lab(c, scale); q[c] = txt.get(c, c); predict.append(c)
    names = {"E": "extraversion", "N": "neuroticism", "A": "agreeableness", "C": "conscientiousness", "O": "openness"}
    for t, nm in names.items():
        vals = []
        for i in range(1, 11):
            c = "%s%d" % (t, i)
            v = d[c].where(d[c] > 0)
            vals.append(6 - v if c in REVERSED else v)
        score = pd.concat(vals, axis=1).mean(axis=1, skipna=True)
        c = "trait_" + nm
        out[c] = K.quantile_band(score, 5, "Quintile ").fillna("Not scored")
        q[c] = "Derived: IPIP Big-Five %s score (mean of 10 items, reverse-keyed where needed), quintile band." % nm
        predict.append(c)
    desc = ("Open-Source Psychometrics Project BIG5 data (c. 2012): the 50-item IPIP Big-Five Factor Markers, "
            "rated 1-5, with demographics, from %d volunteers who confirmed their answers could be used for "
            "research. One row per respondent. Derived items: quintile bands of the five trait scores. No "
            "routed items, so no gates. Missed answers (coded 0) are the ordinary level 'No response'." % len(out))
    frame, schema, _ = K.write_dataset(NAME, out, given, predict, q, {}, desc, SEED)
    K.validate(NAME)
    s, ag = K.summary(frame, schema)
    json.dump({"summary": s, "gates": {}}, open(os.path.join(K.DATASETS, "real_" + NAME, "build_info.json"), "w"), indent=1)
    print(json.dumps(s, indent=1))


if __name__ == "__main__":
    main()
