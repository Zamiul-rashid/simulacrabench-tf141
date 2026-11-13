# unhcr_repeats_fresh

Fabricated data on the REAL UNHCR schema (items, options, gates and split
counts unchanged). Built by `experiments/datasets/builders/unhcr_repeats_fresh.py` (seed 9102) with the
shared generator `unhcr_gen.py`. Roles: random, stratified on wave x country.

## Planted

Exact gates. 37% of the 4,033 round-2 rows (1,492) are re-interviews of a randomly chosen
round-1 household (no key links them):
- household-level GIVEN columns (country, governorate, origin, 8 household counts) equal;
  wave = 2.
- in 50% of re-interviews a different household member answers: relationship, age,
  education, marital status, single parent redrawn (previous relationship avoided);
  otherwise the same respondent (age band moves up by one in 4%).
- answers: each item's potential answer is copied from the round-1 interview with
  probability 0.60 for household-level items (property, documents, visits, returns,
  employment facts, income, assistance, debts, challenges), 0.30 for attitude/opinion items
  (intentions, s7 reasons, friend items, ratings, safety, social cohesion) when the same
  respondent answers and 0.15 when another member answers, and 0.8 / 0.1 for items about
  the respondent as main earner (s4_1, s4_3..s4_6); otherwise drawn fresh from the model
  given the new GIVEN columns. Routing is then applied to the mixed answers.

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

Config: `{"given_scale": 5, "trait_noise": 0.2, "load_scale": 4, "country_scale": 3, "interact_scale": 1.0, "twin_share": 0.37, "new_respondent": 0.5, "stab_household": 0.6, "stab_attitude": 0.3, "stab_attitude_new": 0.15, "stab_respondent": 0.8, "stab_respondent_new": 0.1}`

## Measured on the delivered file

- gate agreement (accuracy of declared gate vs holds-a-value, all rows): median 1.000, min 1.000, max 1.000, share < 0.7: 0.00
- fewest asked TRAIN rows: s3_17_friend_no_ret_safety_lbl=148, s3_17_friend_no_ret_no_econ_lbl=148, s3_17_friend_no_ret_no_education_lbl=148, s3_17_friend_no_ret_no_health_lbl=148, s3_17_friend_no_ret_no_water_lbl=148, s3_17_friend_no_ret_no_electricity_lbl=148, s3_17_friend_no_ret_food_insecurity_lbl=148, s3_17_friend_no_ret_other=148, s7a_2_location_known_lbl=256, s3_10a_returnee_is_head_lbl=280, s3_10b_returnee_gender_lbl=280, s3_10c_returnee_age=280
- re-interviews: n_reinterviews=1492, new_respondent_share=0.501, equal_household_items_where_source_answered=0.888, equal_attitude_items_where_source_answered=0.778, equal_respondent_items_where_source_answered=0.586, equal_all_cells_incl_NA=0.886
- phase 1 ceiling (Monte Carlo, 1000 draws per hidden row): R=0.681, ceiling_given=0.800, hidden_with_visible_link=0.245, ceiling_given_plus_link=0.836, ceiling_given_on_linked_rows=0.663, ceiling_link_on_linked_rows=0.813, ceiling_given_gated_items=0.834, ceiling_given_ungated_items=0.717, R_share_gated=0.710

`ceiling_given` = skill of the true generating distribution P(answer | GIVEN). `ceiling_given_plus_link` additionally conditions hidden rows that have a visible interview of the same household on that interview's potential answers (including answers to questions it was not routed to), so it is an upper bound.
