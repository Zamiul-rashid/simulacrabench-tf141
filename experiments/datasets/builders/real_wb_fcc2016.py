"""freeCodeCamp + CodeNewbie 2016 New Coder Survey -> two World-Bank-like real
test sets (real_wb_fcc2016_s1, real_wb_fcc2016_s2), disjoint random samples of
6,927 of the 15,620 respondents.

Why it resembles the World Bank file: people learning to code, most of them
job seekers. Current income band and employment status are GIVEN (WB: wage
bands, employment status); job-search intentions (when they will apply, which
role, where, expected salary band) are routed on whether the respondent already
works as a developer; the bootcamp block is a small sub-sample (6 %) gated on a
GIVEN column, like the WB tracer follow-up gated on the arm; learning hours and
money are banded like the WB hours items; Part 2 (demographics) drop-out gives
genuine 'Not answered' cells, including in GIVEN columns.

Source: https://www.kaggle.com/datasets/freecodecamp/2016-new-coder-survey-
Licence: ODbL-1.0 (Kaggle dataset page).
"""
import json, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _realkit as K
import _wbkit as W

SEED = 20261112
RAW = os.path.join(K.RAW, "fcc2016", "2016-FCC-New-Coders-Survey-Data.csv")
YN = {0.0: "No", 1.0: "Yes"}
MONEY_E = [-np.inf, 0, 9999, 19999, 29999, 39999, 49999, 69999, 99999, np.inf]
MONEY_L = ["0", "1-9999", "10000-19999", "20000-29999", "30000-39999", "40000-49999",
           "50000-69999", "70000-99999", "100000+"]
HOURS_E = [-np.inf, 0, 1, 2, 3, 4, 5, 10, 15, 20, 30, 40, np.inf]
HOURS_L = ["0", "1", "2", "3", "4", "5", "6-10", "11-15", "16-20", "21-30", "31-40", "more than 40"]
MONTHS_E = [-np.inf, 0, 1, 3, 6, 12, 24, 60, np.inf]
MONTHS_L = ["Less than one month", "About one month", "2-3 months", "4-6 months", "7-12 months",
            "1-2 years", "2-5 years", "More than 5 years"]
SPEND_E = [-np.inf, 0, 99, 499, 999, 4999, np.inf]
SPEND_L = ["0", "1-99", "100-499", "500-999", "1000-4999", "5000+"]
COMMUTE_E = [-np.inf, 0, 15, 30, 45, 60, 90, np.inf]
COMMUTE_L = ["0", "1-15", "16-30", "31-45", "46-60", "61-90", "more than 90"]
DEBT_E = [-np.inf, 4999, 9999, 19999, 39999, 79999, 149999, 299999, np.inf]
DEBT_L = ["<5000", "5000-9999", "10000-19999", "20000-39999", "40000-79999", "80000-149999",
          "150000-299999", "300000+"]
AGE_E = [-np.inf, 19, 24, 29, 34, 44, np.inf]
AGE_L = ["15-19", "20-24", "25-29", "30-34", "35-44", "45+"]

EDU = ["no high school (secondary school)", "some high school", "high school diploma or equivalent (GED)",
       "trade, technical, or vocational training", "some college credit, no degree", "associate's degree",
       "bachelor's degree", "master's degree (non-professional)", "professional degree (MBA, MD, JD, etc.)",
       "Ph.D."]
APPLY = ["I'm already applying", "Within the next 6 months", "Within 7 to 12 months",
         "more than 12 months from now", "I haven't decided"]
CITY = ["less than 100,000", "between 100,000 and 1 million", "more than 1 million"]

