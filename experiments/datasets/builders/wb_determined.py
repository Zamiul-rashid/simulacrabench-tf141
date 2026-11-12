"""wb_determined: wb_realistic with module availability made EXACTLY determined by GIVEN cells.

Hypothesis planted (from the public SkillCraft documentation: arms T1 full feedback, T2 skills
only, T3 career interests & job matches only, T4 no feedback / scores only; platform rollout):
an app either shows a screen or it does not, so "Not answered" caused by the arm or the platform
version is 100% determined, not 97-99% as in wb_realistic. Everything else (respondents, roles,
answers of everyone else) is copied unchanged from wb_realistic.

  arm yes4 (no feedback, scores only)     -> post-feedback items 'Not answered'
  arms yes3, yes4 (no skills feedback)    -> skills-report items, learning links, courses
                                             'Not answered'; upskill hours NA_GATED
  arms yes2, yes4 (no job matches)        -> user.targetSector 'Not answered'
  country recorded (old platform version) -> courses module 'Not answered' (as before, now 100%)
                                             and the last two games (mirror tracing, BRET)
                                             'Not answered' (new: the old version lacked them)

usage: .venv/bin/python experiments/datasets/builders/wb_determined.py
"""
import json
import os
import shutil

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SRC = os.path.join(ROOT, "experiments", "datasets", "wb_realistic")
DST = os.path.join(ROOT, "experiments", "datasets", "wb_determined")
NA, GATED = "Not answered", "NA_GATED"

POST_FEEDBACK = ["user.jobStrengthsAndWeaknesses", "user.helpJobSearch", "user.helpGettingJob",
                 "user.planToIncreaseJobSearch"]
SKILLS_REPORT = ["user.plansToAttachSkillsReport", "user.willSkillsAttachHelpGetInterview"]
LEARNING = ["user.accessedLearningLinks", "user.plannedCourses", "user.helpGetInterview",
            "user.helpGetJobInDesiredSector"]
COURSES = ["user.plannedCourses", "user.helpGetInterview", "user.helpGetJobInDesiredSector"]
LATE_GAMES = ["sc_nstd_mtpt_quit_1", "sc_nstd_mtpt_err_per_s", "sc_nstd_bret_prop"]


def main():
    df = pd.read_parquet(os.path.join(SRC, "respondents.parquet"))
    schema = json.load(open(os.path.join(SRC, "schema.json")))
    before = df.copy()
    g = df["group"]
    old = df["user.country"] != NA
    df.loc[g == "yes4", POST_FEEDBACK] = NA
    df.loc[g.isin(["yes3", "yes4"]), SKILLS_REPORT + LEARNING] = NA
    df.loc[g.isin(["yes3", "yes4"]), "user.howManyHoursToUpskillPerWeek"] = GATED
    df.loc[g.isin(["yes2", "yes4"]), "user.targetSector"] = NA
    df.loc[old, COURSES + LATE_GAMES] = NA
    # keep the schema gate of the upskill item consistent with its parent
    asked = df["user.accessedLearningLinks"].isin(["yes", "plan to"])
    bad = ~asked & (df["user.howManyHoursToUpskillPerWeek"] != GATED)
    df.loc[bad, "user.howManyHoursToUpskillPerWeek"] = GATED
    for t, v in schema["items"].items():                         # sanity: every value legal
        if v["class"] in ("GIVEN", "PREDICT"):
            legal = set(v["values"]) | ({GATED} if v.get("gate") else set())
            assert set(df[t].unique()) <= legal, t
    os.makedirs(DST, exist_ok=True)
    df.to_parquet(os.path.join(DST, "respondents.parquet"), index=False)
    shutil.copy(os.path.join(SRC, "schema.json"), os.path.join(DST, "schema.json"))
    changed = (df != before).sum()
    changed = changed[changed > 0]
    with open(os.path.join(DST, "README.md"), "w") as fh:
        fh.write("# wb_determined\n\n"
                 "`wb_realistic` (same respondents, same roles, same schema) with module availability made "
                 "**exactly** determined by GIVEN cells. Builder: `builders/wb_determined.py` (deterministic "
                 "post-edit of wb_realistic, no randomness).\n\n"
                 "- arm `yes4` (no feedback, scores only): post-feedback items %s all 'Not answered'.\n"
                 "- arms `yes3`, `yes4` (no skills feedback): %s all 'Not answered'; "
                 "`user.howManyHoursToUpskillPerWeek` NA_GATED.\n"
                 "- arms `yes2`, `yes4` (no job matches): `user.targetSector` 'Not answered'.\n"
                 "- `user.country` recorded (old platform version): %s all 'Not answered' (courses module "
                 "absent; mirror tracing and BRET games absent).\n\n"
                 "Purpose: test whether predictions are sharp enough in cells the visible rows show to be "
                 "100%% determined (e.g. a generic pure-cell rule, see experiments/wb_ideas/). "
                 "No ceiling.json (not recomputed).\n\nCells changed per column vs wb_realistic:\n\n%s\n"
                 % (POST_FEEDBACK, SKILLS_REPORT + LEARNING, COURSES + LATE_GAMES,
                    changed.to_string()))
    print(changed.to_string())


if __name__ == "__main__":
    main()
