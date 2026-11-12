"""Stack Overflow Developer Survey 2018 -> three World-Bank-like real test sets
(real_wb_so2018_s1, _s2, _s3), disjoint random samples of 6,927 of the 98,855
respondents.

Why it resembles the World Bank file: a long single-session online survey of
developers and students with an employment status, a job-seeking status, a
salary band, ordered satisfaction / frequency / interest scales, ranking blocks
about what matters when assessing a job (AssessJob 1-10, AssessBenefits 1-11)
and how to be contacted about a job, routing on employment (company size, job
satisfaction, last new job, ...) and on earlier answers (ad-blocker, Stack
Overflow account / Jobs, bootcamp), and heavy drop-out: demographics come last,
so even GIVEN columns carry 'Not answered'.

Source: https://www.kaggle.com/datasets/stackoverflow/stack-overflow-2018-developer-survey
(also https://survey.stackoverflow.co/). Licence: Open Database License (ODbL) /
Database Contents License (DbCL-1.0) as listed on the Kaggle page.
"""
import json, os, re, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _realkit as K
import _wbkit as W

SEED = 20261114
RAWD = os.path.join(K.RAW, "so2018")
NSAMP = 3
SAL_E = [-np.inf, 0, 9999, 24999, 49999, 74999, 99999, 149999, 199999, np.inf]
SAL_L = ["0", "1-9999", "10000-24999", "25000-49999", "50000-74999", "75000-99999", "100000-149999",
         "150000-199999", "200000+"]
CNT_E = [-np.inf, 1, 2, 3, 5, 8, np.inf]
CNT_L = ["1", "2", "3", "4-5", "6-8", "9+"]

AGREE = ["Strongly disagree", "Disagree", "Neither Agree nor Disagree", "Agree", "Strongly agree"]
SATIS = ["Extremely dissatisfied", "Moderately dissatisfied", "Slightly dissatisfied",
         "Neither satisfied nor dissatisfied", "Slightly satisfied", "Moderately satisfied", "Extremely satisfied"]
FREQ_SO = ["I have never visited Stack Overflow (before today)", "I have never participated in Q&A on Stack Overflow",
           "Less than once per month or monthly", "A few times per month or weekly", "A few times per week",
           "Daily or almost daily", "Multiple times per day"]
INTEREST = ["Not at all interested", "A little bit interested", "Somewhat interested", "Very interested",
            "Extremely interested"]
ORD = {
    "Age": ["Under 18 years old", "18 - 24 years old", "25 - 34 years old", "35 - 44 years old", "45 - 54 years old",
            "55 - 64 years old", "65 years or older"],
    "JobSatisfaction": SATIS, "CareerSatisfaction": SATIS,
    "LastNewJob": ["I've never had a job", "Less than a year ago", "Between 1 and 2 years ago",
                   "Between 2 and 4 years ago", "More than 4 years ago"],
    "TimeFullyProductive": ["Less than a month", "One to three months", "Three to six months", "Six to nine months",
                            "Nine months to a year", "More than a year"],
    "TimeAfterBootcamp": ["I already had a full-time job as a developer when I began the program",
                          "Immediately after graduating", "Less than a month", "One to three months",
                          "Four to six months", "Six months to a year", "Longer than a year",
                          "I haven’t gotten a developer job"],
    "NumberMonitors": ["1", "2", "3", "4", "More than 4"],
    "CheckInCode": ["Never", "Less than once per month", "Weekly or a few times per month", "A few times per week",
                    "Once a day", "Multiple times per day"],
    "StackOverflowVisit": FREQ_SO, "StackOverflowParticipate": FREQ_SO,
    "HoursComputer": ["Less than 1 hour", "1 - 4 hours", "5 - 8 hours", "9 - 12 hours", "Over 12 hours"],
    "HoursOutside": ["Less than 30 minutes", "30 - 59 minutes", "1 - 2 hours", "3 - 4 hours", "Over 4 hours"],
    "SkipMeals": ["Never", "1 - 2 times per week", "3 - 4 times per week", "Daily or almost every day"],
    "Exercise": ["I don't typically exercise", "1 - 2 times per week", "3 - 4 times per week",
                 "Daily or almost every day"],
    "SurveyTooLong": ["The survey was too short", "The survey was an appropriate length", "The survey was too long"],
    "SurveyEasy": ["Very difficult", "Somewhat difficult", "Neither easy nor difficult", "Somewhat easy", "Very easy"],
    "WakeTime": ["Before 5:00 AM", "Between 5:00 - 6:00 AM", "Between 6:01 - 7:00 AM", "Between 7:01 - 8:00 AM",
                 "Between 8:01 - 9:00 AM", "Between 9:01 - 10:00 AM", "Between 10:01 - 11:00 AM",
                 "Between 11:01 AM - 12:00 PM", "After 12:01 PM", "I work night shifts",
                 "I do not have a set schedule"],
    "AIFuture": ["I'm worried about the dangers more than I'm excited about the possibilities.",
                 "I don't care about it, or I haven't thought about it.",
                 "I'm excited about the possibilities more than worried about the dangers."],
    "EthicalImplications": ["No", "Unsure / I don't know", "Yes"],
    "OpenSource": ["No", "Yes"], "Hobby": ["No", "Yes"],
}
EDU_KEYS = ["never completed", "Primary", "Secondary", "Some college", "Associate", "Bachelor", "Master",
            "Professional", "doctoral"]