Q = {"Age": "What is your age? (banded)",
     "Gender": "What is your gender?",
     "CountryLive": "Which country do you currently live in?",
     "SchoolDegree": "What is the highest degree or level of school you have completed?",
     "EmploymentStatus": "Regarding employment status, are you currently...",
     "IsSoftwareDev": "Are you already working as a software developer?",
     "Income": "About how much money did you make last year (in US dollars)? (banded; asked of the employed)",
     "AttendedBootcamp": "Have you attended a full-time coding bootcamp?",
     "CityPopulation": "About how many people live in your city?",
     "JobApplyWhen": "When do you plan to start applying for developer jobs?",
     "JobRoleInterest": "Which one of these roles are you most interested in?",
     "JobPref": "Would you prefer to... (work for a startup / medium company / multinational / freelance / own business)",
     "JobWherePref": "Would you prefer to work from home, in an office with other developers, or no preference?",
     "JobRelocateYesNo": "Are you willing to relocate for a job?",
     "ExpectedEarning": "About how much money do you expect to earn per year at your first developer job (in US dollars)? (banded)",
     "EmploymentField": "Which field do you work in?",
     "IsUnderEmployed": "Do you consider yourself under-employed?",
     "CommuteTime": "About how many minutes does it take you to get to work each day? (banded)",
     "HoursLearning": "About how many hours do you spend learning each week? (banded)",
     "MonthsProgramming": "About how many months have you been programming? (banded)",
     "MoneyForLearning": "Aside from university tuition, about how much money have you spent on learning to code so far (in US dollars)? (banded)",
     "BootcampFinish": "Have you finished the bootcamp?",
     "BootcampFullJobAfter": "Did you get a full-time job as a developer after the bootcamp?",
     "BootcampLoanYesNo": "Did you take out a loan to pay for the bootcamp?",
     "BootcampMonthsAgo": "How many months ago did you finish the bootcamp? (banded)",
     "BootcampName": "Which one of these bootcamps did you attend?",
     "BootcampPostSalary": "How much do you make per year at your first developer job after the bootcamp? (banded)",
     "BootcampRecommend": "Would you recommend the bootcamp you attended to a friend?",
     "HasFinancialDependents": "Do you have children or other people who are financially dependent on you?",
     "HasChildren": "Do you have children?",
     "ChildrenNumber": "How many children do you have?",
     "FinanciallySupporting": "Do you financially support any elderly relatives or relatives with disabilities?",
     "HasDebt": "Do you have any debt?",
     "HasStudentDebt": "Do you have student loan debt?",
     "StudentDebtOwe": "About how much do you owe in student loans (in US dollars)? (banded)",
     "HasHomeMortgage": "Do you have a home mortgage?",
     "HomeMortgageOwe": "About how much do you owe on your home mortgage (in US dollars)? (banded)",
     "HasHighSpdInternet": "Do you have high speed internet at your home?",
     "HasServedInMilitary": "Have you served in your country's military?",
     "IsEthnicMinority": "Are you an ethnic minority in your country?",
     "IsReceiveDiabilitiesBenefits": "Do you receive disability benefits from your government?",
     "LanguageAtHome": "Which language do you speak at home with your family?",
     "MaritalStatus": "What is your marital status?",
     "SchoolMajor": "What was the main field of study (major) of your highest degree?",
     "CountryCitizen": "Which country are you a citizen of?"}

RES = ["ResourceCodecademy", "ResourceFCC", "ResourceCoursera", "ResourceUdemy", "ResourceKhanAcademy",
       "ResourceEdX", "ResourcePluralSight", "ResourceUdacity", "ResourceOdinProj", "ResourceCodeWars",
       "ResourceDevTips", "ResourceTreehouse"]
EVT = ["CodeEventNone", "CodeEventConferences", "CodeEventHackathons", "CodeEventCoffee",
       "CodeEventStartUpWknd", "CodeEventWomenCode", "CodeEventGirlDev", "CodeEventNodeSchool"]
POD = ["PodcastNone", "PodcastCodeNewbie", "PodcastJSJabber", "PodcastSEDaily", "PodcastOther",
       "PodcastChangeLog"]


def multi(d, cols, block):
    """Select-all blocks: Yes / No when the respondent ticked anything in the
    block (or its free-text 'other'), otherwise Not answered."""
    any_ = d[block].notna().any(axis=1)
    out = {}
    for c in cols:
        v = np.where(d[c].notna(), "Yes", np.where(any_, "No", W.NA))
        out[c] = pd.Series(v, index=d.index, dtype=object)
    return out


