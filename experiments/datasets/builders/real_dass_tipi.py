"""Real item-level self-report questionnaire with derived score bands:
Open-Source Psychometrics Project, online DASS-42 (Depression Anxiety Stress
Scales) + TIPI (Ten Item Personality Inventory) + a 16-word vocabulary check
list, 2017-2019, with a demographics block.

PREDICT: the 42 DASS items, 10 TIPI items, 16 vocabulary items, the standard
DASS-42 severity bands for depression/anxiety/stress, quintile bands of the five
TIPI trait scores, a vocabulary-score band, a test-duration band and the two
technical fields (screen size, referral source). No skip logic in this
instrument (the one routed item, university major, is free text and dropped).

Source: https://openpsychometrics.org/_rawdata/DASS_data_21.02.19.zip
Terms: the raw-data page says the data are dumped "for general public edification",
anonymous, collected with research consent; no licence named, no registration.
"""
import json, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _realkit as K

NAME = "dass_tipi"
SEED = 20261113
N_ROWS = 20000
RAW = os.path.join(K.RAW, "dass", "DASS_data_21.02.19")

DEP = [3, 5, 10, 13, 16, 17, 21, 24, 26, 31, 34, 37, 38, 42]
ANX = [2, 4, 7, 9, 15, 19, 20, 23, 25, 28, 30, 36, 40, 41]
STR = [1, 6, 8, 11, 12, 14, 18, 22, 27, 29, 32, 33, 35, 39]
BANDS = ["Normal", "Mild", "Moderate", "Severe", "Extremely severe"]


def items_text():
    txt = open(os.path.join(RAW, "codebook.txt"), encoding="utf-8", errors="replace").read()
    out = {}
    for line in txt.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2 and parts[0].strip():
            out[parts[0].strip()] = " ".join(p.strip() for p in parts[1:] if p.strip()).replace("&#39;", "'").replace("&quot;", '"')
    return out


