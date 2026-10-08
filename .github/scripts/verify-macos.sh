#!/usr/bin/env bash
set -euo pipefail
app=$1
arch=$2
mkdir -p diagnostics
codesign --verify --deep --strict --verbose=2 "$app"
test -f "$app/Contents/Info.plist"
for key in NSMicrophoneUsageDescription; do
  /usr/libexec/PlistBuddy -c "Print :$key" "$app/Contents/Info.plist"
done
main=$(/usr/libexec/PlistBuddy -c 'Print :CFBundleExecutable' "$app/Contents/Info.plist")
version=$(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "$app/Contents/Info.plist")
[[ "$version" == "1.5.0" ]]
for code in "$app/Contents/MacOS/$main" "$app/Contents/MacOS/service"; do
  test -f "$code"
  lipo -verify_arch "$arch" "$code"
  file "$code"
  otool -L "$code"
done
count=0
while IFS= read -r -d '' library; do
  lipo -verify_arch "$arch" "$library"
  otool -L "$library"
  count=$((count + 1))
done < <(find "$app/Contents" -type f -name 'librustdesk.dylib' -print0)
[[ "$count" -ge 1 ]]
while IFS= read -r -d '' code; do
  if file -b "$code" | grep -q 'Mach-O'; then
    lipo -verify_arch "$arch" "$code"
    codesign --verify --strict "$code"
  fi
done < <(find "$app/Contents/Frameworks" -type f -print0)
codesign -d --entitlements :- "$app" > diagnostics/entitlements.plist 2> diagnostics/signature.txt
