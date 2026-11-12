"""unhcr_edge: exact gates; held-out-only GIVEN levels; households seen 3-4 times;
scored in phase 1 and phase 2 shapes (see README)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import unhcr_gen as U
from unhcr_repeats import CFG as REPEATS

CFG = dict(REPEATS, twin_share=0.20, extra_appearances=[(250, 2), (80, 3)],
           heldout_given_levels=[("governorate_col", "Red Sea"), ("governorate_col", "Matrouh"),
                                 ("s2_1_hh_relationship_lbl", "9. A non-household member"),
                                 ("s2_4a_origin_governorate_lbl", "As-Sweida"),
                                 ("s2_1b_age", "[generalised:s2]")])
PLANTED = """
Exact gates. Repeated households: 20% of round-2 rows (807) are re-interviews of a
round-1 household as in unhcr_repeats, plus 250 round-1 households that appear twice more
in round 2 and 80 that appear three more times in round 2 (3 and 4 rows per household;
same copy model from the round-1 interview, independent respondent changes).
GIVEN levels seen only in held-out rows: every row with governorate 'Red Sea' or
'Matrouh', relationship '9. A non-household member', origin 'As-Sweida' or age
'[generalised:s2]' is placed in DEV or TEST (so those one-hot columns are all zero in
TRAIN in phase 1; in phase 2 the DEV ones become visible).
Score it with --phase 1 and --phase 2 (phase 2: TRAIN+DEV visible, TEST scored).
"""

if __name__ == "__main__":
    U.run_builder("unhcr_edge", CFG, seed=105, planted=PLANTED, phases=(1, 2))