def build(d):
    o = pd.DataFrame(index=d.index)
    orders = {}
    yn = lambda c: d[c].map(YN)
    # GIVEN
    o["Age"] = W.finish(W.band_num(d.Age, AGE_E, AGE_L)); orders["Age"] = AGE_L + [W.NA]
    g = W.clean(d.Gender).map({"male": "Male", "female": "Female"}).where(lambda s: s.notna() | d.Gender.isna(), "Other")
    o["Gender"] = W.finish(g)
    o["CountryLive"] = W.finish(K.cap_levels(W.clean(d.CountryLive), 15, keep=(np.nan,)).where(d.CountryLive.notna()))
    o["SchoolDegree"] = W.finish(W.clean(d.SchoolDegree)); orders["SchoolDegree"] = EDU + [W.NA]
    o["EmploymentStatus"] = W.finish(W.clean(d.EmploymentStatus))
    o["IsSoftwareDev"] = W.finish(yn("IsSoftwareDev")); orders["IsSoftwareDev"] = ["No", "Yes", W.NA]
    emp_S = ["Employed for wages", "Self-employed business owner", "Self-employed freelancer"]
    inc = W.band_num(d.Income, MONEY_E, MONEY_L)
    o["Income"] = np.where(o.EmploymentStatus.isin(emp_S), inc.fillna(W.NA), np.where(inc.notna(), inc, W.NOT_ASKED))
    orders["Income"] = MONEY_L + [W.NOT_ASKED, W.NA]
    o["AttendedBootcamp"] = W.finish(yn("AttendedBootcamp")); orders["AttendedBootcamp"] = ["No", "Yes", W.NA]
    o["CityPopulation"] = W.finish(W.clean(d.CityPopulation)); orders["CityPopulation"] = CITY + [W.NA]
    given = ["AttendedBootcamp", "Age", "Gender", "CountryLive", "SchoolDegree", "IsSoftwareDev",
             "EmploymentStatus", "Income", "CityPopulation"]
    # PREDICT: raw answers (NaN = blank), then gates
    raw, gate_cands = {}, {}
    def add(name, s, cands, order=None):
        raw[name] = s; gate_cands[name] = cands
        if order is not None:
            orders[name] = order
    jobseek = ["IsSoftwareDev"]
    add("HoursLearning", W.band_num(d.HoursLearning, HOURS_E, HOURS_L), [], HOURS_L)
    add("MonthsProgramming", W.band_num(d.MonthsProgramming, MONTHS_E, MONTHS_L), [], MONTHS_L)
    add("MoneyForLearning", W.band_num(d.MoneyForLearning, SPEND_E, SPEND_L), [], SPEND_L)
    add("JobApplyWhen", W.clean(d.JobApplyWhen), jobseek, APPLY)
    add("JobRoleInterest", W.clean(d.JobRoleInterest), jobseek)
    add("JobPref", W.clean(d.JobPref), jobseek)
    add("JobWherePref", W.clean(d.JobWherePref), jobseek)
    add("JobRelocateYesNo", yn("JobRelocateYesNo"), jobseek)
    add("ExpectedEarning", W.band_num(d.ExpectedEarning, MONEY_E, MONEY_L), jobseek, MONEY_L)
    add("EmploymentField", W.clean(d.EmploymentField).replace({"software development": "software development and IT"}),
        ["EmploymentStatus"])
    add("IsUnderEmployed", yn("IsUnderEmployed"), ["EmploymentStatus"])
    add("CommuteTime", W.band_num(d.CommuteTime, COMMUTE_E, COMMUTE_L), ["EmploymentStatus"], COMMUTE_L)
    bc = ["AttendedBootcamp"]
    add("BootcampFinish", yn("BootcampFinish"), bc)
    add("BootcampLoanYesNo", yn("BootcampLoanYesNo"), bc)
    add("BootcampRecommend", yn("BootcampRecommend"), bc)
    add("BootcampName", K.cap_levels(W.clean(d.BootcampName), 12, keep=(np.nan,)).where(d.BootcampName.notna()), bc)
    add("BootcampFullJobAfter", yn("BootcampFullJobAfter"), ["BootcampFinish", "AttendedBootcamp"])
    add("BootcampMonthsAgo", W.band_num(d.BootcampMonthsAgo, MONTHS_E, MONTHS_L),
        ["BootcampFinish", "AttendedBootcamp"], MONTHS_L)
    add("BootcampPostSalary", W.band_num(d.BootcampPostSalary, MONEY_E, MONEY_L),
        ["BootcampFullJobAfter", "BootcampFinish", "AttendedBootcamp"], MONEY_L)
    add("MaritalStatus", W.clean(d.MaritalStatus), [])
    add("HasFinancialDependents", yn("HasFinancialDependents"), [])
    add("HasChildren", yn("HasChildren"), ["HasFinancialDependents"])
    add("ChildrenNumber", W.band_num(d.ChildrenNumber, [0, 1, 2, 3, np.inf], ["1", "2", "3", "4+"]),
        ["HasChildren", "HasFinancialDependents"], ["1", "2", "3", "4+"])
    add("FinanciallySupporting", yn("FinanciallySupporting"), ["HasFinancialDependents"])
    add("HasDebt", yn("HasDebt"), [])
    add("HasStudentDebt", yn("HasStudentDebt"), ["HasDebt"])
    add("StudentDebtOwe", W.band_num(d.StudentDebtOwe, DEBT_E, DEBT_L), ["HasStudentDebt", "HasDebt"], DEBT_L)
    add("HasHomeMortgage", yn("HasHomeMortgage"), ["HasDebt"])
    add("HomeMortgageOwe", W.band_num(d.HomeMortgageOwe, DEBT_E, DEBT_L), ["HasHomeMortgage", "HasDebt"], DEBT_L)
    for c in ["HasHighSpdInternet", "HasServedInMilitary", "IsEthnicMinority", "IsReceiveDiabilitiesBenefits"]:
        add(c, yn(c), [])
    add("LanguageAtHome", K.cap_levels(W.clean(d.LanguageAtHome), 12, keep=(np.nan,)).where(d.LanguageAtHome.notna()), [])
    add("CountryCitizen", K.cap_levels(W.clean(d.CountryCitizen), 15, keep=(np.nan,)).where(d.CountryCitizen.notna()), [])
    maj = W.clean(d.SchoolMajor).str.title()
    add("SchoolMajor", K.cap_levels(maj, 20, keep=(np.nan,)).where(maj.notna()), ["SchoolDegree"])
    mres = multi(d, RES, [c for c in d.columns if c.startswith("Resource")])
    mevt = multi(d, EVT, [c for c in d.columns if c.startswith("CodeEvent")])
    mpod = multi(d, POD, [c for c in d.columns if c.startswith("Podcast")])
    for c in RES:
        Q[c] = "Which learning resources have you found helpful? (select all) - %s" % c[8:]
    for c in EVT:
        Q[c] = "Which in-person coding events have you attended? (select all) - %s" % c[9:]
    for c in POD:
        Q[c] = "Which coding podcasts do you listen to? (select all) - %s" % c[7:]
    multi_items = {**mres, **mevt, **mpod}
    # gates: first candidate parent (already final) whose answer rates show routing
    gates, predict = {}, []
    for name, s in raw.items():
        chosen = None
        for p in gate_cands[name]:
            par = o[p]
            r = W.rate_gate(s, par)
            if r is not None:
                chosen = (p, r[0]); break
        if chosen:
            asked = o[chosen[0]].isin(chosen[1])
            o[name] = W.rule_gate(s, asked)
            gates[name] = chosen
        else:
            if gate_cands[name]:
                print("no gate accepted for", name, gate_cands[name])
            o[name] = W.finish(s)
        predict.append(name)
    for c, s in multi_items.items():
        o[c] = s; predict.append(c); orders[c] = ["No", "Yes", W.NA]
    for c in predict:
        if c not in orders and set(o[c].unique()) <= {"No", "Yes", W.NA, W.GATED}:
            orders[c] = ["No", "Yes", W.NA]
    return o, given, predict, gates, orders


