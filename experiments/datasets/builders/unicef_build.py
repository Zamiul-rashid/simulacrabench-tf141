"""Fabricated datasets on the real UNICEF schema (starter-kit/data/unicef.json).

  .venv/bin/python experiments/datasets/builders/unicef_build.py realistic
  .venv/bin/python experiments/datasets/builders/unicef_build.py edges

Writes experiments/datasets/unicef_<variant>/{respondents.parquet, schema.json,
ceiling.json}. See each dataset's README.md for what is planted.
"""
import sys

import numpy as np
import pandas as pd

from unicef_wb_common import Sim, build, given_col, ordinal, sigmoid, softmax

COUNTRIES = ['Brazil', 'Egypt', 'Guatemala', 'Iraq', 'Kenya', 'Mali', 'Nepal', 'Nigeria',
             'Pakistan', 'Zambia']
SHARE = [.10, .08, .09, .10, .11, .09, .10, .12, .11, .10]
AGES = ['18 to 24 years old', '25 - 34 years old', '35 - 44 years old', '45 and above']
RELIG = ['Buddhist', 'Christian', 'Hindu', 'Jewish', 'Muslim', 'Traditional religions',
         'Not religious', 'Other', "Baha'i", 'Sikh']
#            Bud   Chr   Hin   Jew   Mus   Trad  NotR  Oth   Bah   Sikh
RELIG_BY_COUNTRY = np.array([
    [.003, .80, .002, .002, .003, .02, .13, .035, .003, .002],   # Brazil
    [.000, .09, .000, .001, .90, .000, .006, .002, .001, .000],  # Egypt
    [.002, .88, .001, .001, .002, .04, .06, .014, .000, .000],   # Guatemala
    [.000, .03, .000, .001, .95, .000, .01, .006, .002, .001],   # Iraq
    [.001, .84, .006, .000, .10, .03, .015, .006, .001, .001],   # Kenya
    [.000, .03, .000, .000, .92, .04, .006, .004, .000, .000],   # Mali
    [.10, .02, .81, .000, .04, .01, .01, .008, .001, .001],      # Nepal
    [.000, .50, .000, .000, .46, .03, .005, .005, .000, .000],   # Nigeria
    [.000, .02, .01, .000, .96, .000, .003, .004, .001, .002],   # Pakistan
    [.001, .95, .003, .000, .01, .02, .01, .005, .001, .000],    # Zambia
])
RELIG_BY_COUNTRY /= RELIG_BY_COUNTRY.sum(1, keepdims=True)
Q08_INTERCEPT = np.array([1.7, .6, .9, 0.0, -.4, -1.0, 1.2, -.8, .4, -.7])
T1_COUNTRY = np.array([.6, .2, .3, -.2, -.1, -.6, .5, -.5, 0., -.4])
T2_COUNTRY = np.array([-.5, .3, 0., .4, .1, .6, -.2, .5, .7, .2])


def ci(given):
    return np.array([COUNTRIES.index(c) for c in given["Country"]])


def age_idx(given):
    """0..3, and 1.5 (neutral) where age was not asked (Egypt)."""
    lut = {a: i for i, a in enumerate(AGES)}
    return np.array([lut.get(a, 1.5) for a in given["Q01"]])


# ---------------------------------------------------------------- GIVEN -------