SIZE_KEYS = ["Fewer than 10", "10 to 19", "20 to 99", "100 to 499", "500 to 999", "1,000 to", "5,000 to", "10,000"]

PRED_SIMPLE = (["OpenSource", "UndergradMajor", "CompanySize", "YearsCodingProf", "JobSatisfaction",
                "CareerSatisfaction", "HopeFiveYears", "JobSearchStatus", "LastNewJob"] +
               ["AssessJob%d" % i for i in range(1, 11)] + ["AssessBenefits%d" % i for i in range(1, 12)] +
               ["JobContactPriorities%d" % i for i in range(1, 6)] +
               ["UpdateCV", "TimeFullyProductive", "TimeAfterBootcamp", "AgreeDisagree1", "AgreeDisagree2",
                "AgreeDisagree3", "OperatingSystem", "NumberMonitors", "CheckInCode", "AdBlocker", "AdBlockerDisable",
                "AIDangerous", "AIInteresting", "AIResponsible", "AIFuture", "EthicsChoice", "EthicsReport",
                "EthicsResponsible", "EthicalImplications", "StackOverflowRecommend", "StackOverflowVisit",
                "StackOverflowHasAccount", "StackOverflowParticipate", "StackOverflowJobs", "StackOverflowDevStory",
                "StackOverflowJobsRecommend", "StackOverflowConsiderMember"] +
               ["HypotheticalTools%d" % i for i in range(1, 6)] +
               ["WakeTime", "HoursComputer", "HoursOutside", "SkipMeals", "Exercise", "EducationParents",
                "Dependents", "SurveyTooLong", "SurveyEasy"])
CANDS = {"UndergradMajor": ["FormalEducation"], "AdBlockerDisable": ["AdBlocker"],
         "StackOverflowParticipate": ["StackOverflowHasAccount"], "StackOverflowDevStory": ["StackOverflowJobs", "StackOverflowHasAccount"],
         "StackOverflowJobsRecommend": ["StackOverflowJobs"], "StackOverflowConsiderMember": ["StackOverflowHasAccount"],
         "TimeAfterBootcamp": ["EducationBootcamp"], "EthicsReport": ["EthicsChoice"]}
GIVEN_CANDS = ["Employment", "Student", "FormalEducation"]


def key_order(vals, keys):
    def rank(v):
        for i, k in enumerate(keys):
            if k.lower() in v.lower():
                return i
        return len(keys)
    return sorted(vals, key=rank)


def num_order(vals):
    def lead(v):
        m = re.match(r"\s*(\d+)", v.replace(",", ""))
        return int(m.group(1)) if m else (-1 if v.lower().startswith(("fewer", "less", "under")) else 10 ** 9)
    return sorted(vals, key=lead)


