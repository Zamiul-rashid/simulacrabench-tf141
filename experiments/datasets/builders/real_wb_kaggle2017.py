"""2017 Kaggle Machine Learning & Data Science Survey -> two World-Bank-like
real test sets (real_wb_kaggle2017_s1, _s2), disjoint random samples of 6,927 of
the 16,716 respondents.

Why it resembles the World Bank file: an online skills/careers survey with heavy
routing by employment situation. Kaggle's own respondent types (worker, coding
worker, learner = student / unemployed job seeker / career switcher, non-worker)
decide which blocks were shown; they are combined into one GIVEN routing column
`SurveyTrack` (the analogue of the WB `group`/`employmentStatus` gate parents).
The learner block holds job-search behaviour (hours per week spent looking for a
job, best job-search resource), 16 ordered "how important is ... when assessing a
job" items and 10 ordered "how important is ... skill for getting a job" items;
the coding-worker block holds job satisfaction, salary change, remote work and
ordered frequency scales; current yearly compensation, converted to USD and cut
into bands, is a GIVEN wage band. The survey had strong drop-out, so many
'Not answered' cells.

Source: https://www.kaggle.com/datasets/kaggle/kaggle-survey-2017
Licence: ODbL-1.0 (Kaggle dataset page).
"""
import json, os, re, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _realkit as K
import _wbkit as W

SEED = 20261113
RAWD = os.path.join(K.RAW, "kaggle_ds2017")

FT, PT = "Employed full-time", "Employed part-time"
IND = "Independent contractor, freelancer, or self-employed"
UNEMP = "Not employed, but looking for work"
TRACKS = ["Employed (full/part-time), writes code to analyse data",
          "Contractor / self-employed, writes code to analyse data",
          "Working, does not write code, switching to data science",
          "Working, does not write code, not switching",
          "Retired",
          "Not employed, looking for work",
          "Not working, learning data science",
          "Not working, not learning data science / prefer not to say"]
GROUPS = {"Worker": TRACKS[:5], "Worker1": TRACKS[:5], "CodingWorker": TRACKS[:2],
          "CodingWorker-NC": TRACKS[:1], "Learners": [TRACKS[2], TRACKS[5], TRACKS[6]]}

AGE_E = [-np.inf, 19, 24, 29, 34, 44, 54, np.inf]
AGE_L = ["<20", "20-24", "25-29", "30-34", "35-44", "45-54", "55+"]
COMP_E = [-np.inf, 0, 9999, 24999, 49999, 74999, 99999, 149999, 199999, np.inf]
COMP_L = ["0", "1-9999", "10000-24999", "25000-49999", "50000-74999", "75000-99999",
          "100000-149999", "150000-199999", "200000+"]
PCT_E = [-np.inf, 0, 10, 25, 50, 75, np.inf]
PCT_L = ["0", "1-10", "11-25", "26-50", "51-75", "76-100"]

EDU = ["I did not complete any formal education past high school",
       "Some college/university study without earning a bachelor's degree", "Bachelor's degree",
       "Master's degree", "Doctoral degree", "Professional degree", "I prefer not to answer"]
PEDU = ["No education", "Primary/elementary school", "High school",
        "Some college/university study, no bachelor's degree", "A bachelor's degree", "A master's degree",
        "A doctoral degree", "A professional degree", "I don't know/not sure", "I prefer not to answer"]
TENURE = ["I don't write code to analyze data", "Less than a year", "1 to 2 years", "3 to 5 years",
          "6 to 10 years", "More than 10 years"]
