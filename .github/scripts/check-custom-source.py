"""Cloud migration contract check; runtime credentials are tested separately in Rust."""
from pathlib import Path
import json
import re
import subprocess

assert re.search(r'^version = "1\.5\.0"$', Path("Cargo.toml").read_text(), re.M)
shared = subprocess.check_output(["git", "ls-tree", "HEAD", "libs/hbb_common"], text=True)
assert "229b904508364c8997aad0fb5af57effac859f60" in shared
assert subprocess.check_output(["git", "hash-object", "src/ui_interface.rs"], text=True).strip() == "b1eeefde2e6a1fa76719766ff4ea8594b90aa61f", "Official ID and permissions interface changed"
defaults = Path("src/custom_defaults.rs").read_text()
assert "www.dsecret.com:21106" in defaults
assert "jA+pdkA5sIUOGG2YivcS6KWuLR6lEi9hvzk+aWis7lk=" in defaults
tabs = Path("flutter/lib/models/peer_tab_model.dart").read_text()
names = re.search(r'tabNames = \[(.*?)\];', tabs, re.S).group(1)
assert re.findall(r"'([^']+)'", names)[:3] == ["Recent sessions", "Favorites", "Discovered"]
assert "maxTabCount = isDesktop ? 3 : 5" in tabs
assert "if (!isDesktop) 'Address book'" in names and "if (!isDesktop) 'Accessible devices'" in names
home = Path("flutter/lib/desktop/pages/desktop_home_page.dart").read_text()
assert "大狸子远程控制" in home
assert "RxBool editHover" not in home
assert "Icons.refresh" in home
settings = Path("flutter/lib/desktop/pages/desktop_setting_page.dart").read_text()
assert "if (!bind.isDisableAccount()) SettingsTabKey.account," not in settings
assert "setup_server_tip" not in Path("flutter/lib/desktop/pages/connection_page.dart").read_text()
common = Path("flutter/lib/common.dart").read_text()
assert "is_start && isWindows && !bind.mainIsInstalled()" in common
assert "await callMainCheckSuperUserPermission()" in common
assert "restoreWidth <= minWidth" in common and "restoreHeight <= minHeight" in common
out = Path("diagnostics")
out.mkdir(exist_ok=True)
(out / "migration-contract.json").write_text(json.dumps({
    "version": "1.5.0", "upstream": "fada664df7a294d1d1a9ca3e7cd3637069122f17",
    "shared_submodule": "229b904508364c8997aad0fb5af57effac859f60",
    "ui_contract": "passed", "official_id_rules": "unchanged",
    "limits": "Source inspection does not replace installation and remote-connection testing."
}, indent=2))
print("Migration source contract passed; credential and macOS launch checks run in platform jobs.")
