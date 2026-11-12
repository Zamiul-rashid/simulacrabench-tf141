#!/usr/bin/env bash
# Rebuild the exact archive uploaded to the SimulacraBench test phase.
#   bash scripts/build_zip.sh            -> tf141_submission.zip in the repo root
set -euo pipefail
cd "$(dirname "$0")/.."
python scripts/fetch_tabicl.py submission
rm -f tf141_submission.zip
(cd submission && zip -q ../tf141_submission.zip main.py requirements.txt tabicl-classifier-v2-20260212.ckpt)
echo "built tf141_submission.zip"
sha256sum submission/main.py submission/requirements.txt