FREQ = ["Never", "Rarely", "Sometimes", "Most of the time", "Always", "Don't know"]
ORD = {
    "LearningDataScienceTime": ["< 1 year", "1-2 years", "3-5 years", "5-10 years", "10-15 years", "15+ years"],
    "TimeSpentStudying": ["0 - 1 hour", "2 - 10 hours", "11 - 39 hours", "40+"],
    "JobHuntTime": ["0", "1-2", "3-5", "6-10", "11-15", "16-20", "20+"],
    "TitleFit": ["Poorly", "Fine", "Perfectly"],
    "UniversityImportance": ["Not at all important", "Not very important", "Somewhat important", "Important",
                             "Very important", "N/A, I did not receive any formal education"],
    "WorkProductionFrequency": FREQ, "RemoteWork": FREQ,
    "AlgorithmUnderstandingLevel": ["Enough to run the code / standard library",
                                    "Enough to explain the algorithm to someone non-technical",
                                    "Enough to tune the parameters properly",
                                    "Enough to code it again from scratch, albeit it may run slowly",
                                    "Enough to refine and innovate on the algorithm",
                                    "Enough to code it from scratch and it will run blazingly fast and be super efficient"],
    "WorkDataVisualizations": ["Less than 10% of projects", "10-25% of projects", "26-50% of projects",
                               "51-75% of projects", "76-99% of projects", "100% of projects"],
    "WorkInternalVsExternalTools": ["Entirely internal", "More internal than external",
                                    "Approximately half internal and half external", "More external than internal",
                                    "Entirely external", "Do not know"],
    "SalaryChange": ["Has decreased 20% or more", "Has decreased between 6% and 19%",
                     "Has stayed about the same (has not increased or decreased more than 5%)",
                     "Has increased between 6% and 19%", "Has increased 20% or more", "I was not employed 3 years ago",
                     "I am not currently employed", "Other",
                     "I do not want to share information about my salary/compensation"],
    "JobSatisfaction": ["1 - Highly Dissatisfied", "2", "3", "4", "5", "6", "7", "8", "9", "10 - Highly Satisfied",
                        "I prefer not to share"],
    "EmployerSize": ["Fewer than 10 employees", "10 to 19 employees", "20 to 99 employees", "100 to 499 employees",
                     "500 to 999 employees", "1,000 to 4,999 employees", "5,000 to 9,999 employees",
                     "10,000 or more employees", "I don't know", "I prefer not to answer"],
    "EmployerSizeChange": ["Decreased significantly", "Decreased slightly", "Stayed the same", "Increased slightly",
                           "Increased significantly"],
    "EmployerMLTime": ["Less than one year", "1-2 years", "3-5 years", "6-10 years", "More than 10 years", "Don't know"],
    "WorkDatasetSize": ["<1MB", "1MB", "10MB", "100MB", "1GB", "10GB", "100GB", "1TB", "10TB", "100TB+"],
    "DataScienceIdentitySelect": ["No", "Sort of (Explain more)", "Yes"],
    "ParentsEducation": PEDU,
}
SKILL = ["BigData", "Degree", "Stats", "EnterpriseTools", "Python", "R", "SQL", "KaggleRanking", "MOOC",
         "Visualizations"]
FACT = ["Learning", "Salary", "Office", "Languages", "Commute", "Management", "ExperienceLevel", "Department",
        "Title", "CompanyFunding", "Impact", "Remote", "Industry", "LeaderReputation", "Diversity",
        "PublishingOpportunity"]
PLAT = {"Kaggle": "Kaggle", "Courses": "Online courses", "SO": "Stack Overflow Q&A", "YouTube": "YouTube Videos",
        "Projects": "Personal Projects", "Textbook": "Textbook", "Blogs": "Blogs", "College": "College/University"}
CW = ["UniversityImportance", "JobFunctionSelect", "WorkProductionFrequency", "WorkDatasetSize",
      "AlgorithmUnderstandingLevel", "WorkDataVisualizations", "WorkInternalVsExternalTools", "WorkMLTeamSeatSelect",
      "RemoteWork", "SalaryChange", "JobSatisfaction", "TimeGatheringData", "TimeModelBuilding", "TimeProduction",
      "TimeVisualizing", "TimeFindingInsights"]
CWNC = ["EmployerSize", "EmployerSizeChange", "EmployerMLTime", "EmployerSearchMethod"]
LEARN = (["LearningDataScienceTime"] + ["JobSkillImportance" + s for s in SKILL] +
         ["TimeSpentStudying", "ProveKnowledgeSelect", "JobSearchResource", "JobHuntTime"] +
         ["JobFactor" + s for s in FACT])
WORK = ["CurrentJobTitleSelect", "TitleFit", "EmployerIndustry"]
ALL = ["DataScienceIdentitySelect", "LanguageRecommendationSelect", "MLToolNextYearSelect", "MLMethodNextYearSelect",
       "FirstTrainingSelect", "ParentsEducation"] + ["LearningCategory" + s for s in
                                                    ["SelftTaught", "OnlineCourses", "Work", "University", "Kaggle"]]


def track(d):
    emp, code = d.EmploymentStatus, d.CodeWriter
    sw, lds = d.CareerSwitcher, d.LearningDataScience.fillna("")
    t = np.select(
        [emp.isin([FT, PT]) & (code == "Yes"), (emp == IND) & (code == "Yes"),
         emp.isin([FT, PT, IND]) & (sw == "Yes"), emp.isin([FT, PT, IND]),
         emp == "Retired", emp == UNEMP, lds.str.startswith("Yes")],
        TRACKS[:7], TRACKS[7])
    return pd.Series(t, index=d.index)


