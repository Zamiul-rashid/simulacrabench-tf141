"""Shared generator for fabricated datasets on the REAL UNHCR schema.

Every builder (unhcr_noisygates.py, unhcr_repeats.py, ...) calls build() with a
config dict. The schema (items, options, gates, split counts) is the real one,
unchanged; only the answers are invented.

Generative story (the same "world" for every dataset unless a config says
otherwise, so datasets differ only in what they plant):

  1. GIVEN columns. Households: country (4), governorate nested in country (46,
     Zipf shares), origin governorate (country-specific shares), household
     composition counts from a size factor and a female-headed flag.
     Respondents: relationship, age, education, marital status, single parent,
     conditional on the household.
  2. Answer latents, drawn from P(latent | GIVEN) only (so the Bayes ceiling
     given GIVEN can be computed by Monte Carlo): six correlated household
     traits (wealth, return orientation, origin ties, integration,
     connectedness, hardship) whose means depend on country, governorate,
     origin and household/respondent features; respondent gender (not a GIVEN
     column, implied by relationship) and a response-style trait; one block
     factor per multi-select block.
  3. Potential answers for every PREDICT item ("what they would say if asked"):
     nominal (softmax), ordinal (ordered logit plus non-substantive 97/98/99
     codes), binary multi-select members (logit with a shared block factor;
     exclusive 'none / don't know / PNA' options zero the rest of the block).
     Each item: base marginal (skewed), trait loadings, country / governorate /
     origin / wave effects, direct effects of GIVEN features, a few hand-coded
     dependencies (anyone working <- adult men, main earner <- relationship).
  4. Re-interviews (optional): the item-wise copy of a source row's potential
     answers with item-class-specific stability, else a fresh draw.
  5. Routing: observed = potential answer if asked, else NA_GATED. Exact gates,
     or "actual routes" that differ from the declared gate (other parent,
     extra open values, country-specific drops, random leak/drop).
"""
import json
import os
import re

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SCHEMA_PATH = os.path.join(ROOT, "starter-kit", "data", "unhcr.json")
OUT_ROOT = os.path.join(ROOT, "experiments", "datasets")
NA = "NA_GATED"
WORLD_SEED = 2026
FLOOR = 1e-3

GOVS = {  # country -> governorates, largest first
    "Jordan": ["Amman", "Irbid", "Al Mafraq", "Zarqa", "Al Balqa", "Madaba", "Al Karak", "Jarash",
               "Ajloun", "Maan", "Al Aqaba", "Al Tafilah"],
    "Lebanon": ["Bekaa", "North", "Mount Lebanon", "Akkar", "Beirut", "South Lebanon",
                "Hermel/Baalbek", "El Nabatieh"],
    "Iraq": ["Duhok", "Erbil", "Al-Sulaymaniyah", "Kirkuk", "Al-Najaf"],
    "Egypt": ["Giza", "Cairo", "Alexandria", "Kalyoubia", "Sharkia", "Damietta", "Dakahlia",
              "Menoufia", "Gharbia", "Behera", "Ismailia", "Port Said", "Beni Suef", "Fayoum",
              "Menia", "Assiut", "Kafr El-Shikh", "Luxor", "Aswan", "Matrouh", "Red Sea"],
}
COUNTRY_SHARE = {"Egypt": 0.17, "Iraq": 0.21, "Jordan": 0.30, "Lebanon": 0.32}
ORIGIN_SHARE = {
    "Egypt": {"Damascus": .25, "Rural Damascus": .28, "Homs": .14, "Aleppo": .10, "Dar'a": .06,
              "Hama": .05, "Idleb": .03, "Lattakia": .02},
    "Iraq": {"Al-Hasakeh": .62, "Aleppo": .10, "Deir-ez-Zor": .08, "Damascus": .07,
             "Ar-Raqqa": .05, "Rural Damascus": .03, "Homs": .02},
    "Jordan": {"Dar'a": .42, "Homs": .16, "Rural Damascus": .14, "Damascus": .10, "Aleppo": .05,
               "Hama": .05, "Idleb": .02, "Quneitra": .02},
    "Lebanon": {"Homs": .22, "Aleppo": .18, "Idleb": .14, "Hama": .12, "Rural Damascus": .10,
                "Ar-Raqqa": .06, "Damascus": .05, "Deir-ez-Zor": .04, "Tartous": .02,
                "Lattakia": .02},
}
ORIGIN_RARE = {"Don’t want to answer": .008, "[generalised:s2]": .004, "As-Sweida": .004}

GIVEN = ["wave", "s1_2_country_asylum_lbl", "s2_1_hh_relationship_lbl", "s2_1b_age",
         "s2_1c_education_level_lbl", "s2_1d_marital_status_lbl", "s2_2_single_parent_lbl",
         "s2_3_boys_0_5", "s2_3_girls_0_5", "s2_3_boys_6_17", "s2_3_girls_6_17",
         "s2_3_men_18_59", "s2_3_women_18_59", "s2_3_men_60plus", "s2_3_women_60plus",
         "governorate_col", "s2_4a_origin_governorate_lbl"]
HH_COLS = ["s1_2_country_asylum_lbl", "s2_3_boys_0_5", "s2_3_girls_0_5", "s2_3_boys_6_17",
           "s2_3_girls_6_17", "s2_3_men_18_59", "s2_3_women_18_59", "s2_3_men_60plus",
           "s2_3_women_60plus", "governorate_col", "s2_4a_origin_governorate_lbl"]
RESP_COLS = ["s2_1_hh_relationship_lbl", "s2_1b_age", "s2_1c_education_level_lbl",
             "s2_1d_marital_status_lbl", "s2_2_single_parent_lbl"]
COUNT_COLS = HH_COLS[1:9]
GI = {g: i for i, g in enumerate(GIVEN)}

TRAITS = ["wealth", "return", "ties", "integr", "connect", "hardship"]
TRAIT_CORR = np.array([
    [1.0, 0.1, 0.3, 0.3, 0.1, -0.5],
    [0.1, 1.0, 0.4, -0.3, 0.4, 0.1],
    [0.3, 0.4, 1.0, 0.0, 0.3, -0.1],
    [0.3, -0.3, 0.0, 1.0, 0.0, -0.3],
    [0.1, 0.4, 0.3, 0.0, 1.0, 0.0],
    [-0.5, 0.1, -0.1, -0.3, 0.0, 1.0]])

ORDINAL_PREFIX = ("s3_7_", "s3_9a_", "s3_9b_", "s3_18_", "s3_10c_", "s4_4_", "s3_4a_", "s3_8a_",
                  "s3_14_", "s3_19_", "s3_20_", "s3_21_", "s3_22_", "s3_24_", "s3_25_", "s5_",
                  "s6_3_", "s6_7_", "s6_8_")
