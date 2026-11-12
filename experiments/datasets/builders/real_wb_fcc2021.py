"""freeCodeCamp 2021 New Coder Survey -> two World-Bank-like real test sets
(real_wb_fcc2021_s1, _s2), disjoint random samples of 6,927 of the 18,126
respondents.

Why it resembles the World Bank file: people learning to code in 2021, mostly
young (median age about 24) job seekers from all world regions, including about
8 % in Sub-Saharan Africa; last-year earnings already come in fixed USD bands
(GIVEN, like the WB wage bands) and expected first-job salary in bands
(PREDICT, like WB wageOfSimilarEmployeesAfter); job-search plans, months spent
looking for the last job (WB howLongSearchingForJob), job-loss risk and ease of
finding another job (1-10), eight job-satisfaction scales, commute, etc. are
routed on employment status / being a developer, both GIVEN.

The questionnaire was a web form that offered explicit "not applicable" answers
("I am not currently working", "I am already a developer", "Not Applicable",
...) instead of hiding questions. Those answers are treated as "not asked":
they become NA_GATED, and the gate (parent, observed_if) is estimated from the
substantive answer rates; blank cells of eligible respondents are 'Not answered'.

Source: https://www.kaggle.com/datasets/fccuser/2021-new-coder-survey
Licence: CC-BY-SA-4.0 (Kaggle dataset page).
"""
import json, os, re, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _realkit as K
import _wbkit as W

SEED = 20261115
RAW = os.path.join(K.RAW, "fcc2021", "2021 New Coder Survey.csv")
HOURS_E = [-np.inf, 0, 1, 2, 3, 4, 5, 10, 15, 20, 30, 40, np.inf]
HOURS_L = ["0", "1", "2", "3", "4", "5", "6-10", "11-15", "16-20", "21-30", "31-40", "more than 40"]
MONTHS_E = [-np.inf, 0, 1, 3, 6, 12, 24, 60, np.inf]
MONTHS_L = ["Less than one month", "About one month", "2-3 months", "4-6 months", "7-12 months",
            "1-2 years", "2-5 years", "More than 5 years"]
SEARCH_E = [-np.inf, 0, 1, 2, 3, 6, 12, 24, np.inf]
SEARCH_L = ["0", "1", "2", "3", "4-6", "7-12", "13-24", "more than 24"]
SPEND_E = [-np.inf, 0, 99, 499, 999, 4999, np.inf]
SPEND_L = ["0", "1-99", "100-499", "500-999", "1000-4999", "5000+"]
AGE_E = [-np.inf, 19, 24, 29, 34, 44, np.inf]
AGE_L = ["15-19", "20-24", "25-29", "30-34", "35-44", "45+"]
INC_LO = [0, 1000, 3000, 5000, 10000, 15000, 20000, 30000, 50000, 75000, 100000]
INC_L = ["Under 1,000", "1,000-2,999", "3,000-4,999", "5,000-9,999", "10,000-14,999", "15,000-19,999",
         "20,000-29,999", "30,000-49,999", "50,000-74,999", "75,000-99,999", "100,000+"]
SAT = ["Very dissatisfied", "Somewhat dissatisfied", "Somewhat satisfied", "Very satisfied", "I do not know"]
TEN = [str(i) for i in range(1, 11)]
EDU = ["No high school (secondary school)", "Some high school", "High school diploma or equivalent (GED)",
       "Trade, technical, or vocational training", "Some college credit, no degree", "Associate’s degree",
       "Bachelor’s degree", "Master's degree (non-professional)", "Professional degree (MBA, MD, JD, etc.)",
       "Ph.D."]
NOT_WORK = ["I am not currently working", "I am not working"]
NA_ANS = {"q11": ["I am not employed as a developer"], "q12": ["I am already a developer"],
          "q13": ["I am not interested in a software development career"],
          "q14": ["I am not interested in a software development career"],
          "q15": ["I am already a developer", "I am not interested in a software development career"],
          "q16": [], "q19": ["I am not interested in a software development career"],
          "q18": ["I am not interested in a software development career"],
          "q21": NOT_WORK, "q27": ["I am not living in the US"], "q33": ["I didn't attend a university"],
          "q40": NOT_WORK, "q44": ["Not applicable"], "q46": NOT_WORK + ["I work from home"][:0]}
for k in range(1, 9):
    NA_ANS["q45_%d" % k] = ["Not Applicable"]


