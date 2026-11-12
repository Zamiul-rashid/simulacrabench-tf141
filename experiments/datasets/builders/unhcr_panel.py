"""unhcr_panel: unhcr_full with nearly every round-2 row a re-interview (see README)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import unhcr_gen as U
from unhcr_full import CFG as FULL, PLANTED as FULL_PLANTED

CFG = dict(FULL, twin_share=0.92)
PLANTED = """
Identical to unhcr_full except that 92% of round-2 rows (3,710 of 4,033) are
re-interviews of round-1 households (tests the hypothesis that the real file is mostly a
panel whose key was removed). For reference, unhcr_full:
""" + FULL_PLANTED

if __name__ == "__main__":
    U.run_builder("unhcr_panel", CFG, seed=106, planted=PLANTED, phases=(1, 2))
