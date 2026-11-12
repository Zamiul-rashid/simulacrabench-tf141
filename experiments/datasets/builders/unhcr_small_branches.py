"""unhcr_small_branches: exact gates, tiny gated branches, a deep item nobody visible
was asked (see README)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import unhcr_gen as U

OVERRIDE = {
    "s3_6_permanent_returns_lbl": {"0.": .965, "1.": .015, "98": .015, "99": .005},
    "s3_9c_returnee_working_lbl": {"1.": .15, "2.": .70, "98": .15},
    "s7a_1_return_destination_lbl": {"1.": .90, "2.": .03, "98": .07},
    "s7a_4_return_alone_lbl": {"0.": .97, "1.": .03},
    "s4_8_worked_pay_lastweek_lbl": {"1.": .97, "2.": .02, "98": .007, "99": .003},
    "s4_9_business_lastweek_lbl": {"1.": .75, "2.": .20, "98": .03, "99": .02},
    "s4_10_family_biz_lastweek_lbl": {"1.": .80, "2.": .15, "98": .03, "99": .02},
    "s3_23_safety_no_concerns_lbl": {"0": .006, "1": .994},
    "s3_15_friend_return_likely_lbl": {"1.": .50, "2.": .006, "3.": .30, "98": .194},
    "s6_10_face_challenges_lbl": {"0.": .985, "1.": .01, "98": .004, "99": .001},
    "s3_2_visited_syria_lbl": {"1.": .01, "2.": .97, "98": .01, "99": .01},
}
CFG = dict(base_override=OVERRIDE, override_shrink=0.05,
           heldout_only_items=["s4_11_job_but_absent_lbl"])
PLANTED = """
Exact gates. Gate parents made rare (base shares in `OVERRIDE`, latent spread on those
parents shrunk to 0.05 so they stay rare), so many gated items have 5-150 asked rows:
s3_6 = Yes 1.5% -> s3_7..s3_9c tiny; s3_9c = Yes 15% of those -> s3_10a/b/c/g/d (depth 4)
nearly empty; s7a_1 = 'another village' 3% -> s7a_2; s7a_4 = Yes 3% -> s7a_5; s4_8 not
'Yes' 3% -> s4_9 -> s4_10 -> s4_11 (depth 4); s3_23 'no concerns' = 0 in 0.6% -> the
10-option rank items s3_23a/b; s3_15 = No 0.6% -> the 8-item s3_17 block; s6_10 = Yes 1% ->
the 13-item s6_11 block; s3_2 = Yes 1% -> s3_3, s3_4a (9 options), s3_4b (14 options).
s4_11 (depth-4 chain end): every row that was asked it is placed in DEV or TEST, so no
visible (TRAIN) row holds a value in phase 1 and the visible column is all NA_GATED.
"""

if __name__ == "__main__":
    U.run_builder("unhcr_small_branches", CFG, seed=104, planted=PLANTED, phases=(1, 2))
