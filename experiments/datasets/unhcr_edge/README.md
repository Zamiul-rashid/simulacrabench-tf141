# unhcr_edge

Fabricated data on the REAL UNHCR schema (items, options, gates and split
counts unchanged). Built by `experiments/datasets/builders/unhcr_edge.py` (seed 105) with the
shared generator `unhcr_gen.py`. Roles: random, stratified on wave x country.

## Planted

Exact gates. Repeated households: 20% of round-2 rows (807) are re-interviews of a
round-1 household as in unhcr_repeats, plus 250 round-1 households that appear twice more
in round 2 and 80 that appear three more times in round 2 (3 and 4 rows per household;
same copy model from the round-1 interview, independent respondent changes).
GIVEN levels seen only in held-out rows: every row with governorate 'Red Sea' or
'Matrouh', relationship '9. A non-household member', origin 'As-Sweida' or age
'[generalised:s2]' is placed in DEV or TEST (so those one-hot columns are all zero in
TRAIN in phase 1; in phase 2 the DEV ones become visible).
Score it with --phase 1 and --phase 2 (phase 2: TRAIN+DEV visible, TEST scored).

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

Config: `{"given_scale": 5, "trait_noise": 0.2, "load_scale": 4, "country_scale": 3, "interact_scale": 1.0, "twin_share": 0.2, "new_respondent": 0.5, "stab_household": 0.6, "stab_attitude": 0.3, "stab_attitude_new": 0.15, "stab_respondent": 0.8, "stab_respondent_new": 0.1, "extra_appearances": [[250, 2], [80, 3]], "heldout_given_levels": [["governorate_col", "Red Sea"], ["governorate_col", "Matrouh"], ["s2_1_hh_relationship_lbl", "9. A non-household member"], ["s2_4a_origin_governorate_lbl", "As-Sweida"], ["s2_1b_age", "[generalised:s2]"]]}`

## Measured on the delivered file

- gate agreement (accuracy of declared gate vs holds-a-value, all rows): median 1.000, min 1.000, max 1.000, share < 0.7: 0.00
- fewest asked TRAIN rows: s3_17_friend_no_ret_safety_lbl=143, s3_17_friend_no_ret_no_econ_lbl=143, s3_17_friend_no_ret_no_education_lbl=143, s3_17_friend_no_ret_no_health_lbl=143, s3_17_friend_no_ret_no_water_lbl=143, s3_17_friend_no_ret_no_electricity_lbl=143, s3_17_friend_no_ret_food_insecurity_lbl=143, s3_17_friend_no_ret_other=143, s7a_2_location_known_lbl=256, s3_10a_returnee_is_head_lbl=339, s3_10b_returnee_gender_lbl=339, s3_10c_returnee_age=339
- re-interviews: n_reinterviews=1547, new_respondent_share=0.487, equal_household_items_where_source_answered=0.881, equal_attitude_items_where_source_answered=0.774, equal_respondent_items_where_source_answered=0.553, equal_all_cells_incl_NA=0.879
- phase 1 ceiling (Monte Carlo, 1000 draws per hidden row): R=0.683, ceiling_given=0.781, hidden_with_visible_link=0.203, ceiling_given_plus_link=0.831, ceiling_given_on_linked_rows=0.522, ceiling_link_on_linked_rows=0.768, ceiling_given_gated_items=0.808, ceiling_given_ungated_items=0.715, R_share_gated=0.711
- phase 2 ceiling (Monte Carlo, 1000 draws per hidden row): R=0.677, ceiling_given=0.776, hidden_with_visible_link=0.217, ceiling_given_plus_link=0.828, ceiling_given_on_linked_rows=0.520, ceiling_link_on_linked_rows=0.756, ceiling_given_gated_items=0.803, ceiling_given_ungated_items=0.712, R_share_gated=0.709

`ceiling_given` = skill of the true generating distribution P(answer | GIVEN). `ceiling_given_plus_link` additionally conditions hidden rows that have a visible interview of the same household on that interview's potential answers (including answers to questions it was not routed to), so it is an upper bound.
