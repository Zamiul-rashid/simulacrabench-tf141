"""Fabricated datasets on the real World Bank schema (starter-kit/data/world_bank.json).

  .venv/bin/python experiments/datasets/builders/wb_build.py realistic
  .venv/bin/python experiments/datasets/builders/wb_build.py edges

Writes experiments/datasets/wb_<variant>/{respondents.parquet, schema.json,
ceiling.json}. See each dataset's README.md for what is planted.
"""
import sys

import numpy as np
import pandas as pd
from scipy.stats import binom, norm

import unicef_wb_common as C
from unicef_wb_common import Sim, build, draw, given_col, onehot, ordinal, sigmoid, softmax

SCHEMA = C.load_real_schema('world_bank')
IT = SCHEMA['items']
NA = 'Not answered'
ARMS = ['yes1', 'yes2', 'yes3', 'yes4']
AGES = ['15-19', '20-24', '25-29', '30-34', '35-44', '45+']
EDU = IT['user.educationLevel']['values']
EDU_RANK = dict(zip(EDU, [0, 1, 2, 3, 3, 4, 5, 6, 7, 7, 3]))
EMP = IT['user.employmentStatus']['values']
EMPLOYED = ['Full-time employed', 'Part-time employed', 'Freelancing / Gig Work',
            'Running own business / Self-employed', 'Internship / Apprenticeship']
WAGE = IT['user.wageOfSimilarEmployees']['values']          # 10 bands + NA
SECTORS = IT['user.preferredSector']['values']                # 23 sectors + Other + NA
# RIASEC code of each of the 23 named sectors (the schema's RIASEC item has no Artistic level;
# Arts is coded Enterprising here)
SECTOR_CODE = ['Realistic', 'Enterprising', 'Realistic', 'Social', 'Investigative', 'Realistic',
               'Social', 'Enterprising', 'Realistic', 'Conventional', 'Realistic', 'Investigative',
               'Social', 'Realistic', 'Enterprising', 'Investigative', 'Enterprising',
               'Conventional', 'Social', 'Realistic', 'Realistic', 'Enterprising', 'Realistic']
SECTOR_BASE = np.array([.3, .0, -1.3, .2, .8, -.6, .4, .2, -1.0, .4, -.3, .6, .0, -.8, -.2, -.5,
                        .5, 1.0, -.6, -1.0, -.8, .2, -.8, -1.5])
MALE_SECT = np.zeros(24); MALE_SECT[[0, 5, 13, 19, 20, 22]] = .8
FEM_SECT = np.zeros(24); FEM_SECT[[3, 6, 11, 12, 18]] = .6
HIED_SECT = np.zeros(24); HIED_SECT[[0, 4, 9, 11, 14, 15, 16]] = .5; HIED_SECT[[2, 10, 19, 5, 18]] = -.5
ENTRY_SECT = np.zeros(24); ENTRY_SECT[[17, 21, 10, 2, 18]] = 1.5
HOURS = ['0', '1', '2', '3', '4', '5', '6-10', '10-15', '16-20', '21-30', '31-40', 'more than 40']


def bands_normal(mu, sd, edges):
    """P of each band of N(mu, sd) cut at interior `edges` -> (n, len(edges)+1)."""
    cdf = norm.cdf((np.asarray(edges)[None, :] - mu[:, None]) / np.broadcast_to(sd, mu.shape)[:, None])
    cdf = np.concatenate([np.zeros((len(mu), 1)), cdf, np.ones((len(mu), 1))], axis=1)
    return np.clip(np.diff(cdf, axis=1), 0, None)


def with_na(P, p_ans):
    """Answer distribution P (n, W-1) shown with probability p_ans, else the last level NA."""
    return np.column_stack([P * p_ans[:, None], 1 - p_ans])


# ------------------------------------------------------------------ GIVEN -----

