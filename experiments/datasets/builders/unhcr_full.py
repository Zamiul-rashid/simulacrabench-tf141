"""unhcr_full: noisy gates + re-interviews + country/governorate effects + rare and
held-out-only options (see README)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import unhcr_gen as U
from unhcr_repeats import CFG as REPEATS

CONST = ["s6_6_assist_wfp_lbl", "s6_6_assist_unhcr_lbl", "s6_6_assist_government_lbl",
         "s4_7_has_work_permit_lbl", "s6_1_income_humanitarian_lbl",
         "s6_1_income_government_lbl", "s5_10_community_relations_lbl",
         "s3_1_has_valid_docs_lbl", "s6_9a_debt_host_country_lbl", "s6_11_challenge_eviction_lbl",
         "s6_11_challenge_legal_lbl", "s4_16_employment_type_lbl",
         "s5_2_citizen_friends_ratio_lbl", "s3_19_origin_comm_freq_lbl",
         "s6_5_assistance_received_lbl"]
HELDOUT_OPTS = [("s5_10_community_relations_lbl", "99.", "DEV"),
                ("s3_14_visit_importance_lbl", "99.", "DEV"),
                ("s6_9b_debt_syria_lbl", "99.", "DEV"),
                ("s4_16_employment_type_lbl", "99.", "TEST"),
                ("s3_19_origin_comm_freq_lbl", "98.", "TEST"),
                ("s6_10_face_challenges_lbl", "99.", "TEST")]
CFG = dict(REPEATS, noisy_gates=True, hh_change=0.05, country_const_items=CONST, gov_scale=2.0,
           gov_trait_scale=1.5, heldout_only_options=HELDOUT_OPTS)
PLANTED = """
Everything in unhcr_noisygates (noisy routing) and unhcr_repeats (37% of round-2 rows are
re-interviews, same stabilities), plus:
- 5% of re-interviews have one child-count column changed by +-1 (household changed, so
  exact matching on all household columns misses them).
- 15 items nearly constant within a country (country effect pattern +-2.5..3.5 on the
  linear predictor, or a dominant option per country for nominal items): CONST_LIST.
- governorate effects doubled on every item (sd 0.6) and governorate trait effects x1.5.
- options that appear only in held-out rows (all visible occurrences recoded to the
  item's visible mode, at least 4 held-out rows carry the option): DEV-only (phase 1)
  s5_10 '99. Refused', s3_14 '99. I prefer not to answer', s6_9b '99. Prefer not to
  answer'; TEST-only (phase 2) s4_16 '99. Refused', s3_19 "98. Don't know", s6_10
  '99. Refused'.
- rare options throughout: 97/98/99 codes at 0.5-4% (as in every dataset).
""".replace("CONST_LIST", ", ".join(CONST))

if __name__ == "__main__":
    U.run_builder("unhcr_full", CFG, seed=103, planted=PLANTED, phases=(1, 2))