def lead_num(v):
    m = re.search(r"\$?([\d,]+)", v)
    if v.lower().startswith(("under", "less", "<")):
        return 0
    return int(m.group(1).replace(",", "")) if m else 10 ** 9


def main():
    d = pd.read_csv(RAW, low_memory=False, dtype=str)
    cols = list(d.columns)
    qn = {}
    for c in cols[1:]:
        m = re.match(r"\s*(\d+)\.", c)
        n = int(m.group(1))
        key = "q%d" % n
        if key in qn.values():
            j = 2
            while "%s_%d" % (key, j) in qn.values():
                j += 1
            key = "%s_%d" % (key, j)
        qn[c] = key
    # first column of a repeated grid gets suffix _1
    for base in ("q39", "q45"):
        first = [c for c, k in qn.items() if k == base]
        for c in first:
            qn[c] = base + "_1"
    d = d.rename(columns=qn)
    Q = {v: " ".join(k.split()) for k, v in qn.items()}
    for c in d.columns:
        d[c] = W.clean(d[c])
    o = pd.DataFrame(index=d.index); orders = {}
    # ---------------- GIVEN
    o["q26"] = W.finish(d.q26); Q["q26"] = Q["q26"]
    o["q23"] = W.finish(W.band_num(d.q23, AGE_E, AGE_L)); orders["q23"] = AGE_L + [W.NA]
    g = d.q24.where(d.q24.isin(["Male", "Female", "Nonbinary", "Prefer not to say"]) | d.q24.isna(), "Other")
    o["q24"] = W.finish(g)
    o["q32"] = W.finish(d.q32); orders["q32"] = EDU + [W.NA]
    o["q20"] = W.finish(K.cap_levels(d.q20, 9, keep=(np.nan,)).where(d.q20.notna()))
    o["q10"] = W.finish(d.q10); orders["q10"] = ["No", "Yes", W.NA]
    inc = d.q22.map(lambda v: np.nan if pd.isna(v) else INC_L[max(i for i, lo in enumerate(INC_LO) if lead_num(v) >= lo)])
    o["q22"] = W.finish(inc); orders["q22"] = INC_L + [W.NA]
    Q["q22"] += " (collapsed from 22 to 11 bands)"
    o["q34"] = W.finish(d.q34); orders["q34"] = ["No", "Yes", W.NA]
    o["q28"] = W.finish(d.q28); orders["q28"] = ["Less than 100,000", "Between 100,000 and 1 million",
                                                 "More than 1 million", W.NA]
    given = ["q26", "q23", "q24", "q32", "q20", "q10", "q22", "q34", "q28"]
    # ---------------- PREDICT
    raw, cands, nas = {}, {}, {}

    def add(name, s, cand=(), order=None, question=None):
        raw[name] = s; cands[name] = list(cand); nas[name] = NA_ANS.get(name, [])
        if order:
            orders[name] = order
        if question:
            Q[name] = question
    add("q1", K.cap_levels(d.q1, 8, keep=(np.nan,)).where(d.q1.notna()))
    blocks = {"q2": ["Online resources", "Books", "Online bootcamps", "Workshops", "In-person bootcamps", "School"],
              "q3": ["freeCodeCamp", "Stack Overflow", "Codecademy", "Udemy", "Mozilla Developer Network",
                     "Khan Academy", "W3Schools", "Coursera"],
              "q4": ["I haven't attended any"], "q5": ["I haven't listened to any"],
              "q6": ["I haven't watched any", "freeCodeCamp", "Programming With Mosh", "CS Dojo"],
              "q17": ["well paid", "I love coding", "new technology"]}
    for b, opts in blocks.items():
        for j, opt in enumerate(opts, 1):
            nm = "%s_tick%d" % (b, j)
            add(nm, W.tick(d[b].str.contains(re.escape(opt), case=False, na=False), d[b].notna(), d.index),
                order=["No", "Yes"], question="%s - %s" % (Q[b], opt))
    add("q7", W.band_num(d.q7, HOURS_E, HOURS_L), order=HOURS_L)
    add("q8", W.band_num(d.q8, MONTHS_E, MONTHS_L), order=MONTHS_L)
    add("q9", W.band_num(d.q9, SPEND_E, SPEND_L), order=SPEND_L)
    add("q11", d.q11, ["q10"])
    add("q12", d.q12, ["q10"])
    add("q13", K.cap_levels(d.q13, 7, keep=(np.nan,)).where(d.q13.notna()), ["q12", "q10"])
    add("q14", K.cap_levels(d.q14, 14, keep=(np.nan,)).where(d.q14.notna()), ["q12", "q10"])
    add("q15", d.q15, ["q12", "q10"], ["I am already applying", "Within the next 6 months",
                                         "Within 7 to 12 months from now", "More than 12 months from now",
                                         "I haven’t decided"])
    exp_vals = sorted([v for v in d.q16.dropna().unique()], key=lead_num)
    add("q16", d.q16, ["q12", "q10"], exp_vals)
    add("q18", K.cap_levels(d.q18, 7, keep=(np.nan,)).where(d.q18.notna()), ["q12", "q10"],
        ["All days in an office", "1 day from home and 4 days in an office",
         "2 days from home and 3 days in an office", "3 days from home and 2 days in an office",
         "4 days from home and 1 day in an office", "All days from home"])
    add("q19", d.q19, ["q12", "q10"], ["No", "Maybe", "Yes"])
    add("q21", K.cap_levels(d.q21, 16, keep=(np.nan,)).where(d.q21.notna()), ["q20"])
    add("q25", K.cap_levels(d.q25, 10, keep=(np.nan,)).where(d.q25.notna()))
    add("q27", K.cap_levels(d.q27, 12, keep=(np.nan,)).where(d.q27.notna()), ["q26"])
    for c in ["q29", "q30", "q31"]:
        add(c, d[c], order=["No", "Yes"])
    add("q33", K.cap_levels(d.q33, 12, keep=(np.nan,)).where(d.q33.notna()), ["q32"])
    add("q35", d.q35)
    add("q36", d.q36, [], ["0", "1", "2", "3", "4", "5", "more than 5"])
    add("q37", d.q37, [], ["No", "Yes"])
    add("q38", d.q38, [], ["No", "Maybe", "Yes"])
    DEBT = ["<$10k", "$10k- $25k", "$26k- $50k", "$51k- $100k", "$101k- $200k", "$201k- $500k", ">$500k"]
    for k in range(1, 8):
        nm = "q39_%d" % k
        add(nm, d[nm].fillna("None / left blank"), [], ["None / left blank"] + DEBT)
    add("q40", d.q40, ["q20"], ["Less than 6 months", "6 to 11 months", "1 to 3 years", "more than 3 years"])
    add("q41", W.band_num(d.q41, SEARCH_E, SEARCH_L), [], SEARCH_L)
    Q["q41"] += " (months, banded)"
    add("q42", d.q42.map(lambda v: v if pd.isna(v) else W.num_label(float(v))), ["q20"], TEN)
    add("q43", d.q43.map(lambda v: v if pd.isna(v) else W.num_label(float(v))), ["q20"], TEN)
    add("q44", d.q44, ["q20"], ["No", "Yes"])
    for k in range(1, 9):
        add("q45_%d" % k, d["q45_%d" % k], ["q20"], SAT)
    add("q46", d.q46, ["q20"], ["I work from home", "Less than 15 minutes", "15 to 29 minutes", "30 to 44 minutes",
                                "45 to 60 minutes", "More than 60 minutes"])
    add("q47", d.q47, [], ["No", "Yes", "Not applicable"])
    add("q48", d.q48, [], ["No", "Yes"])
    add("q49", d.q49, [], ["No", "Yes"])
    gates, predict = {}, []
    for name, s in raw.items():
        na_mask = s.map(lambda v: isinstance(v, str) and any(v.startswith(x) for x in nas[name])).astype(bool)
        subst = s.where(~na_mask)
        chosen = None
        for p in cands[name]:
            par = o[p]
            r = W.rate_gate(subst, par, max_out=0.2)
            if r is not None:
                chosen = (p, r[0]); break
        if chosen:
            cell = W.rule_gate(subst, o[chosen[0]].isin(chosen[1]))
            cell[na_mask] = W.GATED
            gates[name] = chosen
        else:
            if cands[name]:
                print("no gate for", name, "N/A answers kept as a level:", int(na_mask.sum()))
            cell = W.finish(s)
        o[name] = cell
        predict.append(name)
    for k, lst in orders.items():
        miss = set(o[k].unique()) - set(lst) - {W.GATED, W.NA, "Other"}
        if miss:
            print("ORDER MISSING", k, miss)
    for i, idx in enumerate(W.samples(len(d), 2, SEED), 1):
        name = "wb_fcc2021_s%d" % i
        oi = o.iloc[idx].reset_index(drop=True)
        desc = ("freeCodeCamp 2021 New Coder Survey (online, mid-2021): people learning to code, mostly young job "
                "seekers from all world regions (about 8 %% in Sub-Saharan Africa). Random sample %d of 2 (disjoint) "
                "of 6,927 out of 18,126 respondents. Column names are the questionnaire numbers (q1..q49; grids "
                "q39_k, q45_k; select-all ticks qN_tickK). GIVEN: world region, age band, gender, education, "
                "employment status, already a developer, last-year earnings band (USD), student, city size. "
                "PREDICT: learning methods and resources, weekly learning hours, months programming, money spent, "
                "developer-career interest, preferred employer type, target role, when they will apply, expected "
                "first-job salary band, remote-work preference, relocation, job field, household items, debts, job "
                "tenure, months spent looking for the last job, job-loss risk and ease of finding a job (1-10), "
                "eight job-satisfaction scales, commute. Explicit 'not applicable' answers are NA_GATED; blank "
                "cells of eligible respondents are 'Not answered'." % i)
        frame, schema = W.write(name, oi, given, predict, Q, gates, orders, desc, SEED + i)
        K.validate(name)
        st, ag = W.stats(frame, schema, orders, given)
        out = os.path.join(K.DATASETS, "real_" + name)
        json.dump({"summary": st, "gates": {k: {"parent": gates[k][0], "observed_if": gates[k][1],
                                                "agreement": ag[k]} for k in gates}},
                  open(os.path.join(out, "build_info.json"), "w"), indent=1)
        txt = W.readme(name, "freeCodeCamp 2021 New Coder Survey (sample %d of 2)" % i,
                       {"builder": "real_wb_fcc2021.py",
                        "url": "https://www.kaggle.com/datasets/fccuser/2021-new-coder-survey (file '2021 New Coder Survey.csv')"},
                       "CC-BY-SA-4.0 (as listed on the Kaggle dataset page). Downloaded with the Kaggle CLI, no extra terms.",
                       "freeCodeCamp (2021). 2021 New Coder Survey. Kaggle dataset fccuser/2021-new-coder-survey.",
                       ["One row per respondent; disjoint random samples of 6,927 rows (seed %d), `_s1` and `_s2`." % SEED,
                        "Item names are the question numbers; the full question text is in schema.json.",
                        "Last-year earnings (q22) collapsed from 22 USD bands to 11 (GIVEN); expected first-job salary (q16) keeps its 12 bands; hours learning in the World Bank hour bands; months programming and months spent looking for the last job in duration bands; age banded.",
                        "Explicit 'not applicable' answers (e.g. 'I am not currently working', 'I am already a developer', 'Not Applicable', 'I am not living in the US') become NA_GATED. The gate parent is chosen from a short candidate list (questionnaire logic) by substantive answer rates: parent levels answering at >= 25 % of the best level's rate form observed_if; the gate is kept when the other levels answer at most 20 %. Blank cells of eligible respondents are 'Not answered'. Where no gate is accepted the 'not applicable' answer stays an ordinary level.",
                        "Select-all questions (learning methods, resources, events, podcasts, YouTube, reasons) reduced to a few tick items: 'Yes' / 'No' if the question was answered, otherwise 'Not answered'. Debt grid (q39_k): a blank row is the level 'None / left blank'.",
                        "Employment status capped at 9 levels + Other (free-text 'other' answers); other nominal items capped similarly."],
                       frame, schema, st, ag,
                       "Closest of the sets to the World Bank file: a global (incl. Sub-Saharan African) young job-seeker population, earnings in fixed bands as GIVEN, expected-salary bands, job-search plans and months spent searching, employment-status-routed job blocks with ordered 1-10 and 4-point satisfaction scales, gates mostly on GIVEN columns. Different: no psychometric or cognitive-task scores, no randomised arm or follow-up wave, 'not asked' is partly self-declared (explicit not-applicable answers) rather than enforced routing, so gate agreement is below 1.")
        open(os.path.join(out, "README.md"), "w").write(txt)
        print(name, json.dumps(st))


if __name__ == "__main__":
    main()
