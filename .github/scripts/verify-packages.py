"""Inspect delivered files on CI; never runs or installs them on this computer."""
import argparse
import glob
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import zipfile

parser = argparse.ArgumentParser()
parser.add_argument("kind", choices=["android", "linux", "windows", "ios"])
parser.add_argument("arch")
parser.add_argument("patterns", nargs="+")
args = parser.parse_args()
files = [Path(p) for pattern in args.patterns for p in glob.glob(pattern)]
assert files, "No deliverable found for verification"
out = Path("diagnostics")
out.mkdir(exist_ok=True)
report = []

def command(*argv):
    result = subprocess.run(argv, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    report.append({"command": list(argv), "output": result.stdout, "stderr": result.stderr})
    return result.stdout

def elf(data, arch):
    assert data[:4] == b"\x7fELF", "Missing ELF executable/library"
    endian = "<" if data[5] == 1 else ">"
    machine = struct.unpack_from(endian + "H", data, 18)[0]
    assert machine == {"x86_64": 62, "aarch64": 183, "armv7": 40}[arch], (arch, machine)

try:
    for package in files:
        assert package.stat().st_size > 0, package
        if args.kind == "android":
            sdk = Path(__import__("os").environ.get("ANDROID_HOME", "/usr/local/lib/android/sdk"))
            tools = sorted((sdk / "build-tools").iterdir())[-1]
            badging = command(str(tools / "aapt"), "dump", "badging", str(package))
            assert "versionName='1.5.0'" in badging
            command(str(tools / "apksigner"), "verify", "--verbose", "--print-certs", str(package))
            abis = {"aarch64": ["arm64-v8a"], "armv7": ["armeabi-v7a"], "x86_64": ["x86_64"],
                    "universal": ["arm64-v8a", "armeabi-v7a", "x86_64"]}[args.arch]
            with zipfile.ZipFile(package) as archive:
                assert archive.testzip() is None
                assert "AndroidManifest.xml" in archive.namelist()
                for abi in abis:
                    arch = {"arm64-v8a": "aarch64", "armeabi-v7a": "armv7", "x86_64": "x86_64"}[abi]
                    for library in ("librustdesk.so", "libflutter.so", "libc++_shared.so"):
                        elf(archive.read(f"lib/{abi}/{library}")[:64], arch)
        elif args.kind == "windows":
            if package.suffix.lower() in (".exe", ".dll"):
                data = package.read_bytes()
                assert data[:2] == b"MZ"
                pe = struct.unpack_from("<I", data, 60)[0]
                assert data[pe:pe + 4] == b"PE\0\0"
                assert struct.unpack_from("<H", data, pe + 4)[0] == {"x86_64": 0x8664, "x86": 0x14c}[args.arch]
            elif package.suffix.lower() == ".msi":
                assert package.read_bytes()[:8] == bytes.fromhex("D0CF11E0A1B11AE1")
        elif args.kind == "linux":
            if package.suffix == ".deb":
                assert command("dpkg-deb", "-f", str(package), "Version").strip().startswith("1.5.0")
                assert command("dpkg-deb", "-f", str(package), "Architecture").strip() == {
                    "x86_64": "amd64", "aarch64": "arm64", "armv7": "armhf"}[args.arch]
                with tempfile.TemporaryDirectory() as temp:
                    command("dpkg-deb", "-x", str(package), temp)
                    binaries = [p for p in Path(temp).rglob("rustdesk") if p.is_file() and not p.is_symlink()]
                    assert binaries, "Missing client in DEB"
                    for binary in binaries:
                        elf(binary.read_bytes()[:64], args.arch)
                        command("readelf", "-d", str(binary))
            elif package.suffix == ".rpm":
                version = command("rpm", "-qp", "--qf", "%{VERSION} %{ARCH}", str(package))
                assert version == "1.5.0 " + {"x86_64": "x86_64", "aarch64": "aarch64"}[args.arch]
                command("rpm", "-qp", "--requires", str(package))
                command("rpm", "-qpl", str(package))
            elif package.suffix == ".AppImage":
                elf(package.read_bytes()[:64], args.arch)
                assert package.read_bytes()[8:11] == b"AI\x02"
                command("file", str(package))
            elif package.suffix == ".flatpak":
                with tempfile.TemporaryDirectory() as repo:
                    command("ostree", "--repo=" + repo, "init", "--mode=archive-z2")
                    command("flatpak", "build-import-bundle", repo, str(package))
                    refs = command("ostree", "--repo=" + repo, "refs").splitlines()
                    ref = next(r for r in refs if f"/com.rustdesk.RustDesk/{args.arch}/" in r)
                    command("ostree", "--repo=" + repo, "ls", ref, "/files/bin/rustdesk")
        elif args.kind == "ios":
            if package.suffix == ".a":
                command("lipo", str(package), "-verify_arch", "arm64")
            elif package.suffix == ".zip":
                with zipfile.ZipFile(package) as archive:
                    assert archive.testzip() is None
                    assert any(name.endswith(".app/Info.plist") for name in archive.namelist())
        report.append({"file": str(package), "bytes": package.stat().st_size, "status": "verified"})
finally:
    (out / "package-verification.json").write_text(json.dumps(report, indent=2))