def main():
    d = pd.read_csv(os.path.join(RAWD, "multipleChoiceResponses.csv"), encoding="latin1", low_memory=False)
    sch = pd.read_csv(os.path.join(RAWD, "schema.csv"), encoding="latin1")
    qtext = dict(zip(sch.Column, sch.Question))
    asked = dict(zip(sch.Column, sch.Asked))
    rates = pd.read_csv(os.path.join(RAWD, "conversionRates.csv"))
    rate = dict(zip(rates.originCountry, rates.exchangeRate))
    o = pd.DataFrame(index=d.index); orders = {}; Q = {}
    # ---- GIVEN
    o["SurveyTrack"] = track(d); orders["SurveyTrack"] = TRACKS
    Q["SurveyTrack"] = ("Survey routing group derived from the screening answers (employment status, writes code "
                        "to analyse data at work, switching careers to data science, learning data science); it "
                        "decides which blocks were shown, as in Kaggle's RespondentTypeREADME.")
    o["Age"] = W.finish(W.band_num(d.Age, AGE_E, AGE_L)); orders["Age"] = AGE_L + [W.NA]
    g = W.clean(d.GenderSelect).replace({"Non-binary, genderqueer, or gender non-conforming": "Non-binary",
                                         "A different identity": "Other"})
    o["GenderSelect"] = W.finish(g)
    o["Country"] = W.finish(K.cap_levels(W.clean(d.Country), 15, keep=(np.nan,)).where(d.Country.notna()))
    o["FormalEducation"] = W.finish(W.clean(d.FormalEducation)); orders["FormalEducation"] = EDU + [W.NA]
    o["EmploymentStatus"] = W.finish(W.clean(d.EmploymentStatus))
    o["Tenure"] = W.finish(W.clean(d.Tenure)); orders["Tenure"] = TENURE + [W.NA]
    o["MajorSelect"] = W.finish(W.clean(d.MajorSelect))
    amt = pd.to_numeric(d.CompensationAmount.astype(str).str.replace(r"[,\s]", "", regex=True), errors="coerce")
    usd = amt * d.CompensationCurrency.map(rate)
    usd = usd.where(usd < 2_000_000)
    comp = W.band_num(usd, COMP_E, COMP_L)
    cw = o.SurveyTrack.isin(GROUPS["CodingWorker"])
    o["CompensationUSD"] = np.where(cw, comp.fillna(W.NA), comp.fillna(W.NOT_ASKED))
    orders["CompensationUSD"] = COMP_L + [W.NOT_ASKED, W.NA]
    Q["CompensationUSD"] = ("What is your current total yearly compensation (salary + bonus)? Converted to USD with "
                            "the survey's exchange rates and banded; asked of coding workers only, others 'Not asked'.")
    given = ["SurveyTrack", "Age", "GenderSelect", "Country", "FormalEducation", "EmploymentStatus", "Tenure",
             "MajorSelect", "CompensationUSD"]
    for c in given:
        Q.setdefault(c, qtext.get(c, c))
    # ---- PREDICT
    predict, gates = [], {}

    def put(name, raw, parent=None, S=None, order=None, cap=None, question=None):
        raw = W.clean(raw) if raw.dtype == object else raw
        if cap:
            raw = K.cap_levels(raw, cap, keep=(np.nan,)).where(raw.notna())
        if parent is None:
            o[name] = W.finish(raw)
        else:
            o[name] = W.rule_gate(raw, o[parent].isin(S))
            gates[name] = (parent, list(S))
        if order:
            orders[name] = order + ([W.NA] if W.NA not in order else [])
        Q[name] = question or qtext.get(name, name)
        predict.append(name)

    for c in ALL:
        if c.startswith("LearningCategory"):
            put(c, W.band_num(d[c], PCT_E, PCT_L), order=PCT_L)
        else:
            put(c, d[c], order=ORD.get(c), cap=20 if c.startswith("ML") else None)
    plat = d.LearningPlatformSelect.fillna("")
    for k, lab in PLAT.items():
        sel = W.tick(plat.str.contains(re.escape(lab)), plat != "", d.index)
        put("LearningPlatform" + k, sel, order=["No", "Yes"],
            question="What platforms & resources have you used to continue learning data science skills? (select all) - %s" % lab)
        put("LearningPlatformUsefulness" + k, d["LearningPlatformUsefulness" + k], parent="LearningPlatform" + k,
            S=["Yes"], order=["Not Useful", "Somewhat useful", "Very useful"])
    for c in WORK:
        put(c, d[c], "SurveyTrack", GROUPS["Worker"], ORD.get(c))
    for c in LEARN:
        o_ = ORD.get(c)
        if c.startswith("JobSkillImportance"):
            o_ = ["Unnecessary", "Nice to have", "Necessary"]
        if c.startswith("JobFactor"):
            o_ = ["Not important", "Somewhat important", "Very Important"]
        put(c, d[c], "SurveyTrack", GROUPS["Learners"], o_)
    for c in CW:
        raw = d[c]
        o_ = ORD.get(c)
        if c.startswith("Time"):
            raw = W.band_num(raw, PCT_E, PCT_L); o_ = PCT_L
        if c == "WorkDatasetSize":
            raw = W.clean(raw).replace({"100PB": "100TB+", "1PB": "100TB+", "10PB": "100TB+", "1EB": "100TB+",
                                        ">1EB": "100TB+", "100TB": "100TB+"})
        put(c, raw, "SurveyTrack", GROUPS["CodingWorker"], o_)
    for c in CWNC:
        put(c, d[c], "SurveyTrack", GROUPS["CodingWorker-NC"], ORD.get(c))
    # warn about order lists that miss observed levels
    for k, lst in orders.items():
        miss = set(o[k].unique()) - set(lst) - {W.GATED, W.NA, W.NOT_ASKED}
        if miss:
            print("ORDER MISSING", k, miss)
    for i, idx in enumerate(W.samples(len(d), 2, SEED), 1):
        name = "wb_kaggle2017_s%d" % i
        oi = o.iloc[idx].reset_index(drop=True)
        desc = ("2017 Kaggle Machine Learning & Data Science Survey (online, August 2017; data science workers, "
                "students and job seekers in about 50 countries). Random sample %d of 2 (disjoint) of 6,927 out of "
                "16,716 respondents. GIVEN: survey routing track (employment x writes code x learner, decides which "
                "blocks were shown), age band, gender, country, formal education, employment status, coding tenure, "
                "undergraduate major, yearly compensation band in USD (coding workers only). PREDICT: learner block "
                "(job-hunt hours per week, best job-search resource, 16 job-factor and 10 job-skill importance "
                "ratings, study time), worker and coding-worker blocks (job title with 16 options, industry, job "
                "satisfaction 1-10, salary change, remote work, frequency scales, employer size), learning platforms "
                "and their usefulness (gated on the platform being ticked). Blank cells of eligible respondents are "
                "'Not answered' (strong drop-out)." % i)
        frame, schema = W.write(name, oi, given, predict, Q, gates, orders, desc, SEED + i)
        K.validate(name)
        st, ag = W.stats(frame, schema, orders, given)
        out = os.path.join(K.DATASETS, "real_" + name)
        json.dump({"summary": st, "gates": {k: {"parent": gates[k][0], "observed_if": gates[k][1],
                                                "agreement": ag[k]} for k in gates}},
                  open(os.path.join(out, "build_info.json"), "w"), indent=1)
        txt = W.readme(name, "2017 Kaggle ML & Data Science Survey (sample %d of 2)" % i,
                       {"builder": "real_wb_kaggle2017.py",
                        "url": "https://www.kaggle.com/datasets/kaggle/kaggle-survey-2017 (multipleChoiceResponses.csv, schema.csv, conversionRates.csv)"},
                       "ODbL-1.0 (as listed on the Kaggle dataset page). Downloaded with the Kaggle CLI, no extra terms.",
                       "Kaggle (2017). 2017 Kaggle Machine Learning & Data Science Survey. Kaggle dataset kaggle/kaggle-survey-2017.",
                       ["One row per respondent; disjoint random samples of 6,927 rows (seed %d), `_s1` and `_s2`." % SEED,
                        "`SurveyTrack` (GIVEN) is derived from the screening answers EmploymentStatus, CodeWriter, CareerSwitcher and LearningDataScience, following Kaggle's RespondentTypeREADME (Worker, CodingWorker, CodingWorker-NC, Learners). Those screening items are not PREDICT items.",
                        "Gates are the questionnaire's own routing (schema.csv column `Asked`) expressed on `SurveyTrack`; the eight learning-platform usefulness items hang off a derived PREDICT tick item (chained gate, like the WB tracer items gated on tr_job_full).",
                        "Compensation: amount x the survey's exchange rate to USD, values >= 2,000,000 USD treated as not answered, cut into fixed bands; non-coding-workers get 'Not asked'.",
                        "Percent-of-time / percent-of-training items cut into 0, 1-10, 11-25, 26-50, 51-75, 76-100; age in bands; ML tool / method items capped at 20 levels + Other."],
                       frame, schema, st, ag,
                       "Similar: careers/skills survey with routing almost entirely on a GIVEN employment-type column (job-seeker block, worker block, coding-worker block), job-hunt hours per week in bands, many three-level importance scales (like the WB banded scale scores), a 16-option job-title item (WB: 25-option sector), a GIVEN wage band, strong drop-out. Different: international professional/student population (US, India dominate), compensation is actual pay not expected pay, no cognitive task scores, no follow-up wave; the routing column is derived and partly redundant with EmploymentStatus.")
        open(os.path.join(out, "README.md"), "w").write(txt)
        print(name, json.dumps(st))


if __name__ == "__main__":
    main()
