$ErrorActionPreference = 'Stop'
$taskSourceRepo = 'C:\Users\a343o\source\repos\anomalon'
$taskDestinationRepo = 'C:\Users\a343o\source\repos\proposal_fidelity_protocol_pfp'
$taskSourceRelative = 'omega_engine_woland/tests/pilots'
$taskSource = [IO.Path]::GetFullPath((Join-Path $taskSourceRepo $taskSourceRelative))
$taskDestination = [IO.Path]::GetFullPath((Join-Path $taskDestinationRepo 'pilots\anomalon_woland'))
$taskManifest = Join-Path $taskDestinationRepo 'dag\migrations\anomalon_pilots_move.json'

if ($taskSource -ne 'C:\Users\a343o\source\repos\anomalon\omega_engine_woland\tests\pilots') { throw 'Unexpected source path' }
if (-not $taskDestination.StartsWith($taskDestinationRepo + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Destination escaped repository' }
if (-not (Test-Path -LiteralPath $taskSource -PathType Container)) { throw 'Source directory absent' }
if (Test-Path -LiteralPath $taskDestination) { throw 'Destination exists; refusing overwrite' }
if ((Get-Item -LiteralPath $taskSource -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Source is linked' }
$taskLinks = @(Get-ChildItem -LiteralPath $taskSource -Recurse -Force -Attributes ReparsePoint)
if ($taskLinks.Count -ne 0) { throw 'Linked descendants require separate review' }

$taskCommit = (& git -C $taskSourceRepo rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Cannot resolve source Git commit' }
$taskBranch = (& git -C $taskSourceRepo branch --show-current).Trim()
if ($taskBranch -ne 'codex/move-woland-pilots-to-pfp') { throw 'Unexpected source branch' }
$taskTracked = [Collections.Generic.Dictionary[string,string]]::new([StringComparer]::Ordinal)
foreach ($taskLine in (& git -c core.quotepath=false -C $taskSourceRepo ls-files --stage -- $taskSourceRelative)) {
    if ($taskLine -notmatch '^\d+ ([0-9a-f]+) 0\t(.+)$') { throw 'Unexpected Git index record' }
    $taskTracked.Add($Matches[2], $Matches[1])
}
if ($LASTEXITCODE -ne 0) { throw 'Cannot read source Git index' }
$taskFiles = @(Get-ChildItem -LiteralPath $taskSource -Recurse -Force -File | Sort-Object FullName)
$taskDirs = @(Get-ChildItem -LiteralPath $taskSource -Recurse -Force -Directory | ForEach-Object { $_.FullName.Substring($taskSource.Length + 1).Replace('\','/') } | Sort-Object)
$taskEntries = [Collections.Generic.List[object]]::new()
$taskBytes = [long]0
foreach ($taskFile in $taskFiles) {
    $taskRelative = $taskFile.FullName.Substring($taskSource.Length + 1).Replace('\','/')
    $taskGitPath = $taskSourceRelative + '/' + $taskRelative
    $taskDigest = (Get-FileHash -LiteralPath $taskFile.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    $taskEntries.Add([ordered]@{path=$taskRelative; bytes=$taskFile.Length; sha256=$taskDigest; source_git_tracked=$taskTracked.ContainsKey($taskGitPath); source_git_blob= $(if ($taskTracked.ContainsKey($taskGitPath)) {$taskTracked[$taskGitPath]} else {$null})})
    $taskBytes += $taskFile.Length
}
$taskManifestBody = [ordered]@{
    schema_version='1.0'; status='snapshotted_before_move';
    source_repository='https://github.com/dbccpage/anomalon'; source_commit=$taskCommit;
    source_branch=$taskBranch; source_path=$taskSource; destination_path=$taskDestination;
    destination_relative_path='pilots/anomalon_woland';
    files=$taskEntries.Count; bytes=$taskBytes; git_tracked_files=$taskTracked.Count;
    local_extra_files=$taskEntries.Count - $taskTracked.Count;
    created_utc=[DateTime]::UtcNow.ToString('o');
    assessment='Untriaged legacy pilot corpus. Relocation does not establish replayability, correctness, nontriviality or applicability to the sealed benchmark.';
    directories=$taskDirs; entries=$taskEntries
}
$taskManifestBody | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $taskManifest -Encoding utf8NoBOM
Write-Output "Snapshotted $($taskEntries.Count) files ($taskBytes bytes); moving the exact directory."

# Both resolved absolute targets were checked above; no generated shell commands.
New-Item -ItemType Directory -Path (Split-Path -Parent $taskDestination) -Force | Out-Null
Move-Item -LiteralPath $taskSource -Destination $taskDestination
if (Test-Path -LiteralPath $taskSource) { throw 'Source remains after move' }
$taskMovedFiles = @(Get-ChildItem -LiteralPath $taskDestination -Recurse -Force -File)
if ($taskMovedFiles.Count -ne $taskEntries.Count) { throw 'Destination file count differs' }
foreach ($taskEntry in $taskEntries) {
    $taskTarget = Join-Path $taskDestination $taskEntry.path
    if (-not (Test-Path -LiteralPath $taskTarget -PathType Leaf)) { throw "Missing moved file: $($taskEntry.path)" }
    if ((Get-Item -LiteralPath $taskTarget).Length -ne $taskEntry.bytes) { throw "Moved size mismatch: $($taskEntry.path)" }
    if ((Get-FileHash -LiteralPath $taskTarget -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskEntry.sha256) { throw "Moved hash mismatch: $($taskEntry.path)" }
}
$taskMovedDirs = @(Get-ChildItem -LiteralPath $taskDestination -Recurse -Force -Directory | ForEach-Object { $_.FullName.Substring($taskDestination.Length + 1).Replace('\','/') } | Sort-Object)
if (@(Compare-Object $taskDirs $taskMovedDirs).Count -ne 0) { throw 'Directory structure differs' }
$taskManifestBody.status = 'moved_and_every_file_sha256_verified'
$taskManifestBody.completed_utc = [DateTime]::UtcNow.ToString('o')
$taskManifestBody.source_directory_absent = $true
$taskManifestBody | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $taskManifest -Encoding utf8NoBOM
[ordered]@{status=$taskManifestBody.status; files=$taskEntries.Count; bytes=$taskBytes; git_tracked_files=$taskTracked.Count; local_extra_files=$taskEntries.Count-$taskTracked.Count; source_absent=$true; destination=$taskDestination} | ConvertTo-Json -Compress