SECTION_TRAITS = [  # (name prefix, [(trait, sign)]) first match wins
    ("s2_6_", []), ("s2_", [("ties", 1)]), ("s3_1_", [("wealth", 1), ("ties", 1)]),
    ("s3_2_", [("return", 1), ("connect", 1)]), ("s3_3_", [("connect", 1)]),
    ("s3_4", [("return", 1), ("connect", 1)]), ("s3_5_", [("connect", 1)]),
    ("s3_6_", [("connect", 1), ("return", 1)]), ("s3_7_", [("connect", 1)]),
    ("s3_8", [("return", 1)]), ("s3_9", [("connect", 1)]), ("s3_10", [("wealth", 1)]),
    ("s3_11_", [("return", 1), ("ties", 1)]), ("s3_12_", [("return", 1)]),
    ("s3_13_", [("return", 1)]), ("s7a_", [("return", 1), ("wealth", 1)]),
    ("s7b_", [("hardship", 1), ("ties", -1)]), ("s7c_", [("return", 1)]),
    ("s3_14_", [("return", -1), ("connect", -1)]), ("s3_15_", [("connect", 1), ("return", 1)]),
    ("s3_16_", [("connect", 1)]), ("s3_17_", [("connect", 1)]), ("s3_18_", [("connect", 1)]),
    ("s3_19_", [("connect", -1)]), ("s3_2", [("connect", 1), ("return", 1)]),
    ("s4_", [("wealth", 1)]), ("s5_", [("integr", -1)]), ("s6_1_", [("wealth", 1)]),
    ("s6_2_", [("wealth", 1)]), ("s6_3_", [("wealth", -1), ("hardship", 1)]),
    ("s6_4_", [("hardship", 1)]), ("s6_5_", [("hardship", 1), ("wealth", -1)]),
    ("s6_6_", [("hardship", 1)]), ("s6_7_", [("connect", -1)]), ("s6_8_", [("wealth", -1)]),
    ("s6_9", [("hardship", 1)]), ("s6_10_", [("hardship", 1), ("integr", -1)]),
    ("s6_11_", [("hardship", 1)]), ("s6_12_", [("wealth", 1)]),
]
# Base marginals for gate parents and a few others: {item: {value prefix: prob}}
BASE = {
    "s2_7_own_house_syria_lbl": {"0.": .40, "1.": .55, "98": .05},
    "s2_8_own_land_syria_lbl": {"0.": .60, "1.": .35, "98": .05},
    "s2_10_house_condition_lbl": {"1.": .25, "2.": .20, "3.": .30, "4.": .20, "98": .05},
    "s3_2_visited_syria_lbl": {"1.": .25, "2.": .72, "98": .02, "99": .01},
    "s3_5_family_in_syria_lbl": {"1.": .80, "2.": .17, "98": .025, "Not": .005},
    "s3_6_permanent_returns_lbl": {"0.": .80, "1.": .17, "98": .02, "99": .01},
    "s3_9c_returnee_working_lbl": {"1.": .35, "2.": .50, "98": .15},
    "s3_11_intent_return_12m_lbl": {"0.": .42, "1.": .28, "98": .30},
    "s7a_1_return_destination_lbl": {"1.": .85, "2.": .08, "98": .07},
    "s7a_4_return_alone_lbl": {"0.": .85, "1.": .15},
    "s3_12_hope_return_someday_lbl": {"0.": .30, "1.": .55, "98": .15},
    "s3_15_friend_return_likely_lbl": {"1.": .30, "2.": .45, "3.": .10, "98": .15},
    "s3_23_safety_no_concerns_lbl": {"0": .85, "1": .15},
    "s4_0_hh_anyone_working_lbl": {"0.": .35, "1.": .65},
    "s4_1_is_main_earner_lbl": {"0.": .45, "1.": .55},
    "s4_8_worked_pay_lastweek_lbl": {"1.": .80, "2.": .15, "98": .03, "99": .02},
    "s4_9_business_lastweek_lbl": {"1.": .10, "2.": .85, "98": .03, "99": .02},
    "s4_10_family_biz_lastweek_lbl": {"1.": .05, "2.": .90, "98": .03, "99": .02},
    "s6_3_income_adequacy_lbl": {"1.": .03, "2.": .17, "3.": .45, "4.": .35},
    "s6_5_assistance_received_lbl": {"0.": .45, "1.": .52, "98": .02, "99": .01},
    "s6_10_face_challenges_lbl": {"0.": .40, "1.": .57, "98": .02, "99": .01},
    "s3_4a_visit_year": {"before": .02, "2011": .05, "2015": .06, "2019": .10, "2023": .07,
                         "2024": .15, "2025": .50, "98": .04, "99": .01},
    "s3_8a_return_year": {"before": .01, "2011": .03, "2015": .05, "2019": .08, "2023": .08,
                          "2024": .20, "2025": .50, "98": .04, "99": .01},
}
MONTH_BASE = {"1": .14, "2": .12, "3": .12, "4": .13, "5": .14, "6": .06, "7": .02, "8": .02,
              "9": .02, "10": .02, "11": .03, "12": .13, "98": .04, "99": .01}

# Item classes for re-interview stability.
ATTITUDE_PREFIX = ("s2_6_", "s3_11_", "s3_12_", "s3_13_", "s3_14_", "s3_15_", "s3_16_",
                   "s3_17_", "s3_18_", "s3_19_", "s3_2", "s5_", "s7a_", "s7b_", "s7c_")
RESPONDENT_ITEMS = ("s4_1_", "s4_3_", "s4_4_", "s4_5_", "s4_6_")

# Actual routes used when gates are noisy. Each cond: (parent, value prefixes, prob, countries).
# Blocks share their route randomness through `key`.
NOISY_ROUTES = {
    r"^s2_(9|10)_": dict(key="prop", conds=[("s2_7_own_house_syria_lbl", ["1."], 1.0, None),
                                            ("s2_8_own_land_syria_lbl", ["1."], 1.0,
                                             ["Jordan", "Lebanon"])]),
    r"^s2_11_": dict(key="occ", conds=[("s2_10_house_condition_lbl", ["1.", "2.", "4."], 1.0,
                                        None)]),
    r"^s3_(3|4a|4b)_": dict(key="visit", conds=[("s3_2_visited_syria_lbl", ["1.", "98"], 1.0,
                                                 None)]),
    r"^s3_6_": dict(key="perm", conds=[("s3_5_family_in_syria_lbl", ["1."], 1.0, None),
                                       ("s3_5_family_in_syria_lbl", ["2.", "98"], 1.0,
                                        ["Egypt", "Iraq"])]),
    r"^s3_(7|9a|8a|8b|9b|9c)_": dict(key="ret", conds=[
        ("s3_6_permanent_returns_lbl", ["1.", "98"], 1.0, None)]),
    r"^s3_10(a|b|c|g)_": dict(key="retw", conds=[
        ("s3_9c_returnee_working_lbl", ["1."], 1.0, None),
        ("s3_9c_returnee_working_lbl", ["2."], 1.0, ["Jordan", "Lebanon"])]),
    r"^s7a_(1|4|7)_": dict(key="s7a", conds=[
        ("s3_12_hope_return_someday_lbl", ["1."], 1.0, None),
        ("s3_11_intent_return_12m_lbl", ["1."], 1.0, ["Egypt", "Jordan", "Lebanon"])]),
    r"^s7b_": dict(key="s7b", conds=[
        ("s3_12_hope_return_someday_lbl", ["0."], 1.0, None),
        ("s3_11_intent_return_12m_lbl", ["0."], 1.0, ["Egypt", "Iraq"])]),
    r"^s7c_": dict(key="s7c", conds=[
        ("s3_11_intent_return_12m_lbl", ["98"], 1.0, None),
        ("s3_11_intent_return_12m_lbl", ["0."], 1.0, ["Lebanon"])]),
    r"^s3_14_": dict(key="s314", conds=[("s3_11_intent_return_12m_lbl", ["0.", "1.", "98"],
                                         1.0, None)]),
    r"^s3_16_": dict(key="s316", conds=[("s3_15_friend_return_likely_lbl", ["1."], 1.0, None),
                                        ("s3_15_friend_return_likely_lbl", ["3."], 1.0,
                                         ["Jordan", "Lebanon"])]),
    r"^s3_17_": dict(key="s317", conds=[("s3_15_friend_return_likely_lbl", ["2.", "98"], 1.0,
                                         None)]),
    r"^s3_23b_": dict(key="rank2", conds=[("s3_23_safety_no_concerns_lbl", ["0"], 0.85, None)]),
    r"^s4_7_": dict(key="permit", conds=[("s4_0_hh_anyone_working_lbl", ["1."], 1.0, None),
                                         ("s4_0_hh_anyone_working_lbl", ["0."], 1.0,
                                          ["Jordan", "Lebanon"])]),
    r"^s4_(3|4|5|6)_": dict(key="earner", conds=[
        ("s4_1_is_main_earner_lbl", ["0."], 1.0, None),
        ("s4_0_hh_anyone_working_lbl", ["0."], 1.0, ["Egypt", "Lebanon"])]),
    r"^s6_4_": dict(key="needs", conds=[("s6_3_income_adequacy_lbl", ["3.", "4."], 1.0, None),
                                        ("s6_3_income_adequacy_lbl", ["2."], 1.0,
                                         ["Egypt", "Iraq"])]),
    r"^s6_6_": dict(key="assist", conds=[("s6_5_assistance_received_lbl", ["1.", "98"], 1.0,
                                          None)],
                    drop_country={"Egypt": 0.35}),
    r"^s6_12_": dict(key="school", conds=[("s2_3_boys_6_17", ["1", "2", "3", "4", "5", "6", "11"],
                                           1.0, None),
                                          ("s2_3_girls_6_17", ["1", "2", "3", "4", "5", "6", "11"],
                                           1.0, None)]),
}


