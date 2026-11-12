"""unhcr_noisygates: declared gates obeyed only partially (see README)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import unhcr_gen as U

PLANTED = """
Noisy routing, no re-interviews. Who holds a value follows `NOISY_ROUTES` in unhcr_gen.py
instead of the declared gate:
- other parent: s7a (return branch) is asked when s3_12 = Yes, or s3_11 = Yes outside Iraq;
  s7b when s3_12 = No, or s3_11 = No in Egypt/Iraq; s7c when s3_11 = DK, or s3_11 = No in
  Lebanon (so the three s3_11 branches overlap and s7a/s7b follow s3_12 more than s3_11);
  s2_9/s2_10 also when the household owns land (Jordan, Lebanon); s6_12 schooling when
  boys OR girls 6-17 > 0 (declared: boys only; a GIVEN parent).
- extra open values: s2_11 also for 'partially damaged and unsafe'; s3_3/s3_4 also for
  s3_2 = DK; s3_7..s3_9c also for s3_6 = DK; s3_17 also for s3_15 = DK; s6_6 also for
  s6_5 = DK.
- country-specific routing: s3_6 asked of everyone in Egypt/Iraq; s3_10* also for
  s3_9c = No in Jordan/Lebanon; s3_16 also for 'friend already returned' in Jordan/Lebanon;
  s4_7 asked of non-working households in Jordan/Lebanon; s4_3..s4_6 also for s4_0 = No in
  Egypt/Lebanon; s6_4 also for s6_3 = 2 in Egypt/Iraq; s6_6 dropped for 35% of Egypt.
- s3_14 asked of everyone (declared s3_11 = No): the lowest agreement.
- s3_23b dropped for 15% (only one concern named).
- every gated item: random leak (asked although the declared parent closed the gate,
  among rows whose declared parent was asked) at U(0, 0.03) and random drop at U(0, 0.05).
"""

if __name__ == "__main__":
    U.run_builder("unhcr_noisygates", dict(noisy_gates=True), seed=101, planted=PLANTED)
