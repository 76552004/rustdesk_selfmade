import Foundation
import CoreGraphics

let pids = Set(CommandLine.arguments.dropFirst().compactMap { Int($0) })
let windows = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] ?? []
let visible = windows.filter {
    pids.contains($0[kCGWindowOwnerPID as String] as? Int ?? -1) &&
    ($0[kCGWindowLayer as String] as? Int ?? -1) == 0
}
let data = try JSONSerialization.data(withJSONObject: visible, options: [.sortedKeys])
print(String(data: data, encoding: .utf8)!)