def make_given_factory(edges):
    def make_given(n, roles, rng):
        country = given_col(rng, COUNTRIES, SHARE, n)
        c = np.array([COUNTRIES.index(x) for x in country])
        young = np.isin(c, [4, 5, 7, 8, 9])
        P_age = np.where(young[:, None], [.30, .33, .20, .17], [.18, .28, .24, .30])
        q01 = given_col(rng, AGES, P_age)
        q01 = np.where(country == 'Egypt', 'NA_GATED', q01)            # exact GIVEN gate
        fem = np.array([.52, .40, .50, .38, .50, .45, .48, .45, .35, .50])[c]
        pna = np.where(c == 0, .03, .01)
        if edges:
            fem = np.full(n, .5)
        q02 = given_col(rng, ['Female', 'Male', 'Prefer not to answer'],
                        np.column_stack([fem * (1 - pna), (1 - fem) * (1 - pna), pna]))
        urb = np.array([.8, .55, .5, .7, .35, .35, .3, .5, .4, .45])[c]
        if edges:
            urb = np.full(n, .5)                                          # pure noise column
        q03 = given_col(rng, ['Rural', 'Urban'], np.column_stack([1 - urb, urb]))
        q05 = given_col(rng, RELIG, RELIG_BY_COUNTRY[c])
        if edges:
            # never seen in the phase-1 visible rows: Jewish only in DEV/TEST, Sikh only in TEST
            q05 = np.where(np.isin(q05, ['Jewish', 'Sikh']), 'Other', q05)
            held = np.isin(roles, ['DEV', 'TEST'])
            q05 = np.where(held & (rng.random(n) < .025), 'Jewish', q05)
            q05 = np.where((roles == 'TEST') & (rng.random(n) < .02), 'Sikh', q05)
        role_p = np.where((q05 == 'Not religious')[:, None], [.01, .14, .85], [.12, .78, .10])
        if edges:
            role_p = np.where((q05 == 'Not religious')[:, None], [.05, .45, .50], [.20, .50, .30])
        q04 = given_col(rng, ['Religious leader', 'Member of religious community',
                              'Not part of any religious community'], role_p)
        a = np.array([{x: i for i, x in enumerate(AGES)}.get(v, 1.5) for v in q01])
        lg = (np.array([-.8, -.2, -.2, -.2, 0., .4, -.4, .2, 0., .2])[c]
              + np.select([a == 0, a == 1, a == 2, a == 3], [-.3, .5, .3, -1.2], 0.)
              + .1 * (q02 == 'Female'))
        p13 = sigmoid(lg)
        if edges:
            p13 = np.full(n, .04)                                         # few asked rows
        q13 = given_col(rng, ['Yes', 'No'], np.column_stack([p13, 1 - p13]))
        return pd.DataFrame({'Country': country, 'Q01': q01, 'Q02': q02, 'Q03': q03,
                             'Q04': q04, 'Q05': q05, 'Q13': q13})
    return make_given


# ---------------------------------------------------------------- PREDICT -----

# fixed random effects (country x option) per item, drawn once from their own stream
_FX = np.random.default_rng(20261111)
COUNTRY_FX = {item: _FX.normal(scale=1.5 * s, size=(10, w)) for item, s, w in [
    ('Q06', .5, 5), ('Q07', .7, 3), ('Q09', .5, 3), ('Q10', .6, 7), ('Q11', .5, 5),
    ('Q12', .5, 8), ('Q14', .4, 1), ('Q15', .5, 5), ('Q16', .3, 3), ('Q17', .5, 5), ('Q18', .4, 4)]}
AGE_SLOPE = _FX.normal(scale=.35, size=10)          # country x age interaction on Q08
FEM_FX = _FX.normal(scale=.5, size=(10, 5))          # country x gender interaction on Q11