def main():
    d = pd.read_csv(RAW, low_memory=False)
    o_all, given, predict, gates, orders = build(d)
    for i, idx in enumerate(W.samples(len(d), 2, SEED), 1):
        name = "wb_fcc2016_s%d" % i
        o = o_all.iloc[idx].reset_index(drop=True)
        desc = ("freeCodeCamp / CodeNewbie 2016 New Coder Survey (online, March-May 2016): people learning to "
                "code, mostly job seekers. Random sample %d of 2 (disjoint) of 6,927 out of 15,620 respondents. "
                "GIVEN: bootcamp attendance (gates the small bootcamp sub-sample), age band, gender, country, "
                "education, whether already a developer, employment status, last-year income band (USD, asked "
                "of the employed), city size. PREDICT: job-search plans and expected salary (routed on being a "
                "developer), job field (routed on employment), learning effort, bootcamp follow-up, household and "
                "debt items, select-all resource/event/podcast ticks. Money in US dollars per year. Blank cells of "
                "eligible respondents are 'Not answered' (Part 2 drop-out is ~13 %%)." % i)
        frame, schema = W.write(name, o, given, predict, Q, gates, orders, desc, SEED + i)
        K.validate(name)
        st, ag = W.stats(frame, schema, orders, given)
        info = {"summary": st, "gates": {k: {"parent": gates[k][0], "observed_if": gates[k][1], "agreement": ag[k]}
                                         for k in gates}}
        out = os.path.join(K.DATASETS, "real_" + name)
        json.dump(info, open(os.path.join(out, "build_info.json"), "w"), indent=1)
        txt = W.readme(name, "freeCodeCamp 2016 New Coder Survey (sample %d of 2)" % i,
                       {"builder": "real_wb_fcc2016.py", "url": "https://www.kaggle.com/datasets/freecodecamp/2016-new-coder-survey- (file 2016-FCC-New-Coders-Survey-Data.csv); original repository https://github.com/freeCodeCamp/2016-new-coder-survey"},
                       "ODbL-1.0 (as listed on the Kaggle dataset page). Downloaded with the Kaggle CLI, no extra terms.",
                       "freeCodeCamp and CodeNewbie (2016). 2016 New Coder Survey. Kaggle dataset freecodecamp/2016-new-coder-survey-.",
                       ["One row per respondent; disjoint random samples of 6,927 rows (seed %d), `_s1` and `_s2`." % SEED,
                        "Money (income, expected salary, bootcamp salary, debts) cut into fixed USD bands; hours learning in the World Bank hour bands; months programming / months since bootcamp in WB-like duration bands.",
                        "Gates: for every routed item a short list of candidate parents (questionnaire logic) is tried in order and the parent levels with an answer rate >= 25 % of the best level form `observed_if`; the gate is kept when the other levels answer at most 10 % of the time.",
                        "Select-all ticks (resources, events, podcasts): 'Yes' if ticked, 'No' if anything else in the block was ticked, otherwise 'Not answered'.",
                        "Income is GIVEN with an extra level 'Not asked' for respondents outside the employed statuses."],
                       frame, schema, st, ag,
                       "Similar: job-seeker population (72 % are not yet developers), employment status and an income band GIVEN, expected-salary band and job-search plans PREDICT with gates on GIVEN columns, a ~6 % follow-up-like bootcamp block gated on a GIVEN column with a chained sub-gate, many banded/ordered items, real drop-out. Different: US-centred (about 50 % in the USA), USD amounts, no psychometric or cognitive-task scores, many binary select-all items instead of Likert scales, no randomised arm.")
        open(os.path.join(out, "README.md"), "w").write(txt)
        print(name, json.dumps(st))


if __name__ == "__main__":
    main()