def load_schema():
    with open(SCHEMA_PATH, encoding="utf-8") as fh:
        s = json.load(fh)
    s["gated_value"] = NA
    return s


def _starts(values, prefixes):
    return [i for i, v in enumerate(values) if any(v.startswith(p) for p in prefixes)]


def _is_special(v):
    return bool(re.match(r"^(9[789]\b|9[789]\.|Not recorded|\[generalised)", v))


def _logit(p):
    p = np.clip(p, 1e-9, 1 - 1e-9)
    return np.log(p / (1 - p))


def _sample(P, rng):
    u = rng.random(P.shape[0])[:, None]
    c = np.cumsum(P, axis=1)
    c /= c[:, -1:]
    return np.minimum((c < u).sum(1), P.shape[1] - 1)


def _softmax(L):
    L = L - L.max(1, keepdims=True)
    E = np.exp(L)
    return E / E.sum(1, keepdims=True)


def count_value(code, values):
    v = values[code]
    return {"6-10": 7, "11+": 12}.get(v, int(v) if v.isdigit() else 0)


# =============================================================== the world ===

class World:
    """All fixed parameters of the answer model. Drawn from WORLD_SEED in a fixed
    order; dataset-specific modifiers (cfg) are applied afterwards."""

    def __init__(self, schema, cfg):
        self.schema, self.cfg = schema, cfg
        it = schema["items"]
        self.items = it
        self.targets = [n for n, r in it.items() if r["class"] == "PREDICT"]
        self.tix = {n: j for j, n in enumerate(self.targets)}
        self.gvals = {g: it[g]["values"] for g in GIVEN}
        self.vals = {t: it[t]["values"] for t in self.targets}
        rng = np.random.default_rng(WORLD_SEED)
        nT = len(TRAITS)
        self.nF = 15
        gs = cfg.get("given_scale", 1.0)
        # ---- trait means: country, governorate, origin, features ----
        cm = rng.normal(0, 0.5, (4, nT))
        hand = {"return": [-0.2, -0.6, 0.3, 0.4], "integr": [0.5, 0.3, 0.0, -0.7],
                "wealth": [0.4, 0.5, -0.1, -0.5], "hardship": [-0.3, -0.2, 0.2, 0.7],
                "connect": [-0.2, 0.3, 0.2, 0.3]}
        for t, v in hand.items():
            cm[:, TRAITS.index(t)] += v
        self.country_mu = cm * gs
        self.gov_mu = rng.normal(0, 0.45, (46, nT)) * gs * cfg.get("gov_trait_scale", 1.0)
        om = rng.normal(0, 0.45, (16, nT))
        ov = self.gvals["s2_4a_origin_governorate_lbl"]
        for name, d in {"Dar'a": 0.8, "Homs": 0.5, "Damascus": 0.4, "Rural Damascus": 0.5,
                        "Al-Hasakeh": -0.9, "Ar-Raqqa": -0.6, "Deir-ez-Zor": -0.5,
                        "Idleb": 0.2}.items():
            om[ov.index(name), TRAITS.index("return")] += d
        for name, d in {"Homs": -0.6, "Aleppo": -0.4, "Ar-Raqqa": -0.7, "Deir-ez-Zor": -0.6,
                        "Idleb": -0.3, "Dar'a": -0.2}.items():
            om[ov.index(name), TRAITS.index("ties")] += d
        self.origin_mu = om * gs
        fb = rng.normal(0, 0.2, (self.nF, nT))
        for f, t, v in [(6, "wealth", 0.5), (6, "integr", 0.4), (10, "hardship", 0.4),
                        (10, "wealth", -0.4), (12, "hardship", 0.5), (12, "wealth", -0.5),
                        (5, "return", 0.3), (5, "connect", -0.2), (11, "wealth", 0.4),
                        (14, "integr", -0.3), (0, "return", 0.15)]:
            fb[f, TRAITS.index(t)] += v
        # respondent-level features (relationship, age, education, marital status, single
        # parent, gender) move the household traits much less than household features
        fb[[1, 2, 3, 4, 5, 6, 7, 8, 9, 14]] *= cfg.get("resp_trait_scale", 0.35)
        self.feat_mu = fb * gs
        self.chol = np.linalg.cholesky(TRAIT_CORR)
        self.noise = cfg.get("trait_noise", 1.0)

        # ---- items ----
        self.spec = {}
        blocks = []
        for t in self.targets:
            vals = self.vals[t]
            K = len(vals)
            sp = {"K": K}
            if K == 1:
                sp["kind"] = "single"
            elif vals == ["0", "1"]:
                sp["kind"] = "binary"
                m = re.match(r"^(s\d+[a-z]?_\d+[a-z]?)_", t)
                sp["block"] = m.group(1) if m else t
                if sp["block"] not in blocks:
                    blocks.append(sp["block"])
                sp["exclusive"] = bool(re.search(r"(_none|no_concerns|dont_know|_PNA|_pna|"
                                                 r"no_answer|_never)", t))
            elif t.startswith(ORDINAL_PREFIX):
                sp["kind"] = "ordinal"
            else:
                sp["kind"] = "nominal"
            sp["special"] = [i for i, v in enumerate(vals) if _is_special(v)]
            sp["subst"] = [i for i in range(K) if i not in sp["special"]]
            prim = next((tr for p, tr in SECTION_TRAITS if t.startswith(p)), [])
            sp["prim"] = prim
            # base marginal
            if t in BASE:
                base = np.full(K, 0.004)
                for pre, p in BASE[t].items():
                    for i in _starts(vals, [pre]):
                        base[i] = p
            elif t.endswith("_month"):
                base = np.array([MONTH_BASE.get(v, 0.01) for v in vals])
            elif sp["kind"] == "binary":
                base = None
                p1 = (rng.uniform(0.01, 0.05) if sp["exclusive"]
                      else float(np.clip(rng.beta(0.8, 2.2), 0.02, 0.9)))
                sp["b"] = _logit(p1)
            elif sp["kind"] == "ordinal":
                ks = len(sp["subst"])
                m, w = rng.uniform(-0.3, ks - 0.7), rng.uniform(0.7, 2.0)
                q = np.exp(-(np.arange(ks) - m) ** 2 / (2 * w * w)) + 0.01
                base = np.zeros(K)
                base[sp["subst"]] = q / q.sum() * (1 - 0.03 * bool(sp["special"]))
                if sp["special"]:
                    base[sp["special"]] = 0.03 * rng.dirichlet(np.ones(len(sp["special"])) * 2)
            else:
                base = np.zeros(K)
                base[sp["subst"]] = rng.dirichlet(np.full(len(sp["subst"]), 0.9))
                if sp["special"]:
                    base[sp["subst"]] *= 0.96
                    base[sp["special"]] = 0.04 * rng.dirichlet(np.ones(len(sp["special"])) * 2)
            if base is not None:
                base = np.maximum(base, 1e-4)
                sp["base"] = base / base.sum()
                if sp["kind"] == "binary":
                    sp["b"] = _logit(sp["base"][1])
            # loadings and effects
            lw = cfg.get("load_scale", 1.0)
            ce_scale = rng.choice([0.3, 0.6, 1.0, 1.5]) * cfg.get("country_scale", 1.0)
            if sp["kind"] in ("binary", "ordinal"):
                w = rng.normal(0, 0.15, nT)
                for tr, sign in prim:
                    w[TRAITS.index(tr)] = sign * rng.uniform(0.6, 1.3)
                sp["w"] = w * lw
                sp["ce"] = rng.normal(0, ce_scale, 4)
                sp["ge"] = rng.normal(0, 0.3, 46) * cfg.get("gov_scale", 1.0)
                sp["oe"] = rng.normal(0, 0.35, 16)
                sp["we"] = rng.normal(0, 0.1)
                sp["fe"] = rng.normal(0, 0.2, self.nF)
                sp["style"] = rng.normal(0.3 if sp["kind"] == "binary" else 0.0, 0.3)
                sp["bf"] = rng.uniform(0.5, 1.1)
                if sp["kind"] == "ordinal":
                    q = sp["base"][sp["subst"]]
                    q = q / q.sum()
                    sp["cuts"] = _logit(np.cumsum(q)[:-1])
                    sp["sp_b"] = _logit(max(sp["base"][sp["special"]].sum(), 1e-4)) \
                        if sp["special"] else None
            elif sp["kind"] == "nominal":
                W = rng.normal(0, 0.15, (nT, K))
                for tr, sign in prim:
                    W[TRAITS.index(tr)] = rng.normal(0, 0.9, K)
                if not prim:
                    W += rng.normal(0, 0.3, (nT, K))
                sp["W"] = W * lw
                sp["ce"] = rng.normal(0, ce_scale, (4, K))
                sp["ge"] = rng.normal(0, 0.3, (46, K)) * cfg.get("gov_scale", 1.0)
                sp["oe"] = rng.normal(0, 0.35, (16, K))
                sp["we"] = rng.normal(0, 0.1, K)
                sp["fe"] = rng.normal(0, 0.2, (self.nF, K))
                for z in (sp["ce"], sp["ge"], sp["oe"], sp["we"], sp["fe"]):
                    z -= z.mean(-1, keepdims=True)
            self.spec[t] = sp
        self.blocks = blocks
        # dataset modifiers, drawn from a separate stream so the base world is identical
        mrng = np.random.default_rng(WORLD_SEED + 1)
        for t in cfg.get("country_const_items", []):
            sp = self.spec[t]
            pat = mrng.permutation([3.5, 2.5, -2.5, -3.5])
            if sp["kind"] == "nominal":
                sp["ce"] = np.zeros((4, sp["K"]))
                for c in range(4):
                    sp["ce"][c, mrng.choice(sp["subst"])] = abs(pat[c]) + 1.0
            else:
                sp["ce"] = pat
        for t, b in cfg.get("base_override", {}).items():
            sp = self.spec[t]
            base = np.full(sp["K"], 1e-4)
            for pre, p in b.items():
                for i in _starts(self.vals[t], [pre]):
                    base[i] = p
            sp["base"] = base / base.sum()
            if sp["kind"] == "binary":
                sp["b"] = _logit(sp["base"][1])
            if sp["kind"] == "ordinal":
                q = sp["base"][sp["subst"]] / sp["base"][sp["subst"]].sum()
                sp["cuts"] = _logit(np.cumsum(q)[:-1])
                if sp["special"]:
                    sp["sp_b"] = _logit(sp["base"][sp["special"]].sum())
            sp["shrink"] = cfg.get("override_shrink", 0.3)      # weaker latent spread so the rare share stays rare
        # interactions (separate stream so the additive world is unchanged)
        irng = np.random.default_rng(WORLD_SEED + 3)
        isc = cfg.get("interact_scale", 0.0)
        self.co_mu = irng.normal(0, 0.6, (4, 16, nT)) * isc * gs
        self.cw_mu = irng.normal(0, 0.4, (4, 2, nT)) * isc * gs
        for t in self.targets:
            sp = self.spec[t]
            sp["thr_k"] = int(irng.integers(0, nT))
            sp["thr_tau"] = float(irng.normal(0, 0.8))
            sp["thr_g"] = (irng.normal(0, 1.5, sp["K"]) if sp["kind"] == "nominal"
                           else float(irng.normal(0, 1.5))) * isc
        self.isc = isc
        self.t_mean = np.zeros(nT)
        self.t_sd = np.ones(nT)
        if isc:
            srng = np.random.default_rng(WORLD_SEED + 4)
            Hs = self.gen_households(4000, srng)
            idx = np.arange(4000)
            Rs = self.gen_respondents(Hs, idx, srng)
            Gs = np.zeros((4000, len(GIVEN)), int)
            Gs[:, GI["wave"]] = srng.random(4000) < 0.39
            for c in HH_COLS:
                Gs[:, GI[c]] = Hs[c]
            for c in RESP_COLS:
                Gs[:, GI[c]] = Rs[c]
            Ts = self.latents(Gs, srng)["T"]
            self.t_mean, self.t_sd = Ts.mean(0), Ts.std(0)
        # routing
        self.routes = {}
        if cfg.get("noisy_gates"):
            rr = np.random.default_rng(WORLD_SEED + 2)
            for t in self.targets:
                g = it[t].get("gate")
                if not g:
                    continue
                route = None
                for pat, r in NOISY_ROUTES.items():
                    if re.search(pat, t):
                        route = r
                        break
                if route is None:
                    route = dict(key=g["parent"], conds=[(g["parent"], g["observed_if"], 1.0,
                                                          None)])
                route = dict(route)
                route["leak"] = rr.uniform(0, cfg.get("leak_max", 0.03))
                route["drop"] = rr.uniform(0, cfg.get("drop_max", 0.05))
                self.routes[t] = route
        else:
            for t in self.targets:
                g = it[t].get("gate")
                if g:
                    self.routes[t] = dict(key=t, conds=[(g["parent"], g["observed_if"], 1.0,
                                                         None)], leak=0.0, drop=0.0, exact=True)
        # route order: parents first
        order, placed = [], set()
        pending = list(self.targets)
        while pending:
            nxt = []
            for t in pending:
                ps = [c[0] for c in self.routes.get(t, {}).get("conds", [])]
                g = it[t].get("gate")
                if g:
                    ps.append(g["parent"])
                if all(p in placed or p in GI for p in ps):
                    order.append(t)
                    placed.add(t)
                else:
                    nxt.append(t)
            if len(nxt) == len(pending):
                raise ValueError("routing cycle")
            pending = nxt
        self.route_order = order
        # stability classes for re-interviews
        self.iclass = np.array([2 if t.startswith(RESPONDENT_ITEMS) else
                                1 if t.startswith(ATTITUDE_PREFIX) else 0
                                for t in self.targets])

    # ------------------------------------------------------------- GIVEN --
    def gen_households(self, n, rng):
        gv = self.gvals
        C = rng.choice(4, n, p=[COUNTRY_SHARE[c] for c in gv["s1_2_country_asylum_lbl"]])
        gov = np.zeros(n, int)
        org = np.zeros(n, int)
        ov = gv["s2_4a_origin_governorate_lbl"]
        for ci, cname in enumerate(gv["s1_2_country_asylum_lbl"]):
            idx = np.flatnonzero(C == ci)
            names = GOVS[cname]
            w = (np.arange(len(names)) + 1.0) ** -1.2
            gov[idx] = np.array([gv["governorate_col"].index(x) for x in names])[
                rng.choice(len(names), len(idx), p=w / w.sum())]
            po = np.full(16, 0.002)
            for k, p in {**ORIGIN_SHARE[cname], **ORIGIN_RARE}.items():
                po[ov.index(k)] = p
            org[idx] = rng.choice(16, len(idx), p=po / po.sum())
        fh = rng.random(n) < np.where(C == 3, 0.2, 0.13)
        size = rng.gamma(4.0, 0.25, n) * np.where(C == 1, 1.2, 1.0)
        def bins(c, col):
            vals = gv[col]
            out = np.empty(n, int)
            for i, x in enumerate(c):
                if x <= 5 and str(x) in vals:
                    out[i] = vals.index(str(x))
                elif x <= 10 and "6-10" in vals:
                    out[i] = vals.index("6-10")
                elif "11+" in vals and x > 10:
                    out[i] = vals.index("11+")
                else:
                    out[i] = len([v for v in vals if v.isdigit() and int(v) <= x]) - 1
            return out
        H = {"s1_2_country_asylum_lbl": C, "governorate_col": gov,
             "s2_4a_origin_governorate_lbl": org}
        H["s2_3_boys_0_5"] = bins(rng.poisson(0.45 * size), "s2_3_boys_0_5")
        H["s2_3_girls_0_5"] = bins(rng.poisson(0.45 * size), "s2_3_girls_0_5")
        H["s2_3_boys_6_17"] = bins(rng.poisson(0.85 * size), "s2_3_boys_6_17")
        H["s2_3_girls_6_17"] = bins(rng.poisson(0.85 * size), "s2_3_girls_6_17")
        H["s2_3_men_18_59"] = bins(np.where(fh, rng.poisson(0.25, n), 1 + rng.poisson(0.35 * size)),
                                   "s2_3_men_18_59")
        H["s2_3_women_18_59"] = bins(1 + rng.poisson(0.35 * size), "s2_3_women_18_59")
        H["s2_3_men_60plus"] = rng.choice(4, n, p=[.88, .105, .013, .002])
        H["s2_3_women_60plus"] = rng.choice(6, n, p=[.85, .13, .015, .003, .001, .001])
        H["_fh"] = fh
        return H

    def gen_respondents(self, H, idx, rng, exclude=None):
        """Respondent GIVEN columns for households H[idx]. `exclude`: relationship
        codes to avoid (the previous respondent), used for re-interviews."""
        n = len(idx)
        fh = H["_fh"][idx]
        C = H["s1_2_country_asylum_lbl"][idx]
        p_m = np.array([.52, .36, .06, .02, .015, .005, .012, .006, .002])
        p_f = np.array([.75, .02, .14, .01, .04, .01, .02, .008, .002])
        rel = np.zeros(n, int)
        for i in range(n):
            p = (p_f if fh[i] else p_m).copy()
            if exclude is not None:
                p[exclude[i]] *= 0.05
            rel[i] = rng.choice(9, p=p / p.sum())
        age_p = {0: [.05, .25, .33, .2, .11, .05], 1: [.1, .35, .3, .15, .07, .03],
                 2: [.7, .28, .02, 0, 0, 0], 3: [.4, .5, .1, 0, 0, 0], 4: [0, 0, 0, .1, .4, .5],
                 5: [0, 0, 0, .1, .4, .5], 6: [.3, .4, .2, .1, 0, 0], 7: [.2, .3, .2, .2, .1, 0],
                 8: [.2, .3, .2, .2, .1, 0]}
        age = np.array([rng.choice(6, p=np.array(age_p[r]) / sum(age_p[r])) for r in rel])
        age[rng.random(n) < 0.003] = 6
        edu_c = {0: [.06, .01, .30, .30, .06, .07, .20], 1: [.10, .01, .40, .25, .06, .06, .12],
                 2: [.12, .01, .45, .25, .05, .04, .08], 3: [.08, .01, .40, .28, .06, .05, .12]}
        edu = np.zeros(n, int)
        for i in range(n):
            p = np.array(edu_c[C[i]], float)
            if age[i] >= 4:
                p[:3] *= 2.0
            if age[i] <= 1:
                p[3:] *= 1.5
            edu[i] = rng.choice(7, p=p / p.sum())
        edu[rng.random(n) < 0.003] = 7
        mar = np.zeros(n, int)
        for i in range(n):
            r = rel[i]
            if r == 0 and fh[i]:
                p = [.05, .25, .002, .01, .45, .14, .10]
            elif r in (0, 1):
                p = [.02, .92, .002, .03, .01, .01, .01]
            elif r in (2, 6, 7, 8):
                p = [.75, .22, .002, 0, .005, .015, .01]
            elif r == 3:
                p = [.02, .95, .002, .01, .01, .005, .005]
            else:
                p = [0, .6, 0, .02, .36, .01, .01]
            p = np.array(p) / sum(p)
            mar[i] = rng.choice(7, p=p)
        kids = sum(H[c][idx] for c in COUNT_COLS[:4]) > 0
        lone = np.isin(mar, [4, 5, 6]) | (fh & (rel == 0))
        sp = np.where(lone & kids, rng.random(n) < 0.8, rng.random(n) < 0.02).astype(int)
        return {"s2_1_hh_relationship_lbl": rel, "s2_1b_age": age,
                "s2_1c_education_level_lbl": edu, "s2_1d_marital_status_lbl": mar,
                "s2_2_single_parent_lbl": sp}

    # -------------------------------------------------------------- latents --
    def features(self, G):
        gv = self.gvals
        n = G.shape[0]
        F = np.zeros((n, self.nF))
        rel = G[:, GI["s2_1_hh_relationship_lbl"]]
        F[:, 0] = G[:, GI["wave"]] == 1
        F[:, 1] = rel == 0
        F[:, 2] = rel == 1
        F[:, 3] = np.isin(rel, [2, 3])
        F[:, 4] = np.isin(rel, [4, 5])
        age = G[:, GI["s2_1b_age"]]
        F[:, 5] = np.where(age == 6, 0, (age - 2) / 2)
        edu = G[:, GI["s2_1c_education_level_lbl"]]
        F[:, 6] = np.where(edu == 7, 0, (edu - 3) / 2)
        mar = G[:, GI["s2_1d_marital_status_lbl"]]
        F[:, 7] = np.isin(mar, [1, 2, 3])
        F[:, 8] = np.isin(mar, [4, 5, 6])
        F[:, 9] = G[:, GI["s2_2_single_parent_lbl"]]
        cnt = {c: np.array([count_value(k, gv[c]) for k in range(len(gv[c]))])[G[:, GI[c]]]
               for c in COUNT_COLS}
        kids = sum(cnt[c] for c in COUNT_COLS[:4])
        F[:, 10] = np.log1p(kids) - 1.0
        F[:, 11] = cnt["s2_3_men_18_59"] > 0
        F[:, 12] = cnt["s2_3_men_18_59"] == 0
        F[:, 13] = (cnt["s2_3_men_60plus"] + cnt["s2_3_women_60plus"]) > 0
        return F, cnt

    def latents(self, G, rng):
        n = G.shape[0]
        F, cnt = self.features(G)
        rel = G[:, GI["s2_1_hh_relationship_lbl"]]
        pf = np.array([.08, .97, .45, .92, .6, .6, .5, .5, .5])[rel]
        pf = np.where((rel == 0) & (F[:, 12] == 1), 0.85, pf)
        fem = (rng.random(n) < pf).astype(float)
        F[:, 14] = fem
        mu = (self.country_mu[G[:, GI["s1_2_country_asylum_lbl"]]]
              + self.gov_mu[G[:, GI["governorate_col"]]]
              + self.origin_mu[G[:, GI["s2_4a_origin_governorate_lbl"]]]
              + F @ self.feat_mu)
        if getattr(self, "isc", 0):
            c, o, w = (G[:, GI["s1_2_country_asylum_lbl"]], G[:, GI["s2_4a_origin_governorate_lbl"]],
                       G[:, GI["wave"]])
            mu = mu + self.co_mu[c, o] + self.cw_mu[c, w]
        T = mu + self.noise * rng.standard_normal((n, len(TRAITS))) @ self.chol.T
        return {"F": F, "T": T, "style": rng.standard_normal(n),
                "B": rng.standard_normal((n, len(self.blocks))), "cnt": cnt}

    # ----------------------------------------------------- potential answers --
    def _hand(self, t, F, lat, L):
        """Hand-coded dependencies, added to the logit of one option (nominal) or to
        the linear predictor (binary / ordinal)."""
        fem, head, spouse = F[:, 14], F[:, 1], F[:, 2]

        def add(col, x):
            if L.ndim == 2:
                L[:, col] += x
            else:
                L[:] += x
        if t == "s4_0_hh_anyone_working_lbl":
            add(1, 1.6 * F[:, 11] - 1.2 * F[:, 12] + 0.4 * (lat["cnt"]["s2_3_men_18_59"] >= 2))
        elif t == "s4_1_is_main_earner_lbl":
            add(1, 2.2 * head * (1 - fem) - 2.0 * fem - 0.8 * F[:, 3])
        elif t == "s4_3_main_earner_gender":
            add(1, 2.5 * F[:, 12] - 1.0 * fem * F[:, 12])
        elif t == "s4_5_main_earner_relation_lbl":
            add(0, 2.5 * (spouse + F[:, 3]) - 1.0 * head)
            add(2, 1.5 * F[:, 4] + 1.0 * F[:, 12])
        elif t == "s2_6_return_decision_maker":
            add(0, 1.5 * head * (1 - fem))
            add(1, 0.8 * spouse)
            add(3, 1.2 * (1 - head) - 0.8)
        elif t == "s3_10b_returnee_gender_lbl":
            add(1, -1.5)
        return L

    def potential(self, G, lat, rng):
        n = G.shape[0]
        A = np.zeros((n, len(self.targets)), np.int16)
        c = G[:, GI["s1_2_country_asylum_lbl"]]
        g = G[:, GI["governorate_col"]]
        o = G[:, GI["s2_4a_origin_governorate_lbl"]]
        wv = G[:, GI["wave"]]
        F, T = lat["F"], lat["T"]
        Fs = F.copy()
        Fs[:, 14] = Fs[:, 14] - 0.5
        for j, t in enumerate(self.targets):
            sp = self.spec[t]
            shrink = sp.get("shrink", 1.0)
            if sp["kind"] == "single":
                continue
            if sp["kind"] in ("binary", "ordinal"):
                eta = shrink * (T @ sp["w"] + sp["ce"][c] + sp["ge"][g] + sp["oe"][o]
                                + sp["we"] * wv + Fs @ sp["fe"] + sp["style"] * lat["style"])
                if self.isc:
                    k = sp["thr_k"]
                    eta = eta + shrink * sp["thr_g"] * ((T[:, k] - self.t_mean[k]) / self.t_sd[k]
                                               > sp["thr_tau"])
                eta = self._hand(t, F, lat, eta)
                if sp["kind"] == "binary":
                    bi = self.blocks.index(sp["block"])
                    eta = eta + shrink * sp["bf"] * lat["B"][:, bi]
                    A[:, j] = rng.random(n) < 1 / (1 + np.exp(-(sp["b"] + eta)))
                    continue
                cdf = 1 / (1 + np.exp(-(sp["cuts"][None, :] - eta[:, None])))
                P = np.zeros((n, sp["K"]))
                Ps = np.diff(np.concatenate([np.zeros((n, 1)), cdf, np.ones((n, 1))], 1), axis=1)
                if sp["special"]:
                    psp = 1 / (1 + np.exp(-(sp["sp_b"] + 0.3 * lat["style"] - 0.3 * F[:, 6])))
                    share = sp["base"][sp["special"]] / sp["base"][sp["special"]].sum()
                    P[:, sp["special"]] = psp[:, None] * share[None, :]
                    Ps = Ps * (1 - psp)[:, None]
                P[:, sp["subst"]] = Ps
                A[:, j] = _sample(P, rng)
            else:
                L = np.log(sp["base"])[None, :] + shrink * (
                    T @ sp["W"] + sp["ce"][c] + sp["ge"][g] + sp["oe"][o]
                    + np.outer(wv, sp["we"]) + Fs @ sp["fe"])
                if self.isc:
                    k = sp["thr_k"]
                    step = (T[:, k] - self.t_mean[k]) / self.t_sd[k] > sp["thr_tau"]
                    L = L + shrink * np.outer(step, sp["thr_g"])
                L = self._hand(t, F, lat, L)
                A[:, j] = _sample(_softmax(L), rng)
        return self.exclusive(A)

    def exclusive(self, A):
        for b in self.blocks:
            js = [self.tix[t] for t in self.targets if self.spec[t].get("block") == b]
            ex = [j for j in js if self.spec[self.targets[j]]["exclusive"]]
            if not ex:
                continue
            anyx = A[:, ex].max(1) > 0
            for j in js:
                if j not in ex:
                    A[anyx, j] = 0
            first = np.full(A.shape[0], -1)
            for j in ex:
                first = np.where((first < 0) & (A[:, j] > 0), j, first)
            for j in ex:
                A[(first >= 0) & (first != j), j] = 0
        return A

    # --------------------------------------------------------------- routing --
    def _codes_matching(self, p, prefixes, exact):
        vals = self.gvals[p] if p in GI else self.vals[p]
        if exact:
            return [k for k, v in enumerate(vals) if v in prefixes]
        return [k for k, v in enumerate(vals) if any(v.startswith(q) for q in prefixes)]

    def route(self, A, G, rng):
        """Observed codes: -1 = NA_GATED."""
        n = A.shape[0]
        Y = A.astype(np.int16).copy()
        keyu = {}
        cidx = G[:, GI["s1_2_country_asylum_lbl"]]
        cnames = self.gvals["s1_2_country_asylum_lbl"]

        def pcode(p):
            return G[:, GI[p]] if p in GI else Y[:, self.tix[p]]

        for t in self.route_order:
            r = self.routes.get(t)
            if r is None:
                continue
            j = self.tix[t]
            open_ = np.zeros(n, bool)
            for ci, (p, pre, prob, countries) in enumerate(r["conds"]):
                m = np.isin(pcode(p), self._codes_matching(p, pre, r.get("exact", False)))
                if prob < 1.0:
                    k = (r["key"], ci)
                    if k not in keyu:
                        keyu[k] = rng.random(n)
                    m &= keyu[k] < prob
                if countries:
                    m &= np.isin(cidx, [cnames.index(c) for c in countries])
                open_ |= m
            if not r.get("exact"):
                gp = self.items[t]["gate"]["parent"]
                p_asked = np.ones(n, bool) if gp in GI else Y[:, self.tix[gp]] >= 0
                open_ |= p_asked & (rng.random(n) < r["leak"])
                dc = np.array([r.get("drop_country", {}).get(c, 0.0) for c in cnames])
                open_ &= ~(rng.random(n) < r["drop"] + dc[cidx])
            Y[~open_, j] = -1
        return Y

    def declared_open(self, Y, G):
        """Declared-gate openness given observed codes, for agreement statistics."""
        out = {}
        for t in self.targets:
            g = self.items[t].get("gate")
            if not g:
                continue
            p = g["parent"]
            if p in GI:
                pv = np.array(self.gvals[p], dtype=object)[G[:, GI[p]]]
            else:
                jp = self.tix[p]
                pv = np.array(self.vals[p] + [NA], dtype=object)[np.where(Y[:, jp] < 0, -1,
                                                                        Y[:, jp])]
            out[t] = np.isin(pv, g["observed_if"])
        return out

    # ------------------------------------------------------------ simulate --
    def simulate(self, G, rng, src=None, stab=None):
        """Potential answers A and observed Y for GIVEN codes G. With src (n x P
        potential answers of a source interview) and stab (n x P copy probs),
        each item is copied from src w.p. stab, else drawn fresh."""
        lat = self.latents(G, rng)
        A = self.potential(G, lat, rng)
        if src is not None:
            A = np.where(rng.random(A.shape) < stab, src, A).astype(np.int16)
            A = self.exclusive(A)
        return A, self.route(A, G, rng)

    def stability(self, same_resp, cfg):
        """n x P copy probabilities for re-interviews."""
        s = np.array([cfg.get("stab_household", 0.78), cfg.get("stab_attitude", 0.45),
                      cfg.get("stab_respondent", 0.8)])
        S = np.tile(s[self.iclass], (len(same_resp), 1))
        new = ~same_resp
        S[new] = np.array([cfg.get("stab_household", 0.78), cfg.get("stab_attitude_new", 0.3),
                           cfg.get("stab_respondent_new", 0.1)])[self.iclass]
        return S


