param(
    [string]$OutputDirectory = ".\work"
)

$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null

# Get-Process executes on the Windows host, unlike psutil inside the Docker container.
$processes = @(Get-Process | ForEach-Object {
    $cpu = 0.0
    $rss = 0L
    try { if ($null -ne $_.CPU) { $cpu = [double]$_.CPU } } catch { }
    try { $rss = [Int64]$_.WorkingSet64 } catch { }
    [ordered]@{
        pid         = "$($_.Id)"
        name        = $_.ProcessName
        cpu_seconds = $cpu
        rss_bytes   = $rss
    }
})

$timestamp = (Get-Date).ToUniversalTime().ToString("o")
$snapshot = [ordered]@{ taken_at = $timestamp; source = "WindowsProbe"; processes = $processes }
$snapshotPath = Join-Path $OutputDirectory "windows-snapshot.json"
$snapshot | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $snapshotPath -Encoding utf8

# Normalization keeps a live machine's values usable by deterministic lab algorithms.
$cpuProcesses = @($processes | Sort-Object cpu_seconds -Descending | ForEach-Object -Begin { $index = 0 } -Process {
    $burst = [Math]::Max(1, [Math]::Min(100, [Math]::Ceiling(8 * [Math]::Log($_.cpu_seconds + 1, 2))))
    [ordered]@{ pid = $_.pid; arrival = $index % 20; burst = $burst; priority = $index % 5 }
    $index++
})
$requests = @($processes | ForEach-Object {
    # One memory unit is 16 MiB; cap outliers so one browser process cannot dominate the lab.
    [Math]::Max(1, [Math]::Min(512, [Math]::Ceiling($_.rss_bytes / 16MB)))
})
$requestTotal = [int](($requests | Measure-Object -Sum).Sum)
$shape = @(32, 64, 128, 256, 64, 512, 128, 256, 32, 512, 128, 256)
$scale = [Math]::Max(1, [Math]::Ceiling(($requestTotal * 1.10) / (($shape | Measure-Object -Sum).Sum)))
$blocks = @($shape | ForEach-Object { $_ * $scale })
$workloads = [ordered]@{
    captured_processes = $processes.Count
    cpu = [ordered]@{ processes = $cpuProcesses; quantum = 4 }
    memory = [ordered]@{ blocks = $blocks; requests = $requests; unit = "16 MiB normalized RSS" }
}
$workloadPath = Join-Path $OutputDirectory "windows-derived-workloads.json"
$workloads | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $workloadPath -Encoding utf8

Write-Host "Captured $($processes.Count) Windows processes."
Write-Host "Snapshot:  $snapshotPath"
Write-Host "Workloads: $workloadPath"
