param([switch]$Apply)
$ErrorActionPreference = 'Stop'
$taskRepo = 'C:\Users\a343o\source\repos\proposal_fidelity_protocol_pfp'
$taskIncoming = [IO.Path]::GetFullPath((Join-Path $taskRepo 'pilots\anomalon_woland'))
$taskPlanFile = Join-Path $taskRepo 'dag\pilot_triage\retirement_plan.json'
$taskReceiptFile = Join-Path $taskRepo 'dag\pilot_triage\retirement_receipt.json'
if (Test-Path -LiteralPath $taskReceiptFile) { throw 'Removal receipt already exists; inspect it instead of rerunning' }
$taskPlan = Get-Content -LiteralPath $taskPlanFile -Raw | ConvertFrom-Json
$taskPlanDigest = (Get-FileHash -LiteralPath $taskPlanFile -Algorithm SHA256).Hash.ToLowerInvariant()
if ($taskPlan.repository_root -ne $taskRepo -or $taskPlan.incoming_root -ne $taskIncoming) { throw 'Unexpected fixed repository roots' }
if ($taskPlan.status -ne 'frozen_ready_for_checked_removal') { throw 'Plan not frozen for removal' }
if ($taskPlan.pilot_count -ne @($taskPlan.pilots).Count) { throw 'Plan count mismatch' }
foreach ($taskAncestor in @($taskRepo, (Join-Path $taskRepo 'pilots'), $taskIncoming)) {
    if ((Get-Item -LiteralPath $taskAncestor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Linked target ancestry' }
}
$taskLessons = Join-Path $taskRepo 'dag\pilot_triage\retained_lessons.json'
if ($taskPlan.lessons_path -ne 'dag/pilot_triage/retained_lessons.json') { throw 'Unexpected lesson path' }
if ((Get-FileHash -LiteralPath $taskLessons -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskPlan.lessons_sha256) { throw 'Preserved lessons changed' }
$taskArchivePath = [IO.Path]::GetFullPath($taskPlan.recovery_archive.archive_path)
if ((Get-Item -LiteralPath $taskArchivePath).Length -ne $taskPlan.recovery_archive.archive_bytes) { throw 'Archive length changed' }
if ((Get-FileHash -LiteralPath $taskArchivePath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskPlan.recovery_archive.archive_sha256) { throw 'Archive hash changed' }

function Test-CurrentPilot($taskPilot) {
    if ($taskPilot.id -cnotmatch '^pilot_[0-9]{7}$') { throw 'Invalid pilot identifier' }
    if ($taskPilot.path -cne ('pilots/anomalon_woland/' + $taskPilot.id)) { throw 'Unexpected relative target' }
    $taskTarget = [IO.Path]::GetFullPath((Join-Path $taskIncoming $taskPilot.id))
    if (-not $taskTarget.StartsWith($taskIncoming + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Target escaped incoming root' }
    if ([IO.Path]::GetDirectoryName($taskTarget) -ne $taskIncoming) { throw 'Target is not a direct pilot child' }
    if (-not (Test-Path -LiteralPath $taskTarget -PathType Container)) { throw 'Pilot target missing' }
    if ((Get-Item -LiteralPath $taskTarget -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Linked pilot target' }
    if (@(Get-ChildItem -LiteralPath $taskTarget -Recurse -Force -Attributes ReparsePoint).Count -ne 0) { throw 'Linked pilot descendant' }
    $taskAllItems = @((Get-Item -LiteralPath $taskTarget -Force)) + @(Get-ChildItem -LiteralPath $taskTarget -Recurse -Force)
    foreach ($taskItem in $taskAllItems) {
        $taskExtraStreams = @(Get-Item -LiteralPath $taskItem.FullName -Stream * -ErrorAction Stop | Where-Object { $_.Stream -cne ':$DATA' })
        if ($taskExtraStreams.Count -ne 0) { throw 'Unarchived NTFS stream; refusing removal' }
    }
    $taskCurrentDirs = @($taskAllItems | Where-Object { $_.PSIsContainer -and $_.FullName -ne $taskTarget } | ForEach-Object { $_.FullName.Substring($taskIncoming.Length + 1).Replace('\','/') } | Sort-Object)
    $taskExpectedDirs = @($taskArchivedCustody.directories | Where-Object { $_.StartsWith($taskPilot.id + '/', [StringComparison]::Ordinal) } | Sort-Object)
    if ($taskCurrentDirs.Count -ne $taskExpectedDirs.Count) { throw 'Unknown or missing directory; refusing removal' }
    if ($taskCurrentDirs.Count -gt 0 -and @(Compare-Object $taskCurrentDirs $taskExpectedDirs -CaseSensitive).Count -ne 0) { throw 'Directory structure differs from archive custody' }
    $taskExpected = [Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
    foreach ($taskEntry in $taskPilot.entries) {
        if (-not $taskEntry.path.StartsWith($taskPilot.id + '/', [StringComparison]::Ordinal)) { throw 'File outside selected pilot' }
        if ($taskEntry.path -match '(^|/)\.\.?(/|$)|\\|:') { throw 'Noncanonical entry path' }
        $taskExpected.Add($taskEntry.path, $taskEntry)
    }
    $taskCurrentFiles = @(Get-ChildItem -LiteralPath $taskTarget -Recurse -Force -File)
    if ($taskCurrentFiles.Count -ne $taskExpected.Count -or $taskExpected.Count -ne $taskPilot.file_count) { throw 'Unknown or missing files; refusing removal' }
    foreach ($taskFile in $taskCurrentFiles) {
        $taskRelative = $taskFile.FullName.Substring($taskIncoming.Length + 1).Replace('\','/')
        if (-not $taskExpected.ContainsKey($taskRelative)) { throw 'Unmanifested file in target' }
        $taskExpectedFile = $taskExpected[$taskRelative]
        if ($taskFile.Length -ne $taskExpectedFile.bytes) { throw 'Current file size changed' }
        if ((Get-FileHash -LiteralPath $taskFile.FullName -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskExpectedFile.sha256) { throw 'Current file bytes changed' }
    }
    return $taskTarget
}

Add-Type -AssemblyName System.IO.Compression
$taskArchive = [IO.Compression.ZipFile]::OpenRead($taskArchivePath)
try {
    $taskZipEntries = [Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
    foreach ($taskZipEntry in $taskArchive.Entries) { $taskZipEntries.Add($taskZipEntry.FullName, $taskZipEntry) }
    if (-not $taskZipEntries.ContainsKey('_migration_manifest.json')) { throw 'Archived migration manifest absent' }
    $taskManifestReader = [IO.StreamReader]::new($taskZipEntries['_migration_manifest.json'].Open())
    try { $taskArchivedCustody = $taskManifestReader.ReadToEnd() | ConvertFrom-Json }
    finally { $taskManifestReader.Dispose() }
    $taskSeen = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    $taskReports = [Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
    $taskFilesVerified = 0
    foreach ($taskPilot in $taskPlan.pilots) {
        if (-not $taskSeen.Add($taskPilot.id)) { throw 'Duplicate removal target' }
        if ($taskPilot.verdict -notin @('stub_candidate', 'trivial_candidate')) { throw 'Pilot outside selected retirement criteria' }
        $taskReportPath = [IO.Path]::GetFullPath((Join-Path $taskRepo $taskPilot.report))
        if (-not $taskReportPath.StartsWith((Join-Path $taskRepo 'dag\pilot_triage') + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Report outside triage directory' }
        if (-not $taskReports.ContainsKey($taskReportPath)) {
            $taskReportDigest = (Get-FileHash -LiteralPath $taskReportPath -Algorithm SHA256).Hash.ToLowerInvariant()
            $taskReports.Add($taskReportPath, @{digest=$taskReportDigest; body=(Get-Content -LiteralPath $taskReportPath -Raw | ConvertFrom-Json)})
        }
        if ($taskReports[$taskReportPath].digest -ne $taskPilot.report_sha256) { throw 'Assessment report changed' }
        $taskReport = $taskReports[$taskReportPath].body
        $taskReviewed = @($taskReport.pilots | Where-Object { $_.id -ceq $taskPilot.id })
        if ($taskReviewed.Count -ne 1 -or $taskReviewed[0].verdict -cne $taskPilot.verdict -or $taskReviewed[0].path -cne $taskPilot.path -or $taskReviewed[0].rationale -cne $taskPilot.rationale) { throw 'Plan does not match current reviewed verdict' }
        $null = Test-CurrentPilot $taskPilot
        foreach ($taskEntry in $taskPilot.entries) {
            if (-not $taskZipEntries.ContainsKey($taskEntry.path)) { throw 'No archived recovery entry' }
            $taskArchived = $taskZipEntries[$taskEntry.path]
            if ($taskArchived.Length -ne $taskEntry.bytes) { throw 'Archive entry size differs' }
            $taskStream = $taskArchived.Open()
            $taskHasher = [Security.Cryptography.SHA256]::Create()
            try { $taskArchivedHash = [Convert]::ToHexString($taskHasher.ComputeHash($taskStream)).ToLowerInvariant() }
            finally { $taskStream.Dispose(); $taskHasher.Dispose() }
            if ($taskArchivedHash -ne $taskEntry.sha256) { throw 'Archive entry hash differs' }
            $taskFilesVerified += 1
        }
    }
    if ($taskFilesVerified -ne $taskPlan.file_count) { throw 'Total file count mismatch' }
}
finally { $taskArchive.Dispose() }

if (-not $Apply) {
    [ordered]@{status='preflight_passed_no_removal'; pilots=$taskPlan.pilot_count; files=$taskFilesVerified; plan_sha256=$taskPlanDigest} | ConvertTo-Json -Compress
    return
}

$taskReceipt = [ordered]@{schema_version='1.0'; status='applying'; plan_sha256=$taskPlanDigest; started_at_utc=[DateTime]::UtcNow.ToString('o'); removal_intent=$null; removed=@()}
function Write-RemovalReceipt {
    $taskReceiptJson = $taskReceipt | ConvertTo-Json -Depth 8
    $taskReceiptTmp = $taskReceiptFile + '.tmp'
    [IO.File]::WriteAllText($taskReceiptTmp, $taskReceiptJson + "`n", [Text.UTF8Encoding]::new($false))
    [IO.File]::Move($taskReceiptTmp, $taskReceiptFile, $true)
}
Write-RemovalReceipt
foreach ($taskPilot in $taskPlan.pilots) {
    # Resolve, check containment, reject links and recheck every file immediately before removal.
    $taskTarget = Test-CurrentPilot $taskPilot
    $taskReceipt.removal_intent = [ordered]@{id=$taskPilot.id; path=$taskPilot.path; started_at_utc=[DateTime]::UtcNow.ToString('o')}
    Write-RemovalReceipt
    Remove-Item -LiteralPath $taskTarget -Recurse -Force
    if (Test-Path -LiteralPath $taskTarget) { throw 'Pilot remains after removal' }
    $taskReceipt.removed += [ordered]@{id=$taskPilot.id; path=$taskPilot.path; files=$taskPilot.file_count; bytes=$taskPilot.bytes; removed_at_utc=[DateTime]::UtcNow.ToString('o')}
    $taskReceipt.removal_intent = $null
    Write-RemovalReceipt
}
$taskReceipt.status = 'complete'
$taskReceipt.completed_at_utc = [DateTime]::UtcNow.ToString('o')
Write-RemovalReceipt
[ordered]@{status='complete'; retired_pilots=$taskReceipt.removed.Count; files=$taskFilesVerified; recovery_archive_sha256=$taskPlan.recovery_archive.archive_sha256} | ConvertTo-Json -Compress
