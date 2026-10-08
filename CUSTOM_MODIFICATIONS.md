# RustDesk 1.5.0 定制迁移记录

基线为官方稳定版 `1.5.0`，提交 `fada664df7a294d1d1a9ca3e7cd3637069122f17`。
独立分支为 `codex/rebuild-rustdesk-1.5.0`，旧 master 与旧构建分支保留。
本分支先完整导入官方源码，再迁移现有定制；没有沿用旧版核心、依赖或展开的共享库。

## 服务器与密码

- 默认 ID 服务器：`www.dsecret.com:21106`。
- 公钥：`jA+pdkA5sIUOGG2YivcS6KWuLR6lEi9hvzk+aWis7lk=`。
- 原有内置密码保存在 `src/custom_defaults.rs`，值与旧定制记录一致。
- 最新版的服务器、共享配置接口及子模块保持官方版本。客户端设置从 `base::config::keys` 导入。
- 通过 `DEFAULT_SETTINGS` / `DEFAULT_LOCAL_SETTINGS` 提供默认值，已有用户服务器、公钥、主题和开关优先。
- 内置密码采用新版 preset password 接口。个人永久密码通过原有存储验证；失败后仍检查内置密码。两者继续使用官方挑战、常量时间比较和严格存储校验。
- `verification-method` 通过新版 `OVERWRITE_SETTINGS` 固定为 `use-both-passwords`，使服务端和界面一致，迁移旧的仅永久密码配置后仍保留一次性密码。这是原有固定验证模式的兼容迁移，其余默认设置不强制覆盖用户选择。
- 本次没有改变协议、公钥交换、两步验证、登录限流、授权范围或系统权限流程。

## 界面及默认设置

- 桌面主页标题为“大狸子远程控制”。程序名、包名和 Bundle ID 保持 RustDesk，避免破坏系统服务及安装入口。
- 桌面保留“最近会话、收藏、发现”三个设备标签；移动端保留原有五个标签。隐藏桌面账户设置入口、底部服务器提示、ID 三点菜单和一次性密码编辑按钮；保留刷新按钮。
- 默认深色主题，关闭启动更新检查及 LAN 发现，开启 UDP / IPv6 打洞、远程配置修改与 `allow-hide-cm`。
- `allow-hide-cm` 仍使用官方条件：密码批准且仅永久密码时才隐藏窗口。固定并用模式不会额外强制隐藏管理窗口。
- Windows 未安装时点击“启动服务”进入官方安装流程；macOS 原有权限检查保留。
- 保留官方 ID 规则；`src/ui_interface.rs` 及共享子模块未修改。
- 窗口宽高为 1 时恢复默认尺寸，保留原有 1×1 配置修复。
- 移动端和 Sciter 使用自身界面及启动流程；通用服务器、密码和默认设置通过客户端初始化生效。

## GitHub 云编译

入口：`.github/workflows/custom-client.yml`。推送定制分支或手动运行触发。
平台流程根据官方 1.5.0 `.github/workflows/flutter-build.yml` 生成，沿用对应工具版本、补丁、子模块、依赖和桥接生成步骤。

| 平台 | 本轮范围 |
| --- | --- |
| macOS | Intel x64、Apple Silicon ARM64，各自 DMG |
| Windows | x64 Flutter EXE / MSI / 完整程序目录；x86 Sciter EXE / 程序目录 |
| Android | ARM64、ARMv7、x86_64、通用 APK |
| Linux | x64、ARM64 的 DEB、RPM、AppImage、Flatpak；Sciter x64 / ARMv7 DEB，Sciter x64 Flatpak |
| iOS | ARM64 静态库、未签名 `.xcarchive` ZIP |

不启用 Web、Windows ARM64、额外 DRM 版本或 Release 自动发布。
矩阵 `fail-fast: false`，每个平台独立提供诊断。AppImage / Flatpak 即使其他架构失败，也尝试下载自身架构的中间产物。
安装包、中间依赖、校验值和诊断文件通过 Actions Artifact 保留 90 天。

macOS 在 Flutter 与服务文件完成装配后，通过官方签名辅助脚本进行临时签名，保留 Release entitlements。验证主程序、服务、动态库、框架、权限说明与版本；挂载最终 DMG 再次验证其应用。没有 Apple 公证。
云端通过 Launch Services 启动干净配置和旧的 1×1 窗口配置，检查可见主窗口并保存标准输出、窗口记录和崩溃报告。检查失败仍上传已完成的安装包，最后将该平台标记为失败。

Android 优先使用仓库 `ANDROID_SIGNING_KEY` 等现有签名配置。缺失时沿用官方流程的测试证书，APK 同样通过签名与 ABI 检查；不同证书的旧包需要先卸载，测试证书也可能随运行改变。每个 APK 附带 `SIGNING.txt`。
iOS 沿用 `--no-codesign`，ZIP 内为应用归档，需自行签名后安装。

## 云端验证与实际限制

- 独立 Rust 测试进程验证新配置默认值、保存的用户设置、旧验证模式迁移、一次性密码、个人永久密码、内置密码及错误密码拒绝。
- 云端源代码检查核对界面要求、Windows 安装入口、macOS 权限入口和官方 ID 接口未改动；这不等同于实际交互验收。
- macOS 检查实际启动与可用主窗口；所有平台检查产物版本、架构、依赖或包内容，保留 SHA256SUMS。
- 源码、流程与检查均已提交后才触发本轮构建。此记录描述实现和预定云检查，不表示云编译或实际远程连接已经成功。
- 本地仅准备源码和提交，不在本机编译或运行客户端。实际安装及服务器连接仍需用户测试。

## 最小修改范围复核

相对官方 1.5.0，仅修改以下现有运行路径：

| 文件 | 必要变化 |
| --- | --- |
| `src/lib.rs` | 注册独立定制默认模块 |
| `src/common.rs` | 初始化及读取定制后应用默认值和固定密码模式 |
| `src/flutter_ffi.rs` | Flutter / 移动端完成配置初始化后应用定制 |
| `src/server/connection.rs` | 个人永久密码存在时仍验证 preset；注册仅测试模块 |
| `flutter/lib/models/peer_tab_model.dart` | 桌面设备列表保留三个标签 |
| `flutter/lib/desktop/pages/connection_page.dart` | 删除服务器引导提示 |
| `flutter/lib/desktop/pages/desktop_setting_page.dart` | 隐藏账户标签 |
| `flutter/lib/desktop/pages/desktop_home_page.dart` | 主页标题、隐藏菜单和密码编辑入口 |
| `flutter/lib/common.dart` | Windows 安装入口及 1×1 窗口恢复 |

其余实现、测试和定制工作流为新增文件；没有重构共享接口或修改官方子模块。