# =============================================================== building ===

def assign_roles(strata, counts, rng):
    """Random roles in exact counts, spread evenly within each stratum."""
    n = len(strata)
    order = np.lexsort((rng.random(n), strata))
    seq = []
    for r, c in enumerate(counts):
        seq += [((k + rng.random()) / c, r) for k in range(c)]
    seq.sort()
    roles = np.empty(n, int)
    roles[order] = [r for _, r in seq]
    return roles


def build(name, cfg, seed):
    """Generate a dataset; returns (frame, meta). meta carries G, A, Y, twin links."""
    schema = load_schema()
    W = World(schema, cfg)
    rng = np.random.default_rng(seed)
    n_rows = schema["dataset"]["n_rows"]
    n1, n2 = 6316, n_rows - 6316
    twin_share = cfg.get("twin_share", 0.0)
    n_twin = int(round(twin_share * n2))
    extra = cfg.get("extra_appearances", [])      # [(n households, extra copies)]
    n_extra = sum(h * k for h, k in extra)
    n_new2 = n2 - n_twin - n_extra
    n_hh = n1 + n_new2
    H = W.gen_households(n_hh, rng)
    hh_of_row = np.concatenate([np.arange(n1), n1 + np.arange(n_new2)])
    wave = np.concatenate([np.zeros(n1, int), np.ones(n_new2, int)])
    R = W.gen_respondents(H, hh_of_row, rng)

    def Gmat(hh_idx, Rr, wv):
        G = np.zeros((len(hh_idx), len(GIVEN)), int)
        G[:, GI["wave"]] = wv
        for c in HH_COLS:
            G[:, GI[c]] = H[c][hh_idx]
        for c in RESP_COLS:
            G[:, GI[c]] = Rr[c]
        return G

    G = Gmat(hh_of_row, R, wave)
    A, Y = W.simulate(G, rng)
    src_row = np.full(len(G), -1)
    same_resp = np.ones(len(G), bool)
    # ---- re-interviews -------------------------------------------------------
    copies = []
    if n_twin:
        copies.append(rng.choice(n1, n_twin, replace=False))
    if extra:
        pool = rng.permutation(n1)
        at = 0
        for h, k in extra:
            hs = pool[at:at + h]
            at += h
            copies.append(np.repeat(hs, k))
    if copies:
        src = np.concatenate(copies)
        m = len(src)
        Rt = {c: R[c][src].copy() for c in RESP_COLS}
        new = rng.random(m) < cfg.get("new_respondent", 0.5)
        Rn = W.gen_respondents(H, hh_of_row[src], rng, exclude=R["s2_1_hh_relationship_lbl"][src])
        for c in RESP_COLS:
            Rt[c] = np.where(new, Rn[c], Rt[c])
        bump = (~new) & (rng.random(m) < 0.04) & (Rt["s2_1b_age"] < 5)
        Rt["s2_1b_age"] = Rt["s2_1b_age"] + bump
        Gt = Gmat(hh_of_row[src], Rt, np.ones(m, int))
        if cfg.get("hh_change", 0.0):
            ch = np.flatnonzero(rng.random(m) < cfg["hh_change"])
            for i in ch:
                col = GI[COUNT_COLS[rng.integers(0, 4)]]
                Gt[i, col] = max(0, min(5, Gt[i, col] + rng.choice([-1, 1])))
        St = W.stability(~new, cfg)
        At, Yt = W.simulate(Gt, rng, src=A[src], stab=St)
        G = np.vstack([G, Gt])
        A = np.vstack([A, At])
        Y = np.vstack([Y, Yt])
        src_row = np.concatenate([src_row, src])
        same_resp = np.concatenate([same_resp, ~new])
        hh_of_row = np.concatenate([hh_of_row, hh_of_row[src]])
    assert len(G) == n_rows, (len(G), n_rows)
    # ---- unseen GIVEN levels (decided before roles: those rows forced hidden) ----
    force_hidden = np.zeros(n_rows, bool)
    for col, val in cfg.get("heldout_given_levels", []):
        code = W.gvals[col].index(val)
        force_hidden |= G[:, GI[col]] == code
    for t in cfg.get("heldout_only_items", []):
        force_hidden |= Y[:, W.tix[t]] >= 0
    # ---- roles ---------------------------------------------------------------
    sp = schema["split"]
    counts = [sp["n_train"], sp["n_dev"], sp["n_test"]]
    strata = G[:, GI["wave"]] * 4 + G[:, GI["s1_2_country_asylum_lbl"]]
    roles = assign_roles(strata, counts, rng)
    if force_hidden.any():
        fh_idx = np.flatnonzero(force_hidden & (roles == 0))
        for i in fh_idx:   # swap with a random hidden row from the same stratum, not forced
            cand = np.flatnonzero((roles > 0) & ~force_hidden & (strata == strata[i]))
            if len(cand) == 0:
                cand = np.flatnonzero((roles > 0) & ~force_hidden)
            k = rng.choice(cand)
            roles[i], roles[k] = roles[k], roles[i]
    # ---- options that appear only in held-out rows -----------------------------
    planted_opts = []
    for t, val, where in cfg.get("heldout_only_options", []):
        j = W.tix[t]
        val = next(v for v in W.vals[t] if v.startswith(val))
        k = W.vals[t].index(val)
        vis = roles == 0 if where == "DEV" else roles <= 1
        hid = roles == (1 if where == "DEV" else 2)
        has = Y[:, j] == k
        mode = np.bincount(Y[(Y[:, j] >= 0) & vis, j], minlength=len(W.vals[t])).argmax()
        Y[has & vis, j] = mode
        A[has & vis, j] = mode
        cand = np.flatnonzero(hid & (Y[:, j] >= 0) & (Y[:, j] != k))
        need = max(0, 4 - int((has & hid).sum()))
        pick = rng.choice(cand, min(need, len(cand)), replace=False)
        Y[pick, j] = k
        A[pick, j] = k
        planted_opts.append((t, val, where, int((Y[hid, j] == k).sum())))
    # ---- frame ---------------------------------------------------------------
    perm = rng.permutation(n_rows)
    G, A, Y, roles = G[perm], A[perm], Y[perm], roles[perm]
    inv = np.empty(n_rows, int)
    inv[perm] = np.arange(n_rows)
    src_row = np.where(src_row[perm] >= 0, inv[np.maximum(src_row[perm], 0)], -1)
    same_resp, hh_of_row = same_resp[perm], hh_of_row[perm]
    data = {"respondent_id": ["R%06d" % (i + 1) for i in range(n_rows)],
            "role": np.array(["TRAIN", "DEV", "TEST"], dtype=object)[roles]}
    for g in GIVEN:
        data[g] = np.array(W.gvals[g], dtype=object)[G[:, GI[g]]]
    for t in W.targets:
        j = W.tix[t]
        data[t] = np.array(W.vals[t] + [NA], dtype=object)[np.where(Y[:, j] < 0, -1, Y[:, j])]
    cols = ["respondent_id", "role"] + [n for n, r in schema["items"].items()
                                        if r["class"] in ("GIVEN", "PREDICT")]
    frame = pd.DataFrame(data)[cols]
    meta = dict(W=W, G=G, A=A, Y=Y, roles=roles, src_row=src_row, same_resp=same_resp,
                hh=hh_of_row, planted_opts=planted_opts, schema=schema, cfg=cfg, seed=seed)
    return frame, meta


