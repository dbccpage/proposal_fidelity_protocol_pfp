param([switch]$Apply)
$ErrorActionPreference = 'Stop'
$pfpRoot = [IO.Path]::GetFullPath('C:\Users\a343o\source\repos\proposal_fidelity_protocol_pfp')
$anomalonRoot = [IO.Path]::GetFullPath('C:\Users\a343o\source\repos\anomalon')
$planPath = Join-Path $pfpRoot 'dag\migrations\demo_support_move_plan.json'
$receiptPath = Join-Path $pfpRoot 'dag\migrations\demo_support_move_receipt.json'
$plan = Get-Content -LiteralPath $planPath -Raw | ConvertFrom-Json
$planHash = (Get-FileHash -LiteralPath $planPath -Algorithm SHA256).Hash.ToLowerInvariant()

function Contained-Path([string]$root, [string]$relative) {
    if ([IO.Path]::IsPathRooted($relative) -or $relative.Contains(':') -or $relative.Contains('\') -or
        ($relative.Split('/') | Where-Object { $_ -in @('', '.', '..') })) {
        throw "Unsafe relative path: $relative"
    }
    $path = [IO.Path]::GetFullPath((Join-Path $root $relative))
    if (-not $path.StartsWith($root.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path escapes fixed root: $path"
    }
    $cursor = $path
    while ($cursor) {
        if (Test-Path -LiteralPath $cursor) {
            $item = Get-Item -LiteralPath $cursor -Force
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Reparse point: $cursor" }
            if ($cursor.StartsWith($root.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase)) {
                $streams = @(Get-Item -LiteralPath $cursor -Stream * -ErrorAction Stop)
                if ($streams | Where-Object { $_.Stream -ne ':$DATA' }) { throw "Uninventoried alternate stream: $cursor" }
            }
        }
        $cursor = [IO.Path]::GetDirectoryName($cursor)
    }
    return $path
}

function Verify-Bytes([string]$path, $entry) {
    $item = Get-Item -LiteralPath $path -Force
    if ($item.PSIsContainer -or $item.Length -ne $entry.bytes) { throw "Size/type changed: $path" }
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.sha256) {
        throw "Hash changed: $path"
    }
    $streams = @(Get-Item -LiteralPath $path -Stream * -ErrorAction Stop)
    if ($streams | Where-Object { $_.Stream -ne ':$DATA' }) { throw "Uninventoried alternate stream: $path" }
}

function Save-Receipt($receipt) {
    $temporary = $receiptPath + '.tmp'
    $raw = [Text.Encoding]::UTF8.GetBytes(($receipt | ConvertTo-Json -Depth 12))
    $stream = [IO.File]::Open($temporary, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try { $stream.Write($raw, 0, $raw.Length); $stream.Flush($true) } finally { $stream.Dispose() }
    Move-Item -LiteralPath $temporary -Destination $receiptPath -Force
}

if (Test-Path -LiteralPath $receiptPath) { throw 'Move receipt already exists; inspect custody before resuming.' }
if ($plan.entries.Count -eq 0) { throw 'Empty relocation plan.' }
$seenSources = @{}
$seenTargets = @{}
$resolved = @()
foreach ($entry in $plan.entries) {
    $sourceRoot = switch ($entry.source_repo) { 'anomalon' { $anomalonRoot }; 'pfp' { $pfpRoot }; default { throw 'Unknown source repository.' } }
    $allowed = if ($entry.source_repo -eq 'anomalon') {
        ($entry.source_relative_path -match '^omega_engine_woland/(documentation|_fixtures|program_profiles|evidence)/') -or
        ($entry.source_relative_path -in @($plan.ancillary_source_tests))
    } else { $entry.source_relative_path.StartsWith('education/') }
    if (-not $allowed) { throw "Source outside reviewed scope: $($entry.source_relative_path)" }
    if (-not ($entry.destination_relative_path -match '^pilots/(anomalon_woland_support|education)/')) {
        throw 'Destination outside fixed pilot import roots.'
    }
    $source = Contained-Path $sourceRoot $entry.source_relative_path
    $target = Contained-Path $pfpRoot $entry.destination_relative_path
    if ($seenSources.ContainsKey($source) -or $seenTargets.ContainsKey($target)) { throw 'Duplicate source or destination.' }
    $seenSources[$source] = $true
    $seenTargets[$target] = $true
    if (Test-Path -LiteralPath $target) { throw "Destination already exists: $target" }
    Verify-Bytes $source $entry
    $resolved += [pscustomobject]@{ source = $source; target = $target; entry = $entry }
}
$recovery = Get-Content -LiteralPath (Join-Path $pfpRoot 'dag\migrations\demo_support_recovery.json') -Raw | ConvertFrom-Json
if ($recovery.plan_sha256 -ne $planHash -or
    (Get-FileHash -LiteralPath $recovery.archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $recovery.sha256 -or
    -not $recovery.all_member_hashes_verified) { throw 'Recovery archive is not verified for this plan.' }
Write-Output "Verified plan: $($resolved.Count) files; plan SHA256 $planHash"
if (-not $Apply) { return }
$receipt = [ordered]@{ schema_version = '1.0'; plan_sha256 = $planHash; state = 'copying'; started_utc = [DateTime]::UtcNow.ToString('o'); entries = @(); recovery = $recovery.archive; durability_scope = 'File handles flushed before removal. Directory/rename persistence and concurrent hostile writers are not crash or power-loss certified.' }
Save-Receipt $receipt
foreach ($row in $resolved) {
    Verify-Bytes $row.source $row.entry
    $checkedTarget = Contained-Path $pfpRoot $row.entry.destination_relative_path
    if (Test-Path -LiteralPath $checkedTarget) { throw "Destination appeared after preflight: $checkedTarget" }
    $parent = Split-Path -Parent $row.target
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
    $inputStream = [IO.File]::Open($row.source, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read)
    try {
        $outputStream = [IO.File]::Open($checkedTarget, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
        try { $inputStream.CopyTo($outputStream); $outputStream.Flush($true) } finally { $outputStream.Dispose() }
    } finally { $inputStream.Dispose() }
    Verify-Bytes $row.target $row.entry
    $receipt.entries += [ordered]@{ source_repo = $row.entry.source_repo; source_relative_path = $row.entry.source_relative_path; destination_relative_path = $row.entry.destination_relative_path; sha256 = $row.entry.sha256; bytes = $row.entry.bytes; state = 'copy_verified' }
    Save-Receipt $receipt
}
# All destinations must be verified before the first source deletion.
foreach ($row in $resolved) { Verify-Bytes $row.target $row.entry; Verify-Bytes $row.source $row.entry }
$receipt.state = 'removing_verified_sources'
Save-Receipt $receipt
for ($index = 0; $index -lt $resolved.Count; $index++) {
    $row = $resolved[$index]
    $sourceRoot = if ($row.entry.source_repo -eq 'anomalon') { $anomalonRoot } else { $pfpRoot }
    $checkedSource = Contained-Path $sourceRoot $row.entry.source_relative_path
    $checkedTarget = Contained-Path $pfpRoot $row.entry.destination_relative_path
    Verify-Bytes $checkedSource $row.entry
    Verify-Bytes $checkedTarget $row.entry
    $receipt.entries[$index].state = 'source_removal_intent'
    Save-Receipt $receipt
    Remove-Item -LiteralPath $checkedSource -Force
    if (Test-Path -LiteralPath $checkedSource) { throw "Source remains: $checkedSource" }
    $receipt.entries[$index].state = 'moved_and_verified'
    Save-Receipt $receipt
}
# Remove only empty parent directories under the explicitly reviewed roots.
$parents = @{}
foreach ($row in $resolved) {
    $parent = Split-Path -Parent $row.source
    $boundary = if ($row.entry.source_repo -eq 'anomalon') { Join-Path $anomalonRoot 'omega_engine_woland' } else { Join-Path $pfpRoot 'education' }
    while ($parent.StartsWith($boundary + '\', [StringComparison]::OrdinalIgnoreCase)) {
        $parents[$parent] = $boundary
        $parent = Split-Path -Parent $parent
    }
}
foreach ($parent in ($parents.Keys | Sort-Object Length -Descending)) {
    if ((Test-Path -LiteralPath $parent) -and @(Get-ChildItem -LiteralPath $parent -Force).Count -eq 0) {
        $item = Get-Item -LiteralPath $parent -Force
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Reparse point before empty cleanup: $parent" }
        if (-not $item.FullName.StartsWith($parents[$parent] + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Empty cleanup escaped boundary.' }
        Remove-Item -LiteralPath $parent
    }
}
$receipt.state = 'complete'
$receipt.completed_utc = [DateTime]::UtcNow.ToString('o')
Save-Receipt $receipt
Write-Output "Moved and verified $($resolved.Count) files; source originals removed."
