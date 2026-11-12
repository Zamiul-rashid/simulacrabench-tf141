# unhcr_small_branches

Fabricated data on the REAL UNHCR schema (items, options, gates and split
counts unchanged). Built by `experiments/datasets/builders/unhcr_small_branches.py` (seed 104) with the
shared generator `unhcr_gen.py`. Roles: random, stratified on wave x country.

## Planted

Exact gates. Gate parents made rare (base shares in `OVERRIDE`, latent spread on those
parents shrunk to 0.05 so they stay rare), so many gated items have 5-150 asked rows:
s3_6 = Yes 1.5% -> s3_7..s3_9c tiny; s3_9c = Yes 15% of those -> s3_10a/b/c/g/d (depth 4)
nearly empty; s7a_1 = 'another village' 3% -> s7a_2; s7a_4 = Yes 3% -> s7a_5; s4_8 not
'Yes' 3% -> s4_9 -> s4_10 -> s4_11 (depth 4); s3_23 'no concerns' = 0 in 0.6% -> the
10-option rank items s3_23a/b; s3_15 = No 0.6% -> the 8-item s3_17 block; s6_10 = Yes 1% ->
the 13-item s6_11 block; s3_2 = Yes 1% -> s3_3, s3_4a (9 options), s3_4b (14 options).
s4_11 (depth-4 chain end): every row that was asked it is placed in DEV or TEST, so no
visible (TRAIN) row holds a value in phase 1 and the visible column is all NA_GATED.

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

Config: `{"given_scale": 5, "trait_noise": 0.2, "load_scale": 4, "country_scale": 3, "interact_scale": 1.0, "base_override": {"s3_6_permanent_returns_lbl": {"0.": 0.965, "1.": 0.015, "98": 0.015, "99": 0.005}, "s3_9c_returnee_working_lbl": {"1.": 0.15, "2.": 0.7, "98": 0.15}, "s7a_1_return_destination_lbl": {"1.": 0.9, "2.": 0.03, "98": 0.07}, "s7a_4_return_alone_lbl": {"0.": 0.97, "1.": 0.03}, "s4_8_worked_pay_lastweek_lbl": {"1.": 0.97, "2.": 0.02, "98": 0.007, "99": 0.003}, "s4_9_business_lastweek_lbl": {"1.": 0.75, "2.": 0.2, "98": 0.03, "99": 0.02}, "s4_10_family_biz_lastweek_lbl": {"1.": 0.8, "2.": 0.15, "98": 0.03, "99": 0.02}, "s3_23_safety_no_concerns_lbl": {"0": 0.006, "1": 0.994}, "s3_15_friend_return_likely_lbl": {"1.": 0.5, "2.": 0.006, "3.": 0.3, "98": 0.194}, "s6_10_face_challenges_lbl": {"0.": 0.985, "1.": 0.01, "98": 0.004, "99": 0.001}, "s3_2_visited_syria_lbl": {"1.": 0.01, "2.": 0.97, "98": 0.01, "99": 0.01}}, "override_shrink": 0.05, "heldout_only_items": ["s4_11_job_but_absent_lbl"]}`

## Measured on the delivered file

- gate agreement (accuracy of declared gate vs holds-a-value, all rows): median 1.000, min 1.000, max 1.000, share < 0.7: 0.00
- fewest asked TRAIN rows: s4_11_job_but_absent_lbl=0, s3_10a_returnee_is_head_lbl=15, s3_10b_returnee_gender_lbl=15, s3_10c_returnee_age=15, s3_10d_employ_before_return_lbl=15, s3_10g_employ_syria_lbl=15, s7a_2_location_known_lbl=37, s3_17_friend_no_ret_safety_lbl=43, s3_17_friend_no_ret_no_econ_lbl=43, s3_17_friend_no_ret_no_education_lbl=43, s3_17_friend_no_ret_no_health_lbl=43, s3_17_friend_no_ret_no_water_lbl=43
- phase 1 ceiling (Monte Carlo, 1000 draws per hidden row): R=0.596, ceiling_given=0.809, hidden_with_visible_link=0.000, ceiling_given_gated_items=0.833, ceiling_given_ungated_items=0.755, R_share_gated=0.700
- phase 2 ceiling (Monte Carlo, 1000 draws per hidden row): R=0.592, ceiling_given=0.791, hidden_with_visible_link=0.000, ceiling_given_gated_items=0.811, ceiling_given_ungated_items=0.743, R_share_gated=0.700

`ceiling_given` = skill of the true generating distribution P(answer | GIVEN). `ceiling_given_plus_link` additionally conditions hidden rows that have a visible interview of the same household on that interview's potential answers (including answers to questions it was not routed to), so it is an upper bound.