def main():
    d = pd.read_csv(os.path.join(RAW, "data.csv"), sep="\t")
    d = d.sample(n=N_ROWS, random_state=SEED).reset_index(drop=True)
    txt = items_text()
    out = pd.DataFrame(index=d.index); q = {}
    def lab(col, mapping, missing="No response"):
        return d[col].map(lambda v: mapping.get(int(v), missing) if pd.notna(v) else missing)
    out["country"] = K.cap_levels(d.country.fillna("NONE").astype(str).replace({"NONE": "Unknown"}), 49)
    q["country"] = "Country the respondent connected from (ISO code)."
    out["education"] = lab("education", {1: "Less than high school", 2: "High school", 3: "University degree", 4: "Graduate degree"})
    out["urban"] = lab("urban", {1: "Rural (country side)", 2: "Suburban", 3: "Urban (town, city)"})
    out["gender"] = lab("gender", {1: "Male", 2: "Female", 3: "Other"})
    out["engnat"] = lab("engnat", {1: "Yes", 2: "No"})
    out["age"] = K.band(d.age, [0, 17, 21, 25, 30, 40, 50, 200], ["<=17", "18-21", "22-25", "26-30", "31-40", "41-50", "51+"])
    out["hand"] = lab("hand", {1: "Right", 2: "Left", 3: "Both"})
    out["religion"] = lab("religion", {1: "Agnostic", 2: "Atheist", 3: "Buddhist", 4: "Christian (Catholic)",
                                       5: "Christian (Mormon)", 6: "Christian (Protestant)", 7: "Christian (Other)",
                                       8: "Hindu", 9: "Jewish", 10: "Muslim", 11: "Sikh", 12: "Other"})
    out["orientation"] = lab("orientation", {1: "Heterosexual", 2: "Bisexual", 3: "Homosexual", 4: "Asexual", 5: "Other"})
    out["race"] = lab("race", {10: "Asian", 20: "Arab", 30: "Black", 40: "Indigenous Australian",
                               50: "Native American", 60: "White", 70: "Other"})
    out["voted"] = lab("voted", {1: "Yes", 2: "No"})
    out["married"] = lab("married", {1: "Never married", 2: "Currently married", 3: "Previously married"})
    out["familysize"] = K.band(d.familysize.where(d.familysize > 0), [0, 1, 2, 3, 4, 5, 100], ["1", "2", "3", "4", "5", "6+"])
    for c in ["age", "familysize"]:
        out[c] = out[c].fillna("No response")
    qs = {"education": "How much education have you completed?", "urban": "What type of area did you live when you were a child?",
          "gender": "What is your gender?", "engnat": "Is English your native language?", "age": "How many years old are you?",
          "hand": "What hand do you use to write with?", "religion": "What is your religion?",
          "orientation": "What is your sexual orientation?", "race": "What is your race?",
          "voted": "Have you voted in a national election in the past year?", "married": "What is your marital status?",
          "familysize": "Including you, how many children did your mother have?"}
    q.update(qs)
    given = list(out.columns)
    scale = {1: "1. Did not apply to me at all", 2: "2. Applied to me to some degree, or some of the time",
             3: "3. Applied to me to a considerable degree, or a good part of the time",
             4: "4. Applied to me very much, or most of the time"}
    predict = []
    for i in range(1, 43):
        c = "Q%dA" % i
        out[c] = lab(c, scale); q[c] = txt.get("Q%d" % i, c); predict.append(c)
    tipi = {1: "1. Disagree strongly", 2: "2. Disagree moderately", 3: "3. Disagree a little", 4: "4. Neither agree nor disagree",
            5: "5. Agree a little", 6: "6. Agree moderately", 7: "7. Agree strongly"}
    for i in range(1, 11):
        c = "TIPI%d" % i
        out[c] = lab(c, tipi); q[c] = "I see myself as: " + txt.get(c, c); predict.append(c)
    for i in range(1, 17):
        c = "VCL%d" % i
        out[c] = lab(c, {1: "Checked (knows the word)", 0: "Unchecked"}); q[c] = "Word check list: " + txt.get(c, c); predict.append(c)
    # derived score bands (DASS-42 standard severity cut-offs; items scored 0-3)
    sc = lambda idx: sum(d["Q%dA" % i] - 1 for i in idx)
    cuts = {"dass_depression": (DEP, [-1, 9, 13, 20, 27, 99]), "dass_anxiety": (ANX, [-1, 7, 9, 14, 19, 99]),
            "dass_stress": (STR, [-1, 14, 18, 25, 33, 99])}
    for c, (idx, e) in cuts.items():
        out[c] = pd.cut(sc(idx), e, labels=BANDS).astype(str)
        q[c] = "Derived: DASS-42 %s severity band (standard cut-offs)." % c.split("_")[1]
        predict.append(c)
    tv = {i: d["TIPI%d" % i].where(d["TIPI%d" % i] > 0) for i in range(1, 11)}
    traits = {"tipi_extraversion": (1, 6), "tipi_agreeableness": (7, 2), "tipi_conscientiousness": (3, 8),
              "tipi_emotional_stability": (9, 4), "tipi_openness": (5, 10)}
    for c, (pos, rev) in traits.items():
        score = (tv[pos] + (8 - tv[rev])) / 2
        out[c] = K.quantile_band(score, 5, "Quintile ").fillna("Not scored")
        q[c] = "Derived: TIPI %s score, quintile band within the sample." % c.split("_", 1)[1].replace("_", " ")
        predict.append(c)
    real = [i for i in range(1, 17) if i not in (6, 9, 12)]
    vs = d[["VCL%d" % i for i in real]].sum(axis=1) - d[["VCL6", "VCL9", "VCL12"]].sum(axis=1)
    out["vocab_score"] = pd.cut(vs, [-4, 6, 8, 10, 11, 12, 13], labels=["<=6", "7-8", "9-10", "11", "12", "13"]).astype(str)
    q["vocab_score"] = "Derived: real words checked minus fake words checked (band)."
    out["test_duration"] = K.quantile_band(d.testelapse, 5, "Quintile ").astype(str)
    q["test_duration"] = "Derived: time spent on the DASS items (quintile band; Quintile 1 = fastest)."
    out["screensize"] = lab("screensize", {1: "Small screen (phone etc.)", 2: "Big screen (laptop, desktop)"})
    q["screensize"] = "Device screen size."
    out["source"] = lab("source", {0: "Other or unknown", 1: "Front page of the hosting site", 2: "Google"})
    q["source"] = "How the respondent found the test."
    predict += ["vocab_score", "test_duration", "screensize", "source"]
    for c in given + predict:
        out[c] = out[c].astype(str)
    desc = ("Open-Source Psychometrics Project online DASS-42 (Depression Anxiety Stress Scales) with the "
            "Ten Item Personality Inventory, a 16-word vocabulary check list (3 fake words) and a demographics "
            "block, collected 2017-2019 from volunteers who agreed their answers could be used for research; "
            "random subsample of %d of 39,775 respondents. One row per respondent. Derived items: DASS-42 "
            "severity bands (standard cut-offs), TIPI trait quintile bands, a vocabulary-score band and a "
            "test-duration quintile band. No item is routed, so no gates. Item non-response (coded 0) is the "
            "ordinary level 'No response'." % len(out))
    frame, schema, _ = K.write_dataset(NAME, out, given, predict, q, {}, desc, SEED)
    K.validate(NAME)
    s, ag = K.summary(frame, schema)
    json.dump({"summary": s, "gates": {}}, open(os.path.join(K.DATASETS, "real_" + NAME, "build_info.json"), "w"), indent=1)
    print(json.dumps(s, indent=1))


if __name__ == "__main__":
    main()
