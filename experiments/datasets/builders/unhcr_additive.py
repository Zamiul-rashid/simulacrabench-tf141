"""unhcr_additive: ablation of unhcr_noisygates with the interaction terms switched off
(see README)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import unhcr_gen as U
from unhcr_noisygates import PLANTED as NG

CFG = dict(noisy_gates=True, interact_scale=0.0)
PLANTED = """
ABLATION. Identical to unhcr_noisygates (same seed, same noisy routing) except that the
world's interaction terms are switched off (interact_scale = 0): no country x origin or
country x wave trait effects and no threshold (step) response, so every item's logit is
additive in the one-hot GIVEN columns plus the latent noise (apart from the ordinal link,
the gate products and the hand-coded dependencies). Purpose: does per-question logistic
regression (v1) reach the ceiling when the world is additive, i.e. are the interactions
what separates v1 from flexible models? For reference, noisygates:
""" + NG

if __name__ == "__main__":
    U.run_builder("unhcr_additive", CFG, seed=101, planted=PLANTED)
