"""Collect package hashes and failure logs without printing signing secrets."""
import glob
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

out = Path("diagnostics")
out.mkdir(exist_ok=True)
files = set()
for pattern in sys.argv[1:]:
    for match in glob.glob(pattern, recursive=True):
        p = Path(match)
        if p.is_dir():
            files.update(f for f in p.rglob("*") if f.is_file() and not f.is_symlink())
        elif p.is_file():
            files.add(p)
with (out / "SHA256SUMS").open("w") as sums:
    for p in sorted(files):
        digest = hashlib.sha256()
        with p.open("rb") as f:
            for block in iter(lambda: f.read(1024 * 1024), b""):
                digest.update(block)
        sums.write(f"{digest.hexdigest()}  {p.as_posix()}\n")
metadata = {key: os.environ.get(key, "") for key in
            ("GITHUB_SHA", "GITHUB_RUN_ID", "GITHUB_JOB", "RUNNER_OS", "RUNNER_ARCH")}
metadata["job_status"] = os.environ.get("CUSTOM_JOB_STATUS", "unknown")
(out / "build.json").write_text(json.dumps(metadata, indent=2))
root = os.environ.get("VCPKG_ROOT")
if root:
    trees = Path(root) / "buildtrees"
    if trees.exists():
        for log in trees.rglob("*.log"):
            dest = out / "vcpkg" / log.relative_to(trees)
            dest.parent.mkdir(parents=True, exist_ok=True)
            with log.open("rb") as source:
                source.seek(max(0, log.stat().st_size - 256 * 1024))
                dest.write_bytes(source.read())
reports = Path.home() / "Library/Logs/DiagnosticReports"
if reports.exists():
    for crash in reports.glob("*RustDesk*"):
        if crash.is_file():
            shutil.copy2(crash, out / crash.name)
