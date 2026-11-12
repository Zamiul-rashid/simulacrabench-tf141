"""Download the TabICL v2 classifier checkpoint that the submission bundles, pinned to a
fixed Hugging Face revision and verified by SHA-256.

  python scripts/fetch_tabicl.py [destination_dir]      (default: submission/)
"""
import hashlib, os, sys, urllib.request

REPO, REVISION = "jingang/TabICL", "4dcd344ece2c00be9e831fdd35bed57b5ad83e19"   # BSD-3-Clause
NAME = "tabicl-classifier-v2-20260212.ckpt"
SHA256 = "bdc7dbd5e4ff21f8f0456fcf90c6b7cdf72dbea960f2d05b19bec19f9b3d4ed0"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


dest = os.path.join(sys.argv[1] if len(sys.argv) > 1 else "submission", NAME)
if os.path.exists(dest) and sha256(dest) == SHA256:
    print("already present and verified:", dest)
    sys.exit(0)
url = "https://huggingface.co/%s/resolve/%s/%s" % (REPO, REVISION, NAME)
print("downloading", url)
urllib.request.urlretrieve(url, dest + ".part")
if sha256(dest + ".part") != SHA256:
    os.remove(dest + ".part")
    sys.exit("checksum mismatch: the download is not the checkpoint used in the submission")
os.replace(dest + ".part", dest)
print("saved and verified:", dest)
