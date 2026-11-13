"""unhcr_repeats_fresh: unhcr_repeats' configuration with a new seed (9102), built after the
design was frozen, so it was never used for any design decision (held-out check for the paper)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import unhcr_gen as U
from unhcr_repeats import CFG, PLANTED

if __name__ == "__main__":
    U.run_builder("unhcr_repeats_fresh", CFG, seed=9102, planted=PLANTED)
