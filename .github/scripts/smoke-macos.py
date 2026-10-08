"""Cloud-only launch regression for clean and legacy 1x1 window profiles."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

assert os.environ.get("GITHUB_ACTIONS") == "true", "Run this check on GitHub Actions"
app = Path(sys.argv[1]).resolve()
logs = Path("diagnostics")
logs.mkdir(exist_ok=True)
profile = Path.home() / "Library/Preferences/com.carriez.RustDesk"
assert not profile.exists(), "Smoke check requires a clean, disposable CI runner"
helper = logs / "window-list"
subprocess.run(["swiftc", ".github/scripts/window-list.swift", "-o", str(helper)], check=True)

try:
    for case in ("clean", "legacy-1x1"):
        if case == "legacy-1x1":
            local = profile / "RustDesk_local.toml"
            local.parent.mkdir(parents=True, exist_ok=True)
            local.write_text('[ui_flutter]\nwm_Main = \'{"width":1.0,"height":1.0,"offsetWidth":0.0,"offsetHeight":0.0,"isMaximized":false,"isFullscreen":false}\'\n')
        log = (logs / f"launch-{case}.log").resolve()
        process = subprocess.Popen(["open", "-n", "-W", "--stdout", str(log), "--stderr", str(log), str(app)])
        valid = False
        try:
            deadline = time.monotonic() + 60
            snapshots = []
            while time.monotonic() < deadline:
                pids = subprocess.run(["pgrep", "-x", "RustDesk"], capture_output=True, text=True).stdout.split()
                if pids:
                    result = subprocess.run([str(helper.resolve()), *pids], capture_output=True, text=True, check=True)
                    windows = json.loads(result.stdout)
                    snapshots.append(windows)
                    valid = any(w.get("kCGWindowBounds", {}).get("Width", 0) >= 800 and
                                w.get("kCGWindowBounds", {}).get("Height", 0) >= 500 for w in windows)
                    if valid:
                        break
                if process.poll() is not None:
                    break
                time.sleep(2)
            (logs / f"windows-{case}.json").write_text(json.dumps(snapshots, indent=2))
            assert valid, f"No usable main window in {case}; see launch and crash diagnostics"
            print(f"{case}: visible main window confirmed")
        finally:
            subprocess.run(["pkill", "-x", "RustDesk"], check=False)
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.terminate()
                process.wait(timeout=5)
finally:
    reports = Path.home() / "Library/Logs/DiagnosticReports"
    if reports.exists():
        for crash in reports.glob("*RustDesk*"):
            if crash.is_file():
                shutil.copy2(crash, logs / crash.name)
    app_logs = Path.home() / "Library/Logs/RustDesk"
    if app_logs.exists():
        shutil.copytree(app_logs, logs / "app-logs", dirs_exist_ok=True)