def main():
    cols = ["Hobby", "Country", "Student", "Employment", "FormalEducation", "YearsCoding", "ConvertedSalary", "Gender",
            "Age", "DevType", "LanguageWorkedWith", "EducationTypes"] + [c for c in PRED_SIMPLE if c not in
                                                                         ("Hobby",)]
    cols = list(dict.fromkeys(cols))
    d = pd.read_csv(os.path.join(RAWD, "survey_results_public.csv"), usecols=cols, low_memory=False)
    sch = pd.read_csv(os.path.join(RAWD, "survey_results_schema.csv"))
    Q = dict(zip(sch.Column, sch.QuestionText))
    o = pd.DataFrame(index=d.index); orders = {}
    # ---- GIVEN
    o["Hobby"] = W.finish(W.clean(d.Hobby))
    o["Country"] = W.finish(K.cap_levels(W.clean(d.Country), 20, keep=(np.nan,)).where(d.Country.notna()))
    o["Student"] = W.finish(W.clean(d.Student))
    o["Employment"] = W.finish(W.clean(d.Employment))
    o["FormalEducation"] = W.finish(W.clean(d.FormalEducation))
    o["YearsCoding"] = W.finish(W.clean(d.YearsCoding))
    g = W.clean(d.Gender)
    o["Gender"] = W.finish(g.where(g.isin(["Male", "Female"]) | g.isna(), "Other / several"))
    o["Age"] = W.finish(W.clean(d.Age))
    emp_S = ["Employed full-time", "Employed part-time", "Independent contractor, freelancer, or self-employed"]
    sal = W.band_num(d.ConvertedSalary, SAL_E, SAL_L)
    o["SalaryBand"] = np.where(o.Employment.isin(emp_S), sal.fillna(W.NA), sal.fillna(W.NOT_ASKED))
    orders["SalaryBand"] = SAL_L + [W.NOT_ASKED, W.NA]
    Q["SalaryBand"] = Q["ConvertedSalary"] + " (banded; asked of the employed, others 'Not asked')"
    given = ["Hobby", "Country", "Student", "Employment", "FormalEducation", "YearsCoding", "Gender", "Age",
             "SalaryBand"]
    # ---- PREDICT raw
    raw = {}
    for c in PRED_SIMPLE:
        s = d[c]
        if s.dtype != object:
            s = s.map(lambda v: np.nan if pd.isna(v) else W.num_label(v))
        raw[c] = W.clean(s)
    for c in ["UndergradMajor"]:
        raw[c] = K.cap_levels(raw[c], 10, keep=(np.nan,)).where(raw[c].notna())
    raw["DevTypeCount"] = W.band_num(d.DevType.str.count(";") + 1, CNT_E, CNT_L)
    raw["LanguageCount"] = W.band_num(d.LanguageWorkedWith.str.count(";") + 1, CNT_E, CNT_L)
    Q["DevTypeCount"] = "Number of developer roles ticked in 'Which of the following describe you?' (banded)"
    Q["LanguageCount"] = "Number of languages ticked as worked with extensively in the past year (banded)"
    et = d.EducationTypes
    raw["EducationBootcamp"] = W.tick(et.str.contains("bootcamp", na=False), et.notna(), d.index)
    Q["EducationBootcamp"] = Q["EducationTypes"] + " - Participated in a full-time developer training program or bootcamp"
    order_pred = ["OpenSource", "UndergradMajor", "CompanySize", "YearsCodingProf", "DevTypeCount", "LanguageCount",
                  "JobSatisfaction", "CareerSatisfaction", "HopeFiveYears", "JobSearchStatus", "LastNewJob"] + \
                 [c for c in PRED_SIMPLE if c.startswith(("AssessJob", "AssessBenefits", "JobContact"))] + \
                 ["UpdateCV", "TimeFullyProductive", "EducationBootcamp"] + \
                 [c for c in PRED_SIMPLE if c not in ("OpenSource", "UndergradMajor", "CompanySize", "YearsCodingProf",
                                                      "JobSatisfaction", "CareerSatisfaction", "HopeFiveYears",
                                                      "JobSearchStatus", "LastNewJob", "UpdateCV", "TimeFullyProductive")
                  and not c.startswith(("AssessJob", "AssessBenefits", "JobContact"))]
    gates, predict = {}, []
    for name in order_pred:
        s = raw[name]
        chosen = None
        for p in CANDS.get(name, []) + GIVEN_CANDS:
            r = W.rate_gate(s, o[p])
            if r is not None:
                chosen = (p, r[0]); break
        if chosen:
            o[name] = W.rule_gate(s, o[chosen[0]].isin(chosen[1])); gates[name] = chosen
        else:
            o[name] = W.finish(s)
        predict.append(name)
    # ---- natural orders
    for c in given + predict:
        vals = [v for v in o[c].unique() if v not in (W.NA, W.GATED, W.NOT_ASKED)]
        if c in orders:
            continue
        if c in ORD:
            orders[c] = ORD[c]
        elif c in ("FormalEducation", "EducationParents"):
            orders[c] = key_order(vals, EDU_KEYS)
        elif c == "CompanySize":
            orders[c] = key_order(vals, SIZE_KEYS)
        elif c in ("YearsCoding", "YearsCodingProf", "StackOverflowRecommend", "StackOverflowJobsRecommend") or \
                c.startswith(("AssessJob", "AssessBenefits", "JobContact")):
            orders[c] = num_order(vals)
        elif c.startswith(("AgreeDisagree",)):
            orders[c] = AGREE
        elif c.startswith("HypotheticalTools"):
            orders[c] = INTEREST
        elif c in ("DevTypeCount", "LanguageCount"):
            orders[c] = CNT_L
        else:
            continue
        miss = set(vals) - set(orders[c])
        if miss:
            print("ORDER MISSING", c, miss)
    for i, idx in enumerate(W.samples(len(d), NSAMP, SEED), 1):
        name = "wb_so2018_s%d" % i
        oi = o.iloc[idx].reset_index(drop=True)
        desc = ("Stack Overflow Developer Survey 2018 (online, January 2018; professional developers, students and "
                "hobbyists in 180+ countries). Random sample %d of %d (disjoint) of 6,927 out of 98,855 respondents. "
                "GIVEN: codes as a hobby, country, student status, employment status, formal education, years "
                "coding, gender, age band, yearly salary band in USD (employed only). PREDICT: open source, major, "
                "company size, professional coding years, job and career satisfaction (7-point), job-seeking status, "
                "last new job, ranks of 10 job aspects and 11 benefits, contact preferences, CV update reason, "
                "bootcamp outcome, attitudes (agree/disagree), tools, AI and ethics opinions, Stack Overflow use and "
                "recommendation (0-10), interest scales, daily routine, parents' education, survey feedback. Gates "
                "are inferred from answer rates over a short list of candidate parents. Blank cells of eligible "
                "respondents are 'Not answered' (strong drop-out; demographics come last)." % (i, NSAMP))
        frame, schema = W.write(name, oi, given, predict, Q, gates, orders, desc, SEED + i)
        K.validate(name)
        st, ag = W.stats(frame, schema, orders, given)
        out = os.path.join(K.DATASETS, "real_" + name)
        json.dump({"summary": st, "gates": {k: {"parent": gates[k][0], "observed_if": gates[k][1],
                                                "agreement": ag[k]} for k in gates}},
                  open(os.path.join(out, "build_info.json"), "w"), indent=1)
        txt = W.readme(name, "Stack Overflow Developer Survey 2018 (sample %d of %d)" % (i, NSAMP),
                       {"builder": "real_wb_so2018.py",
                        "url": "https://www.kaggle.com/datasets/stackoverflow/stack-overflow-2018-developer-survey (survey_results_public.csv, survey_results_schema.csv); publisher page https://survey.stackoverflow.co/"},
                       "Kaggle lists DbCL-1.0 (Database Contents License); Stack Overflow releases the survey data under the Open Database License (ODbL). Downloaded with the Kaggle CLI, no extra terms.",
                       "Stack Overflow (2018). Stack Overflow Developer Survey 2018. Kaggle dataset stackoverflow/stack-overflow-2018-developer-survey.",
                       ["One row per respondent; %d disjoint random samples of 6,927 rows (seed %d)." % (NSAMP, SEED),
                        "Salary: ConvertedSalary (annual USD, Stack Overflow's conversion) cut into fixed bands, GIVEN, with 'Not asked' for respondents outside the employed statuses.",
                        "Rank items (AssessJob, AssessBenefits, JobContactPriorities) kept as their rank 1..k, in numeric order; DevType and LanguageWorkedWith reduced to banded counts of ticks; a derived tick item `EducationBootcamp` is the parent of TimeAfterBootcamp.",
                        "Gates: for each PREDICT item the item-specific parent (if any) and then Employment, Student, FormalEducation are tried in order; the parent levels whose answer rate is >= 25 % of the best level's form `observed_if`, and the gate is kept when the other (substantive) levels hold >= 0.3 % of rows and answer at most 10 % of the time.",
                        "Gender: Male, Female, or 'Other / several' (multi-select); country capped at 20 + Other; undergrad major capped at 10 + Other."],
                       frame, schema, st, ag,
                       "Similar: employment status and salary band GIVEN, job-seeking status and job-assessment priorities PREDICT, many ordered scales (7-point satisfaction, 5-point agreement and interest, 0-10 recommendation, frequency bands), routing on GIVEN employment / education, strong drop-out. Different: professional developers rather than young job seekers, ranks (each person's ranks form a permutation) rather than banded scale scores, no cognitive tasks, no follow-up wave, salary is actual pay not expected pay, many gates hang off PREDICT items (ad blocker, Stack Overflow account) rather than GIVEN ones.")
        open(os.path.join(out, "README.md"), "w").write(txt)
        print(name, json.dumps(st))


if __name__ == "__main__":
    main()
