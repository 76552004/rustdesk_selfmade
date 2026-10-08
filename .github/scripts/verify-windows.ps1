param([string]$Dist, [string]$Ui)
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force diagnostics | Out-Null
$version = (Get-Item "$Dist/rustdesk.exe").VersionInfo.ProductVersion
if ($version -notmatch '^1\.5\.0(?:\D|$)') { throw "Unexpected client version: $version" }
$required = if ($Ui -eq 'flutter') {
    @('librustdesk.dll', 'flutter_windows.dll', 'data/icudtl.dat', 'data/flutter_assets')
} else {
    @('sciter.dll')
}
foreach ($file in $required) {
    if (!(Test-Path "$Dist/$file")) { throw "Missing client dependency: $file" }
}
$report = @("Client version: $version", "UI: $Ui", "Required dependencies: $($required -join ', ')")
foreach ($msi in Get-ChildItem -Path SignOutput -Filter *.msi) {
    $installer = New-Object -ComObject WindowsInstaller.Installer
    $database = $installer.GetType().InvokeMember('OpenDatabase', 'InvokeMethod', $null, $installer, @($msi.FullName, 0))
    $view = $database.GetType().InvokeMember('OpenView', 'InvokeMethod', $null, $database, @("SELECT Value FROM Property WHERE Property = 'ProductVersion'"))
    $view.GetType().InvokeMember('Execute', 'InvokeMethod', $null, $view, $null) | Out-Null
    $record = $view.GetType().InvokeMember('Fetch', 'InvokeMethod', $null, $view, $null)
    $msiVersion = $record.GetType().InvokeMember('StringData', 'GetProperty', $null, $record, @(1))
    if ($msiVersion -notmatch '^1\.5\.0(?:\D|$)') { throw "Unexpected MSI version: $msiVersion" }
    $report += "MSI version: $msiVersion"
}
$report | Set-Content diagnostics/windows-version-and-dependencies.txt
