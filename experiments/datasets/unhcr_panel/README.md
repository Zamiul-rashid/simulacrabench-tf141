# unhcr_panel

Fabricated data on the REAL UNHCR schema (items, options, gates and split
counts unchanged). Built by `experiments/datasets/builders/unhcr_panel.py` (seed 106) with the
shared generator `unhcr_gen.py`. Roles: random, stratified on wave x country.

## Planted

Identical to unhcr_full except that 92% of round-2 rows (3,710 of 4,033) are
re-interviews of round-1 households (tests the hypothesis that the real file is mostly a
panel whose key was removed). For reference, unhcr_full:

Everything in unhcr_noisygates (noisy routing) and unhcr_repeats (37% of round-2 rows are
re-interviews, same stabilities), plus:
- 5% of re-interviews have one child-count column changed by +-1 (household changed, so
  exact matching on all household columns misses them).
- 15 items nearly constant within a country (country effect pattern +-2.5..3.5 on the
  linear predictor, or a dominant option per country for nominal items): s6_6_assist_wfp_lbl, s6_6_assist_unhcr_lbl, s6_6_assist_government_lbl, s4_7_has_work_permit_lbl, s6_1_income_humanitarian_lbl, s6_1_income_government_lbl, s5_10_community_relations_lbl, s3_1_has_valid_docs_lbl, s6_9a_debt_host_country_lbl, s6_11_challenge_eviction_lbl, s6_11_challenge_legal_lbl, s4_16_employment_type_lbl, s5_2_citizen_friends_ratio_lbl, s3_19_origin_comm_freq_lbl, s6_5_assistance_received_lbl.
- governorate effects doubled on every item (sd 0.6) and governorate trait effects x1.5.
- options that appear only in held-out rows (all visible occurrences recoded to the
  item's visible mode, at least 4 held-out rows carry the option): DEV-only (phase 1)
  s5_10 '99. Refused', s3_14 '99. I prefer not to answer', s6_9b '99. Prefer not to
  answer'; TEST-only (phase 2) s4_16 '99. Refused', s3_19 "98. Don't know", s6_10
  '99. Refused'.
- rare options throughout: 97/98/99 codes at 0.5-4% (as in every dataset).

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

Config: `{"given_scale": 5, "trait_noise": 0.2, "load_scale": 4, "country_scale": 3, "interact_scale": 1.0, "twin_share": 0.92, "new_respondent": 0.5, "stab_household": 0.6, "stab_attitude": 0.3, "stab_attitude_new": 0.15, "stab_respondent": 0.8, "stab_respondent_new": 0.1, "noisy_gates": true, "hh_change": 0.05, "country_const_items": ["s6_6_assist_wfp_lbl", "s6_6_assist_unhcr_lbl", "s6_6_assist_government_lbl", "s4_7_has_work_permit_lbl", "s6_1_income_humanitarian_lbl", "s6_1_income_government_lbl", "s5_10_community_relations_lbl", "s3_1_has_valid_docs_lbl", "s6_9a_debt_host_country_lbl", "s6_11_challenge_eviction_lbl", "s6_11_challenge_legal_lbl", "s4_16_employment_type_lbl", "s5_2_citizen_friends_ratio_lbl", "s3_19_origin_comm_freq_lbl", "s6_5_assistance_received_lbl"], "gov_scale": 2.0, "gov_trait_scale": 1.5, "heldout_only_options": [["s5_10_community_relations_lbl", "99.", "DEV"], ["s3_14_visit_importance_lbl", "99.", "DEV"], ["s6_9b_debt_syria_lbl", "99.", "DEV"], ["s4_16_employment_type_lbl", "99.", "TEST"], ["s3_19_origin_comm_freq_lbl", "98.", "TEST"], ["s6_10_face_challenges_lbl", "99.", "TEST"]]}`

## Measured on the delivered file

- gate agreement (accuracy of declared gate vs holds-a-value, all rows): median 0.876, min 0.326, max 0.998, share < 0.7: 0.32
- fewest asked TRAIN rows: s7a_2_location_known_lbl=292, s7a_6_return_companions_lbl=425, s3_10d_employ_before_return_lbl=517, s3_10c_returnee_age=551, s3_10g_employ_syria_lbl=567, s3_10b_returnee_gender_lbl=573, s3_10a_returnee_is_head_lbl=579, s4_11_job_but_absent_lbl=660, s7a_5_alone_reason_lbl=741, s3_8a_return_year=924, s3_9b_returned_children=974, s3_8b_return_month=976
- re-interviews: n_reinterviews=3710, new_respondent_share=0.494, equal_household_items_where_source_answered=0.868, equal_attitude_items_where_source_answered=0.831, equal_respondent_items_where_source_answered=0.641, equal_all_cells_incl_NA=0.86
- options present only in held-out rows (item, option, role, count): [('s5_10_community_relations_lbl', '99. Refused (DO NOT READ ALOUD)', 'DEV', 8), ('s3_14_visit_importance_lbl', '99. I prefer not to answer', 'DEV', 4), ('s6_9b_debt_syria_lbl', '99. Prefer not to answer', 'DEV', 112), ('s4_16_employment_type_lbl', '99. Refused', 'TEST', 4), ('s3_19_origin_comm_freq_lbl', "98. Don't know (DO NOT READ ALOUD)", 'TEST', 50), ('s6_10_face_challenges_lbl', '99. Refused to answer', 'TEST', 39)]
- phase 1 ceiling (Monte Carlo, 1000 draws per hidden row): R=0.780, ceiling_given=0.664, hidden_with_visible_link=0.588, ceiling_given_plus_link=0.740, ceiling_given_on_linked_rows=0.613, ceiling_link_on_linked_rows=0.743, ceiling_given_gated_items=0.671, ceiling_given_ungated_items=0.643, R_share_gated=0.744
- phase 2 ceiling (Monte Carlo, 1000 draws per hidden row): R=0.773, ceiling_given=0.679, hidden_with_visible_link=0.627, ceiling_given_plus_link=0.743, ceiling_given_on_linked_rows=0.640, ceiling_link_on_linked_rows=0.743, ceiling_given_gated_items=0.692, ceiling_given_ungated_items=0.641, R_share_gated=0.745

`ceiling_given` = skill of the true generating distribution P(answer | GIVEN). `ceiling_given_plus_link` additionally conditions hidden rows that have a visible interview of the same household on that interview's potential answers (including answers to questions it was not routed to), so it is an upper bound.
