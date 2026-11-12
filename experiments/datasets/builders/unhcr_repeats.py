"""unhcr_repeats: exact gates; ~37% of round-2 households are re-interviews (see README)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import unhcr_gen as U

CFG = dict(twin_share=0.37, new_respondent=0.5, stab_household=0.6, stab_attitude=0.3,
           stab_attitude_new=0.15, stab_respondent=0.8, stab_respondent_new=0.1)
PLANTED = """
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
"""

if __name__ == "__main__":
    U.run_builder("unhcr_repeats", CFG, seed=102, planted=PLANTED)