def simulate_factory(edges):
    def simulate(given, rng):
        s = Sim(SCHEMA, given, rng)
        n, c, a = s.n, ci(given), age_idx(given)
        fem = s.is_('Q02', 'Female').astype(float)
        urban = s.is_('Q03', 'Urban').astype(float) * (0.0 if edges else 1.0)
        leader = s.is_('Q04', 'Religious leader').astype(float)
        notpart = s.is_('Q04', 'Not part of any religious community').astype(float)

        # three correlated latent traits whose means depend on country and demographics
        cov = .40 * np.array([[1, .3, .5], [.3, 1, .2], [.5, .2, 1]])
        eps = rng.multivariate_normal(np.zeros(3), cov, size=n)
        nig_pak = np.isin(c, [7, 8]).astype(float)
        T1 = T1_COUNTRY[c] + .3 * leader + .15 * (a - 1.5) + urban * (.3 + .5 * nig_pak) + eps[:, 0]
        T2 = (T2_COUNTRY[c] + .6 * leader - .8 * notpart
              + fem * np.where(np.isin(c, [3, 5, 8]), .4, -.2) + eps[:, 1])
        T3 = .5 * T1_COUNTRY[c] + .3 + .2 * leader + eps[:, 2]
        one = np.ones(n)

        L = np.column_stack([.2 + 1.2 * T2 + .8 * leader, -1.0 * T2, -.8 * one, -3.5 * one,
                             np.where(np.isin(c, [5, 7]), -3.2, -6.0)]) + COUNTRY_FX['Q06'][c]
        s.put('Q06', softmax(L))

        if edges:
            s.put('Q07', np.tile([.99, .0, .01], (n, 1)))                # constant in visible rows
        else:
            L = np.column_stack([.8 + .8 * T1 + .6 * T2, -.3 - .5 * T1, 0 * one]) + COUNTRY_FX['Q07'][c]
            s.put('Q07', softmax(L))

        if edges:
            xor = (fem > 0) ^ s.is_('Q04', 'Member of religious community')
            lg = np.where(xor, 2.2, -2.2) + .6 * T1
        else:
            lg = Q08_INTERCEPT[c] + 1.3 * T1 + AGE_SLOPE[c] * (a - 1.5) + .3 * urban
        p = sigmoid(lg)
        s.put('Q08', np.column_stack([p, 1 - p]))

        gate = dict(obey=.96, leak=.03) if edges else {}
        L = np.column_stack([.3 + .9 * T1, -.2 - .8 * T1 + .3 * T2, 0 * one]) + COUNTRY_FX['Q09'][c]
        s.put('Q09', softmax(L), **gate)
        L = np.column_stack([.8 - .3 * T1, -.4 * T1, -.2 * one, -.3 * one + .2 * urban,
                             -1.2 + .9 * T2, -2.0 + 1.0 * T2, -1.5 * one]) + COUNTRY_FX['Q10'][c]
        s.put('Q10', softmax(L), **gate)

        L = (np.column_stack([1.2 + .3 * T1, -.8 + 1.0 * T2 + 1.0 * leader, .2 * one, -.6 * one, -1.5 * one])
             + COUNTRY_FX['Q11'][c] + fem[:, None] * FEM_FX[c])
        s.put('Q11', softmax(L))

        if edges:
            f = {'Buddhist': 'Doing my part to protect my community',
                 'Christian': 'Clear information on vaccine safety and side effects',
                 'Hindu': 'Government guidance', 'Jewish': 'Public statements by influential persons',
                 'Muslim': 'Seeing religious leaders lead by example through taking the vaccine publicly',
                 'Traditional religions': 'Strong recommendation from the persons I trust most',
                 'Not religious': 'Social media or traditional media', 'Other': 'Other',
                 "Baha'i": 'Doing my part to protect my community', 'Sikh': 'Government guidance'}
            s.put_value('Q12', [f[v] for v in s.values['Q05']])        # determined by a GIVEN column
        else:
            L = np.column_stack([1.0 * one, .2 * one, -.6 + .8 * T2, -.7 * one, -.2 + .3 * T1,
                                 -.8 + .5 * urban, .1 + .3 * T1, -2 * one]) + COUNTRY_FX['Q12'][c]
            s.put('Q12', softmax(L))

        # child battery, gated on the GIVEN Q13 (exact)
        ns = sigmoid(-3 - .5 * T3)
        P = ordinal(-(1.5 * T3 + COUNTRY_FX['Q14'][c, 0]), [.9, 3.0])
        s.put('Q14', np.column_stack([P * (1 - ns)[:, None], ns]))
        L = np.column_stack([1.3 * one, -1 + .9 * T2, .3 * one, -1.2 * one, -2 * one]) + COUNTRY_FX['Q15'][c]
        s.put('Q15', softmax(L))
        L = np.column_stack([2.0 + .8 * T3, -.3 - .5 * T3, 0 * one]) + COUNTRY_FX['Q16'][c]
        s.put('Q16', softmax(L))
        L = np.column_stack([.8 + .7 * T3 + .4 * T2, -.5 - .5 * T3, -.4 * one, -.2 * one,
                             np.where(c == 8, -3.0, -4.5)]) + COUNTRY_FX['Q17'][c]
        s.put('Q17', softmax(L))
        L = np.column_stack([.6 + .8 * T3 + .5 * T2, -1.6 - .6 * T3, .4 - .6 * T2, -.6 * one]) + COUNTRY_FX['Q18'][c]
        s.put('Q18', softmax(L))
        return s.values, s.probs
    return simulate


def edges_post_edit(frame, rng):
    vis = (frame['role'] == 'TRAIN').to_numpy()
    # an option present in held-out rows but never in the phase-1 visible rows
    rel = 'Goes against my religious belief'
    m = vis & (frame['Q10'] == rel).to_numpy()
    frame.loc[m, 'Q10'] = 'Other'
    # an item constant in the phase-1 visible rows
    frame.loc[vis, 'Q07'] = 'Yes'
    return frame


import unicef_wb_common as C  # noqa: E402
SCHEMA = C.load_real_schema('unicef')

if __name__ == '__main__':
    variant = sys.argv[1]
    if variant == 'realistic':
        build('unicef_realistic', 'unicef', make_given_factory(False), simulate_factory(False),
              seed=101)
    elif variant == 'edges':
        build('unicef_edges', 'unicef', make_given_factory(True), simulate_factory(True),
              seed=202, post_edit=edges_post_edit)
    else:
        raise SystemExit('variant must be realistic or edges')