def make_given_factory(edges):
    def make_given(n, roles, rng):
        new = rng.random(n) < .612                         # platform version; country not asked
        country = np.where(new, NA, given_col(rng, ['South Africa', 'Lesotho', 'Nigeria', 'Other'],
                                              [.804, .097, .054, .045], n))
        rand = rng.random(n) < np.where(new, .053, .37)
        group = np.where(rand, given_col(rng, ARMS, [.25] * 4, n), 'Not randomised')
        pna = np.where(new, .05, .005)
        P = np.column_stack([np.outer(1 - pna, [.08, .30, .30, .17, .13, .02]), pna])
        age = given_col(rng, AGES + [NA], P)
        gender = given_col(rng, ['Female', 'Male', 'Other', 'Prefer not to say', NA],
                           [.55, .42, .005, .01, .015], n)
        a = np.array([AGES.index(x) if x in AGES else 1.5 for x in age])
        L = (np.log([.005, .01, .12, .05, .40, .15, .12, .05, .02, .005, .03])[None, :]
             + np.outer(np.minimum(a, 3) - 1.5, [-.2, -.2, -.3, 0, -.1, .2, .4, .5, .6, .6, 0]))
        L[a == 0, 5:10] -= 3
        edu = given_col(rng, EDU, softmax(L))
        if edges:
            edu = np.where(edu == EDU[9], EDU[8], edu)
            edu = np.where(np.isin(roles, ['DEV', 'TEST']) & (rng.random(n) < .03), EDU[9], edu)
            gender = np.where(gender == 'Other', 'Prefer not to say', gender)
            gender = np.where((roles == 'TEST') & (rng.random(n) < .02), 'Other', gender)
        er = np.array([EDU_RANK[e] for e in edu])
        p = sigmoid(-.6 + .5 * a + .15 * (er - 3))
        if edges:
            p = np.full(n, .5)                             # hadJob: pure noise
        had = np.where(rng.random(n) < p, 'yes', 'no')
        L = np.tile([2.0, -.2, -1.2, -1.2, -1.5, -1.5, -1.5, -1.5, .2], (n, 1))
        L[:, 8] += 1.5 * (a == 0) - .5 * (a >= 3)
        if not edges:
            L[:, 2:6] += 1.2 * (had == 'yes')[:, None]
        emp = given_col(rng, EMP, softmax(L))
        ctry = np.select([country == 'Lesotho', country == 'Nigeria'], [-.5, -.3], 0.)
        w = .5 * (er - 3) + .2 * a + ctry + rng.normal(0, .8, n)
        cuts = [-2.8, -1.9, -1.1, -.5, 0, .6, 1.2, 1.8, 2.5]
        wi = np.searchsorted(cuts, w)
        li = np.searchsorted(cuts, w - .4 + rng.normal(0, .5, n))
        skipper = rng.random(n) < .03 + .1 * (age == NA)
        wage = np.where(skipper | (rng.random(n) < .01), NA, np.asarray(WAGE)[wi])
        low = np.where(skipper | (rng.random(n) < .01), NA, np.asarray(WAGE)[li])
        return pd.DataFrame({'group': group, 'user.age': age, 'user.gender': gender,
                             'user.country': country, 'user.educationLevel': edu,
                             'user.hadJob': had, 'user.employmentStatus': emp,
                             'user.wageOfSimilarEmployees': wage, 'user.lowestAcceptablePay': low})
    return make_given


# ------------------------------------------------------------------ PREDICT ---

