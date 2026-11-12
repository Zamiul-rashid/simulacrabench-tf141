"""Score one submission on a list of datasets, one run at a time under a memory cap,
skipping any (submission, dataset, phase) that already has a PASS row in results.csv.

  .venv/bin/python experiments/eval/run_matrix.py <submission_dir> <tag> <dataset[:phase]> ...
"""
import csv, os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sub, tag, jobs = sys.argv[1], sys.argv[2], sys.argv[3:]
name = os.path.basename(sub.rstrip("/"))
def done():
    path = os.path.join(ROOT, "experiments/eval/results.csv")
    return {(r["submission"], r["dataset"], r["phase"]) for r in csv.DictReader(open(path)) if r["status"] == "PASS"} if os.path.exists(path) else set()
for job in jobs:
    ds, _, phase = job.partition(":"); phase = phase or "1"
    if (name, ds, phase) in done():
        print("skip %s on %s phase %s (already scored)" % (name, ds, phase), flush=True); continue
    cmd = ["flock", os.path.join(ROOT, "experiments/eval/.prep.lock"), "systemd-run", "--user", "--scope", "-q",
           "-p", "MemoryMax=8G", "-p", "MemorySwapMax=0", os.path.join(ROOT, ".venv/bin/python"),
           os.path.join(ROOT, "experiments/eval/run.py"), sub, os.path.join(ROOT, "experiments/datasets", ds),
           "--phase", phase, "--tag", tag]
    out = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    lines = [l for l in (out.stdout + out.stderr).splitlines()
             if l.startswith(("SKILL", "FAIL")) or "dropped: [" in l or "Error" in l]
    print("\n".join(l[:200] for l in lines) or "NO OUTPUT for %s on %s (exit %s)" % (name, ds, out.returncode), flush=True)
print("MATRIX_DONE", flush=True)
