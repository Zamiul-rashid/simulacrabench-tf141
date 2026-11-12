# unhcr_noisygates

Fabricated data on the REAL UNHCR schema (items, options, gates and split
counts unchanged). Built by `experiments/datasets/builders/unhcr_noisygates.py` (seed 101) with the
shared generator `unhcr_gen.py`. Roles: random, stratified on wave x country.

## Planted

Noisy routing, no re-interviews. Who holds a value follows `NOISY_ROUTES` in unhcr_gen.py
instead of the declared gate:
- other parent: s7a (return branch) is asked when s3_12 = Yes, or s3_11 = Yes outside Iraq;
  s7b when s3_12 = No, or s3_11 = No in Egypt/Iraq; s7c when s3_11 = DK, or s3_11 = No in
  Lebanon (so the three s3_11 branches overlap and s7a/s7b follow s3_12 more than s3_11);
  s2_9/s2_10 also when the household owns land (Jordan, Lebanon); s6_12 schooling when
  boys OR girls 6-17 > 0 (declared: boys only; a GIVEN parent).
- extra open values: s2_11 also for 'partially damaged and unsafe'; s3_3/s3_4 also for
  s3_2 = DK; s3_7..s3_9c also for s3_6 = DK; s3_17 also for s3_15 = DK; s6_6 also for
  s6_5 = DK.
- country-specific routing: s3_6 asked of everyone in Egypt/Iraq; s3_10* also for
  s3_9c = No in Jordan/Lebanon; s3_16 also for 'friend already returned' in Jordan/Lebanon;
  s4_7 asked of non-working households in Jordan/Lebanon; s4_3..s4_6 also for s4_0 = No in
  Egypt/Lebanon; s6_4 also for s6_3 = 2 in Egypt/Iraq; s6_6 dropped for 35% of Egypt.
- s3_14 asked of everyone (declared s3_11 = No): the lowest agreement.
- s3_23b dropped for 15% (only one concern named).
- every gated item: random leak (asked although the declared parent closed the gate,
  among rows whose declared parent was asked) at U(0, 0.03) and random drop at U(0, 0.05).

## Shared world

Shared answer model ("world", identical in every unhcr_* dataset unless listed
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
.28 / DK .30 at the base).

Config: `{"given_scale": 5, "trait_noise": 0.2, "load_scale": 4, "country_scale": 3, "interact_scale": 1.0, "noisy_gates": true}`

## Measured on the delivered file

- gate agreement (accuracy of declared gate vs holds-a-value, all rows): median 0.866, min 0.325, max 0.999, share < 0.7: 0.32
- fewest asked TRAIN rows: s7a_2_location_known_lbl=265, s7a_6_return_companions_lbl=452, s3_10d_employ_before_return_lbl=627, s3_10c_returnee_age=666, s3_10b_returnee_gender_lbl=670, s3_10g_employ_syria_lbl=675, s3_10a_returnee_is_head_lbl=679, s4_11_job_but_absent_lbl=707, s7a_5_alone_reason_lbl=732, s3_8a_return_year=980, s3_8b_return_month=1005, s3_9b_returned_children=1018
- phase 1 ceiling (Monte Carlo, 1000 draws per hidden row): R=0.760, ceiling_given=0.782, hidden_with_visible_link=0.000, ceiling_given_gated_items=0.780, ceiling_given_ungated_items=0.787, R_share_gated=0.740

`ceiling_given` = skill of the true generating distribution P(answer | GIVEN). `ceiling_given_plus_link` additionally conditions hidden rows that have a visible interview of the same household on that interview's potential answers (including answers to questions it was not routed to), so it is an upper bound.