def simulate_factory(edges):
    def simulate(given, rng):
        s = Sim(SCHEMA, given, rng)
        n = s.n
        one = np.ones(n)
        g = lambda c: given[c].to_numpy(dtype=object)                       # noqa: E731
        new = g('user.country') == NA
        fem = (g('user.gender') == 'Female').astype(float)
        male = (g('user.gender') == 'Male').astype(float)
        a = np.array([AGES.index(x) if x in AGES else 1.5 for x in g('user.age')])
        er = np.array([EDU_RANK[e] for e in g('user.educationLevel')], dtype=float)
        ez = (er - 3.5) / 1.5
        emp = g('user.employmentStatus')
        searching = emp == 'Searching for a job'
        grp = g('group')
        any_na = (np.column_stack([g(c) == NA for c in given.columns]).any(axis=1)).astype(float)

        # latent traits
        Z = rng.normal(size=(n, 24))
        pos = .8 * Z[:, 0] + .2 * fem - .35 * ez                                             # acquiescence
        big5 = Z[:, 1:6] + .3 * pos[:, None]
        other = Z[:, 6:11] + .4 * big5[:, [2]] + .3 * pos[:, None]          # gm, pp, EI x3
        riasec = Z[:, 11:17]
        riasec[:, 0] += .6 * male; riasec[:, 3] += .6 * fem; riasec[:, 1] += .4 * ez
        gcog = .6 * ez + .15 * (a <= 1) + .7 * Z[:, 17]
        persev = Z[:, 18] + .3 * big5[:, 2]
        risk = Z[:, 19] + .3 * male
        engage = .7 * Z[:, 20] + .5 * ez - 1.0 * any_na - .5 * new + .3 * searching
        effort = Z[:, 21] + .3 * searching
        optim = Z[:, 22] + .2 * ez
        upsk = Z[:, 23] + .3 * pos

        # monotone dropout through the session: P(reached stage s | engage)
        a_s = np.array([3.5, 3.0, 3.5, 3.5, 3.3, 3.0, 3.0, 3.5, 3.0])
        cont = sigmoid(a_s[None, :] + .8 * engage[:, None] + .3 * ez[:, None])
        p_reach = np.cumprod(cont, axis=1)                                   # (n, 9)
        reached = np.cumprod(rng.random((n, 9)) < cont, axis=1).astype(bool)

        def staged(item, P_ans, stage, skip=.0, shown=None, ans_idx=None, **gate):
            """Answer P_ans if the stage was reached, the item not skipped and the
            module shown; NA (last level) otherwise."""
            opts = s.opts(item)
            assert opts[-1] == NA, item
            p = p_reach[:, stage - 1] * (1 - skip) * (one if shown is None else shown)
            if ans_idx is None:
                ans_idx = draw(P_ans, rng)
            r = reached[:, stage - 1] & (rng.random(n) >= skip) & (
                rng.random(n) < (one if shown is None else shown))
            vals = np.where(r, np.asarray(opts, dtype=object)[ans_idx], NA)
            return s.put(item, with_na(P_ans, p), values=vals, **gate)

        def likert_band(trait, k=4, base=3.3):
            L = np.clip(np.rint(base + .35 * pos[:, None] + .7 * trait[:, None]
                                + rng.normal(0, .8, (n, k))), 1, 5)
            return np.searchsorted([2.5, 3.0, 3.5, 4.0, 4.5], L.mean(1), side='right')

        # ---- pre-assessment survey: gated on the GIVEN employment status ---------
        eg = dict(obey=.94, leak=.04) if edges else {}
        P = ordinal(.35 * a + .3 * (g('user.hadJob') == 'no') + .2 * Z[:, 21], np.linspace(-2.2, 1.8, 7))
        s.put('user.howLongSearchingForJob', P, **eg)
        hrs_pre = ordinal(.9 * effort, [-3.5, -3, -2.5, -2, -1.6, -1.2, 0, .8, 1.5, 2.2, 3])
        s.put('user.howManyHoursSearchedPerWeek', hrs_pre, **eg)
        s.put('user.howManyApplicationsLastMonth',
              ordinal(.8 * effort + .2 * ez, [-2.5, -1.8, -1.2, -.7, -.3, .1, 1.0, 1.8, 2.4, 3, 3.6]), **eg)
        p_yes = sigmoid(.8 + .6 * optim)
        s.put('user.expectedToFindJobInSixMonths',
              np.column_stack([.97 * (1 - p_yes), .97 * p_yes, .03 * one]), **eg)

        def duration(eta):
            fine = ordinal(eta, np.linspace(-2.0, 1.5, 7))                   # 8 fine levels
            coarse = fine[:, :4].sum(1)
            P = np.zeros((n, 9))
            P[:, [0, 1, 2, 3, 5, 6, 7, 8]] = fine
            # the newer platform version offers the coarse 'Under 6 months' instead
            P[new, :4] = 0
            P[new, 4] = coarse[new]
            return P
        s.put('user.howLongUnemployed', duration(.35 * a - .2 * ez), **eg)
        s.put('user.howLongInCurrentPosition', duration(.3 * a - .3), **eg)

        # ---- sectors (25 options), gated on the GIVEN age ------------------------
        code_w = np.array([[1, 0, 0, 0, 0, 0] if c == 'Realistic' else
                           [0, 1, 0, 0, 0, 0] if c == 'Investigative' else
                           [0, 0, 1, 0, 0, 0] if c == 'Enterprising' and i == 1 else
                           [0, 0, 0, 1, 0, 0] if c == 'Social' else
                           [0, 0, 0, 0, 1, 0] if c == 'Enterprising' else
                           [0, 0, 0, 0, 0, 1] for i, c in enumerate(SECTOR_CODE)] + [[0] * 6])
        Ls = (SECTOR_BASE[None, :] * (1.6 if edges else 1.0) + .9 * riasec @ code_w.T
              + male[:, None] * MALE_SECT + fem[:, None] * FEM_SECT + ez[:, None] * HIED_SECT)
        P_pref = softmax(Ls)
        pref_idx = draw(P_pref, rng)
        pref_vals = np.where(rng.random(n) < .02, NA, np.asarray(SECTORS, dtype=object)[pref_idx])
        s.put('user.preferredSector', with_na(P_pref, .98 * one), values=pref_vals)
        P_app = .35 * onehot(pref_idx, 24) + .65 * softmax(Ls * .5 + ENTRY_SECT)
        app_idx = draw(P_app, rng)
        app_vals = np.where(rng.random(n) < .03, NA, np.asarray(SECTORS, dtype=object)[app_idx])
        s.put('user.appliedInThePastSector', with_na(P_app, .97 * one), values=app_vals)

        # ---- self-report scales: derived bands of the mean of 4 Likert items ------
        stage1 = ['sc_nstd_extra', 'sc_nstd_agree', 'sc_nstd_consc', 'sc_nstd_stability', 'sc_nstd_open',
                  'sc_nstd_gm', 'sc_nstd_pp', 'sc_nstd_s_aware', 'sc_nstd_s_manage', 'sc_nstd_soc_aware',
                  'sc_nstd_realistic', 'sc_nstd_invest', 'sc_nstd_artistic', 'sc_nstd_social',
                  'sc_nstd_enterp', 'sc_nstd_convent']
        traits = np.column_stack([big5, other, riasec])
        for j, item in enumerate(stage1):
            b = likert_band(traits[:, j], base=3.0 if j >= 10 else 3.5)
            staged(item, onehot(b, 6), 1, ans_idx=b)

        # ---- timed tasks -----------------------------------------------------------
        P = bands_normal(4.5 + .9 * gcog, .9, [2.5, 3.5, 4.5, 5.5, 6.5])
        staged('sc_nstd_corsi_1', np.column_stack([.02 * one, .98 * P]), 2)
        for item, mu in (('sc_nstd_ds_f_2', 6.3), ('sc_nstd_ds_b_2', 4.8)):
            P = bands_normal(mu + 1.1 * gcog, 1.3 * one, np.arange(2.5, 14, 1.0))
            staged(item, np.column_stack([.015 * one, .985 * P]), 3)
        k = np.arange(11)
        pk = binom.pmf(k[None, :], 10, sigmoid(1.0 * gcog)[:, None])
        P = np.column_stack([pk[:, :3].sum(1), pk[:, 3:8], pk[:, 8:].sum(1)])
        staged('sc_nstd_hmt_1', P, 4)
        staged('sc_nstd_cpt_corrected', bands_normal(78 + 10 * gcog + 5 * big5[:, 2], 12 * one,
                                                     [25.5, 50.5, 75.5, 90.5]), 5)
        staged('sc_nstd_tmt_log_a', bands_normal(4.1 - .25 * gcog, .3 * one, [3.9, 4.3, 4.6]), 6)
        lam = np.exp(-.8 - .4 * gcog)
        pe = np.column_stack([np.exp(-lam), lam * np.exp(-lam), lam ** 2 / 2 * np.exp(-lam)])
        staged('sc_nstd_tmt_err_a', np.column_stack([pe, 1 - pe.sum(1)]), 6)
        staged('sc_nstd_tmt_log_b', bands_normal(4.45 - .3 * gcog, .35 * one, [4.0, 4.4, 4.8]), 6)
        lam = np.exp(-.2 - .4 * gcog)
        pe = np.column_stack([np.exp(-lam), lam * np.exp(-lam), lam ** 2 / 2 * np.exp(-lam)])
        staged('sc_nstd_tmt_err_b', np.column_stack([pe, 1 - pe.sum(1)]), 6)
        if edges:
            xor = new ^ (fem > 0)
            q = np.where(xor, .85, .08)
        else:
            q = sigmoid(-1.2 - .9 * persev)
        staged('sc_nstd_mtpt_quit_1', np.column_stack([1 - q, q]), 7)
        staged('sc_nstd_mtpt_err_per_s', bands_normal(np.log(.18) - .2 * gcog, .5 * one,
                                                      np.log([.1, .2, .3])), 7)
        staged('sc_nstd_bret_prop', bands_normal(.45 + .08 * risk, .12 * one, [.25, .40, .50, .65]), 8)

        # ---- post-assessment survey (stage 9), with arm- and version-specific modules
        feedback = (grp != 'yes4').astype(float)
        report = np.isin(grp, ['yes1', 'yes2', 'Not randomised']).astype(float)
        shown_fb = np.where(feedback > 0, 1.0, .03)
        shown_rep = np.where(report > 0, 1.0, .03)
        shown_new = np.where(new, 1.0, .02)
        cuts5 = [-2.5, -1.5, -.4, .9]
        staged('user.jobStrengthsAndWeaknesses', ordinal(.9 * pos + .3, cuts5), 9, .02, shown_fb)
        staged('user.helpJobSearch', ordinal(.9 * pos + .5, cuts5), 9, .02, shown_fb)
        staged('user.helpGettingJob', ordinal(.9 * pos + .3, cuts5), 9, .02, shown_fb)
        py = sigmoid(.8 + .5 * pos)
        na_app = np.where(searching, .03, .6)
        P = np.column_stack([py * .7, py * .3, (1 - py)]) * (1 - na_app)[:, None]
        staged('user.planToIncreaseJobSearch', np.column_stack([P, na_app]), 9, .02, shown_fb)
        if edges:
            deg = np.isin(g('user.educationLevel'), EDU[6:10])
            s.put_value('user.plansToAttachSkillsReport', np.where(deg, 'yes', 'no'))
        else:
            py = sigmoid(1.0 + .5 * pos)
            staged('user.plansToAttachSkillsReport', np.column_stack([1 - py, py]), 9, .02, shown_rep)
        staged('user.willSkillsAttachHelpGetInterview', ordinal(.9 * pos + .4, cuts5), 9, .02, shown_rep)
        staged('user.targetSector', .6 * onehot(pref_idx, 24) + .4 * P_pref, 9, .02)
        # near-duplicates of pre-survey items
        hrs_post = ordinal(.9 * effort + .4 - .8 * (~searching), [-3.5, -3, -2.5, -2, -1.6, -1.2, 0, .8, 1.5, 2.2, 3])
        staged('user.howManyHoursWillSearchPerWeek', hrs_post, 9, .02)
        staged('user.howManyApplicationsNextMonth',
               ordinal(.8 * effort + .5 - .8 * (~searching), [-2.5, -1.8, -1.2, -.7, -.3, .1, 1.0, 1.8, 2.4, 3, 3.6]), 9, .02)
        pre = s.values['user.expectedToFindJobInSixMonths']
        p_yes = sigmoid(1.0 + .6 * optim)
        P = np.column_stack([1 - p_yes, p_yes])
        P = np.where((pre == 'yes')[:, None], .7 * np.array([0, 1.]) + .3 * P,
                     np.where((pre == 'no')[:, None], .7 * np.array([1., 0]) + .3 * P, P))
        staged('user.expectsToFindJobInSixMonths', P, 9, .02)

        def near_dup(col, width):
            """P over the first `width` bands: 55% the GIVEN answer again, else a neighbour."""
            v = g(col)
            idx = np.array([WAGE.index(x) if x != NA else -1 for x in v])
            P = np.zeros((n, width))
            ok = idx >= 0
            ii = np.clip(idx, 0, width - 1)
            P[np.arange(n)[ok], ii[ok]] += .55
            for d, wgt in ((-1, .15), (1, .2), (-2, .04), (2, .06)):
                jj = np.clip(ii + d, 0, width - 1)
                P[np.arange(n)[ok], jj[ok]] += wgt
            P[ok] /= P[ok].sum(1, keepdims=True)
            P[~ok] = bands_normal(.5 * (er[~ok] - 3) + .2 * a[~ok], 1.0 * one[~ok],
                                  np.linspace(-2.8, 2.5, width - 1))
            return P
        staged('user.wageOfSimilarEmployeesAfter', near_dup('user.wageOfSimilarEmployees', 10), 9, .02)
        staged('user.lowestAcceptablePayAfter', near_dup('user.lowestAcceptablePay', 10), 9, .02)
        pu = softmax(np.column_stack([0 * one, .8 + .3 * upsk, -.3 + .5 * upsk]))
        staged('user.accessedLearningLinks', pu, 9, .02)
        s.put('user.howManyHoursToUpskillPerWeek',
              ordinal(.9 * upsk, [-3, -2.5, -1.8, -1.2, -.8, -.4, .8, 1.6, 2.3, 3, 3.6]))
        Lc = np.column_stack([.3 * one, .4 * one, .5 + .4 * riasec[:, 1], .2 * one, .3 * one, .2 * one,
                              -.5 + .5 * riasec[:, 4], .1 * one, -.2 * one, .3 * one, .4 + .5 * riasec[:, 1],
                              -.8 * one, .2 + .5 * riasec[:, 4], -.3 + .4 * riasec[:, 4],
                              .1 + .4 * riasec[:, 4], -1 * one, -1.2 * one])
        staged('user.plannedCourses', softmax(Lc), 9, .02, shown_new)
        staged('user.helpGetInterview', ordinal(.9 * pos + .5, cuts5), 9, .02, shown_new)
        if edges:
            s.put('user.helpGetJobInDesiredSector', np.tile([0, 0, 0, .02, 0, .98], (n, 1)))
        else:
            staged('user.helpGetJobInDesiredSector', ordinal(.9 * pos + .5, cuts5), 9, .02, shown_new)
        staged('user.reportUsefullness', ordinal(.9 * pos + 1.0, cuts5), 9, .02)
        staged('user.likelyToRecommend', ordinal(.9 * pos + 1.1, cuts5), 9, .02)

        # ---- 6-month tracer: gated on the GIVEN group (exact), ~38% respond -------
        p_resp = sigmoid(-.5 + .3 * engage + .2 * ez)
        resp = rng.random(n) < p_resp

        def tracer(item, P_ans, skip=.03, ans_idx=None):
            opts = s.opts(item)
            p = p_resp * (1 - skip)
            if ans_idx is None:
                ans_idx = draw(P_ans, rng)
            r = resp & (rng.random(n) >= skip)
            vals = np.where(r, np.asarray(opts, dtype=object)[ans_idx], NA)
            return s.put(item, with_na(P_ans, p), values=vals)

        E = [EMP.index(e) for e in emp]
        Lt = np.tile([1.2, -.3, -.2, -.3, -.8, -.8, -.6, -.9, -.2], (n, 1)) + (.4 * ez)[:, None] * np.array(
            [0, 0, 1, .5, 0, 0, .5, 0, 0])
        if edges:
            Lt[:, 2:7] -= 2.0                                        # few employed -> few tr_feel_work rows
        P_emp = .45 * onehot(np.array(E), 9) + .55 * softmax(Lt)
        e_idx = draw(P_emp, rng)
        tr_emp = tracer('tr_employment_status', P_emp, ans_idx=e_idx)
        emp_now = np.isin(np.asarray(EMP, dtype=object)[e_idx], EMPLOYED)
        # job_full: consistent with the employment status 93% of the time
        pj = np.where(emp_now, .93, .07)
        answered_emp = tr_emp != NA
        P_job = np.where(answered_emp[:, None], np.column_stack([1 - pj, pj]), 0)
        # P(job_full | latent) marginalising the employment draw, for the ceiling
        pe_now = (P_emp * np.isin(EMP, EMPLOYED)[None, :]).sum(1)
        pj_marg = .93 * pe_now + .07 * (1 - pe_now)
        p_ans = p_resp * .97
        P_full = np.column_stack([p_ans * (1 - pj_marg), p_ans * pj_marg, 1 - p_ans])
        job = np.where(answered_emp, np.where(rng.random(n) < pj, 'Yes', 'No'), NA)
        s.put('tr_job_full', P_full, values=job)
        del P_job
        s.put('tr_job_number', np.tile([.03, .86, .09, .02], (n, 1)))
        tracer('tr_did_full', np.tile([.7, .1, .2], (n, 1)))
        pf = np.where(grp == 'yes4', .15, .65)
        tracer('tr_feedback_full', np.column_stack([1 - pf, pf]))
        already = np.isin(emp, EMPLOYED)
        jy = s.values['tr_job_full'] == 'Yes'
        P = np.where(jy[:, None], np.where(already[:, None], [.05, .1, .02, .13, .7], [.1, .1, .05, .65, .1]),
                     [.5, .33, .14, .02, .01])
        tracer('tr_feedback_increase_job', P)
        P_tr = .45 * onehot(np.minimum(pref_idx, 22), 23) + .55 * softmax(Ls[:, :23])
        t_idx = draw(P_tr, rng)
        tgt = tracer('tr_target_sector', P_tr, ans_idx=t_idx)
        # RIASEC code of the target sector: a deterministic function of tr_target_sector
        lvl = ['Realistic', 'Investigative', 'Social', 'Enterprising', 'Conventional']
        code = np.array([lvl.index(SECTOR_CODE[i]) for i in range(23)])
        M = onehot(code, 5)                                                   # 23 x 5
        P_code_ans = P_tr @ M
        vals = np.where(tgt == NA, NA, np.asarray(lvl + [NA], dtype=object)[np.where(tgt == NA, 5, code[t_idx])])
        s.put('tr_riasec_target_sector', with_na(P_code_ans, p_resp * .97), values=vals)
        for item, eta in (('tr_help_job_search_full', .8 * pos), ('tr_help_get_job_full', .5 * pos - .8),
                          ('tr_report_help_interview_full', .5 * pos - .5)):
            py = sigmoid(eta)
            tracer(item, np.column_stack([py * .8, (1 - py) * .8, .2 * one]))
        tracer('tr_recommend_full', ordinal(.9 * pos + .8, [-1.0, 0.0]))
        pa = np.where(report > 0, .4, .1)
        tracer('tr_attach_skills_report_full', np.column_stack([1 - pa, pa]))

        def tr_wage(col):
            v = g(col)
            idx = np.array([WAGE.index(x) if x != NA else -1 for x in v])
            ok = idx >= 0
            ii = np.clip(idx - 1, 0, 7)                                       # '0' -> first, 25000+ -> last
            P = np.full((n, 8), 0.0)
            P[np.arange(n)[ok], ii[ok]] += .5
            for d, wgt in ((-1, .2), (1, .3)):
                jj = np.clip(ii + d, 0, 7)
                P[np.arange(n)[ok], jj[ok]] += wgt
            P[~ok] = bands_normal(.5 * (er[~ok] - 3), one[~ok], np.linspace(-2, 2, 7))
            return P
        tracer('tr_similar_wage_after', tr_wage('user.wageOfSimilarEmployees'))
        tracer('tr_low_pay_after', tr_wage('user.lowestAcceptablePay'))
        c12 = [-3.5, -3, -2.5, -2, -1.6, -1.2, 0, .8, 1.5, 2.2, 3]
        tracer('tr_search_hours_after', ordinal(.9 * effort - 1.0 * jy, c12))
        tracer('tr_applications_next_1m', ordinal(.8 * effort - 1.0 * jy + .3, c12))
        tracer('tr_job_offers', ordinal(.5 * optim + .8 * jy, [.3, 1.3, 2.2]))
        tracer('tr_upskill_hours_week', ordinal(.9 * upsk, c12))
        # feelings about work: mean of 8 items (1-4) snapped to the levels the schema lists
        lv = np.array([float(x) for x in IT['tr_feel_work']['values'][:-1]])
        m = np.clip(np.rint(3.3 + .4 * pos[:, None] + rng.normal(0, .7, (n, 8))), 1, 4).mean(1)
        fi = np.abs(m[:, None] - lv[None, :]).argmin(1)
        vals = np.where(rng.random(n) < .05, NA, np.asarray(IT['tr_feel_work']['values'], dtype=object)[fi])
        s.put('tr_feel_work', np.column_stack([.95 * onehot(fi, 11), .05 * one]), values=vals)
        se = np.clip(np.rint(3.3 + .4 * pos[:, None] + rng.normal(0, .6, (n, 5))), 1, 4).mean(1)
        b = np.select([se < 3.39, se < 3.79, se < 3.99], [0, 1, 2], 3)
        tracer('tr_self_efficacy', onehot(b, 4), ans_idx=b)
        return s.values, s.probs
    return simulate


def edges_post_edit(frame, rng):
    vis = (frame['role'] == 'TRAIN').to_numpy()
    m = vis & (frame['user.preferredSector'] == 'Legal').to_numpy()     # unseen option in visible rows
    frame.loc[m, 'user.preferredSector'] = 'Management'
    frame.loc[vis, 'user.helpGetJobInDesiredSector'] = NA                # constant in visible rows
    return frame


if __name__ == '__main__':
    variant = sys.argv[1]
    if variant == 'realistic':
        build('wb_realistic', 'world_bank', make_given_factory(False), simulate_factory(False), seed=303)
    elif variant == 'edges':
        build('wb_edges', 'world_bank', make_given_factory(True), simulate_factory(True), seed=404,
              post_edit=edges_post_edit)
    else:
        raise SystemExit('variant must be realistic or edges')