def write(name, frame, meta, readme):
    out = os.path.join(OUT_ROOT, name)
    os.makedirs(out, exist_ok=True)
    schema = meta["schema"]
    for c in frame.columns:
        if c not in ("respondent_id", "role"):
            allowed = set(schema["items"][c]["values"]) | ({NA} if schema["items"][c].get("gate")
                                                           else set())
            bad = set(frame[c].unique()) - allowed
            assert not bad, (c, bad)
    assert not frame.isna().any().any()
    frame.to_parquet(os.path.join(out, "respondents.parquet"), index=False)
    with open(os.path.join(out, "schema.json"), "w", encoding="utf-8") as fh:
        json.dump(schema, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    with open(os.path.join(out, "README.md"), "w", encoding="utf-8") as fh:
        fh.write(readme)
    return out


# ============================================================ diagnostics ===

def agreement(meta):
    """Per gated item: accuracy of the declared gate as a predictor of 'holds a value'."""
    W, Y, G = meta["W"], meta["Y"], meta["G"]
    dec = W.declared_open(Y, G)
    out = {}
    for t, o in dec.items():
        has = Y[:, W.tix[t]] >= 0
        out[t] = float((o == has).mean())
    return out


def twin_stats(meta):
    src, roles, A, Y, W = meta["src_row"], meta["roles"], meta["A"], meta["Y"], meta["W"]
    tw = np.flatnonzero(src >= 0)
    if not len(tw):
        return {}
    same = (Y[tw] == Y[src[tw]])
    held = Y[src[tw]] >= 0
    cls = W.iclass
    out = {"n_reinterviews": int(len(tw)),
           "new_respondent_share": float((~meta["same_resp"][tw]).mean())}
    for c, nm in ((0, "household"), (1, "attitude"), (2, "respondent")):
        m = held[:, cls == c]
        out["equal_%s_items_where_source_answered" % nm] = float(same[:, cls == c][m].mean())
    out["equal_all_cells_incl_NA"] = float(same.mean())
    return out


def ceiling(meta, phase=1, M=1000, chunk=60, use_twin=True, seed=123):
    """Skill of the generating distribution P(y | GIVEN) (Monte Carlo, M draws per
    hidden row), and, if re-interviews exist and use_twin, of P(y | GIVEN, a
    visible linked interview's potential answers) (an upper bound: it uses the
    linked row's answers to questions it was not asked). Returns dict."""
    W, G, A, Y, roles = meta["W"], meta["G"], meta["A"], meta["Y"], meta["roles"]
    src = meta["src_row"]
    vis = roles == 0 if phase == 1 else roles <= 1
    hid = np.flatnonzero(roles == (1 if phase == 1 else 2))
    P = len(W.targets)
    K = np.array([len(W.vals[t]) + (1 if W.items[t].get("gate") else 0) for t in W.targets])
    # marginal reference (as score.py: visible counts + 0.5, floored)
    Ycode = np.where(Y < 0, K[None, :] - 1, Y)
    ref_lp = np.zeros((len(hid), P))
    for j in range(P):
        cnt = np.bincount(Ycode[vis, j], minlength=K[j]) + 0.5
        p = cnt / cnt.sum()
        p = FLOOR + (1 - K[j] * FLOOR) * p
        ref_lp[:, j] = np.log(p[Ycode[hid, j]])
    R = -ref_lp.mean()
    # linked visible interview for each hidden row
    hh = meta["hh"]
    link = np.full(len(hid), -1)
    if use_twin and (src >= 0).any():
        by_hh = {}
        for i in np.flatnonzero(vis):
            by_hh.setdefault(hh[i], []).append(i)
        for a, i in enumerate(hid):
            cand = by_hh.get(hh[i], [])
            if cand:
                orig = [c for c in cand if src[c] < 0]
                link[a] = (orig or cand)[0]
    rng = np.random.default_rng(seed)
    lp_g = np.zeros((len(hid), P))
    lp_t = np.zeros((len(hid), P))
    for lo in range(0, len(hid), chunk):
        rows = hid[lo:lo + chunk]
        Gr = np.repeat(G[rows], M, axis=0)
        truth = np.repeat(Ycode[rows], M, axis=0)
        for mode in ("g", "t"):
            if mode == "t":
                sel = link[lo:lo + chunk] >= 0
                if not sel.any():
                    lp_t[lo:lo + chunk] = lp_g[lo:lo + chunk]
                    continue
                lk = np.maximum(link[lo:lo + chunk], 0)
                sr = meta["same_resp"]
                same = np.repeat(np.where(src[rows] >= 0, sr[rows], True) & sr[lk], M)
                srcA = np.repeat(A[np.maximum(link[lo:lo + chunk], 0)], M, axis=0)
                _, Ys = W.simulate(Gr, rng, src=srcA, stab=W.stability(same, meta["cfg"]))
            else:
                _, Ys = W.simulate(Gr, rng)
            Yc = np.where(Ys < 0, K[None, :] - 1, Ys)
            hit = (Yc == truth).reshape(len(rows), M, P).sum(1)
            p = (hit + 0.1) / (M + 0.1 * K[None, :])
            p = FLOOR + (1 - K[None, :] * FLOOR) * p
            if mode == "g":
                lp_g[lo:lo + chunk] = np.log(p)
            else:
                lp_t[lo:lo + chunk] = np.where(sel[:, None], np.log(p), lp_g[lo:lo + chunk])
    out = {"R": R, "ceiling_given": 1 + lp_g.mean() / R,
           "hidden_with_visible_link": float((link >= 0).mean())}
    if (link >= 0).any():
        out["ceiling_given_plus_link"] = 1 + lp_t.mean() / R
        out["ceiling_given_on_linked_rows"] = 1 + lp_g[link >= 0].mean() / R
        out["ceiling_link_on_linked_rows"] = 1 + lp_t[link >= 0].mean() / R
    # where the skill sits: gated vs ungated items
    gated = np.array([bool(W.items[t].get("gate")) for t in W.targets])
    out["ceiling_given_gated_items"] = 1 + lp_g[:, gated].mean() / -ref_lp[:, gated].mean()
    out["ceiling_given_ungated_items"] = 1 + lp_g[:, ~gated].mean() / -ref_lp[:, ~gated].mean()
    out["R_share_gated"] = float(-ref_lp[:, gated].sum() / -ref_lp.sum())
    return out


def summary_lines(meta):
    W, Y, roles = meta["W"], meta["Y"], meta["roles"]
    lines = []
    ag = agreement(meta)
    if ag:
        v = np.array(list(ag.values()))
        lines.append("gate agreement (accuracy of declared gate vs holds-a-value, all rows): "
                     "median %.3f, min %.3f, max %.3f, share < 0.7: %.2f"
                     % (np.median(v), v.min(), v.max(), (v < 0.7).mean()))
    asked_train = {t: int((Y[roles == 0, W.tix[t]] >= 0).sum()) for t in W.targets
                   if W.items[t].get("gate")}
    small = sorted(asked_train.items(), key=lambda kv: kv[1])[:12]
    lines.append("fewest asked TRAIN rows: " + ", ".join("%s=%d" % kv for kv in small))
    return lines, ag, asked_train


WORLD = dict(given_scale=5, trait_noise=0.2, load_scale=4, country_scale=3, interact_scale=1.0)
WORLD_TEXT = """Shared answer model ("world", identical in every unhcr_* dataset unless listed
under planted): six correlated household traits whose means are driven by country,
governorate, origin, country x origin and country x wave interactions and household /
respondent features (given_scale=5, trait_noise=0.2: answers are strongly determined
by the GIVEN columns, as the real leaderboard implies); trait loadings x4; per-item
country effects x3, governorate effects sd 0.3, origin effects sd 0.35; one threshold
(step) response per item on one trait (interaction structure an additive model
cannot fit); ordinal items via ordered logit with 97/98/99 codes driven by education
and a response-style trait; multi-select blocks share a household x block factor and
exclusive none / don't know / PNA options zero the rest of the block; hand-coded
dependencies (anyone working <- adult men; main earner <- relationship and gender;
schooling <- children). Gate parents have realistic shares (e.g. s3_11 No .42 / Yes
.28 / DK .30 at the base)."""


def run_builder(name, cfg, seed, planted, phases=(1,), M=1000):
    import time
    t0 = time.time()
    full_cfg = dict(WORLD, **cfg)
    frame, meta = build(name, full_cfg, seed)
    lines, ag, asked = summary_lines(meta)
    ts = twin_stats(meta)
    ceil = {ph: ceiling(meta, phase=ph, M=M) for ph in phases}
    roles = meta["roles"]
    md = ["# %s" % name, "", "Fabricated data on the REAL UNHCR schema (items, options, gates and split",
          "counts unchanged). Built by `experiments/datasets/builders/%s.py` (seed %d) with the"
          % (name, seed),
          "shared generator `unhcr_gen.py`. Roles: random, stratified on wave x country.", "",
          "## Planted", "", planted.strip(), "", "## Shared world", "", WORLD_TEXT, "",
          "Config: `%s`" % json.dumps({k: v for k, v in full_cfg.items()}, default=str), "",
          "## Measured on the delivered file", ""]
    md += ["- " + l for l in lines]
    if ts:
        md.append("- re-interviews: " + ", ".join("%s=%s" % (k, round(v, 3) if isinstance(v, float)
                                                              else v) for k, v in ts.items()))
    if meta["planted_opts"]:
        md.append("- options present only in held-out rows (item, option, role, count): %s"
                  % meta["planted_opts"])
    for ph, c in ceil.items():
        md.append("- phase %d ceiling (Monte Carlo, %d draws per hidden row): %s"
                  % (ph, M, ", ".join("%s=%.3f" % (k, v) for k, v in c.items())))
    md.append("")
    md.append("`ceiling_given` = skill of the true generating distribution P(answer | GIVEN). "
              "`ceiling_given_plus_link` additionally conditions hidden rows that have a visible "
              "interview of the same household on that interview's potential answers (including "
              "answers to questions it was not routed to), so it is an upper bound.")
    write(name, frame, meta, "\n".join(md) + "\n")
    if ag:
        with open(os.path.join(OUT_ROOT, name, "gate_agreement.json"), "w") as fh:
            json.dump({"agreement": ag, "asked_train_rows": asked}, fh, indent=1)
    print("\n".join(md))
    print("built %s in %.0fs" % (name, time.time() - t0))
    return frame, meta, ceil
