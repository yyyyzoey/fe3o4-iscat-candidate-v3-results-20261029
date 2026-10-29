param(
    [string]$PartsDir = ".\results_bundle.zip.parts",
    [string]$Output = ".\results_bundle.zip",
    [string]$ExpectedSha256 = "fd5539a688e9b69bcf1f543518f08e1bbd8818e928f1f2c991ee24260857e1c7"
)
$ErrorActionPreference = "Stop"
$parts = Get-ChildItem -LiteralPath $PartsDir -Filter "results_bundle.zip.part*" | Sort-Object Name
if ($parts.Count -eq 0) { throw "No parts found in $PartsDir" }
$outPath = [IO.Path]::GetFullPath((Join-Path (Get-Location) $Output))
$stream = [IO.File]::Open($outPath, [IO.FileMode]::Create, [IO.FileAccess]::Write, [IO.FileShare]::None)
try {
    foreach ($p in $parts) {
        $input = [IO.File]::OpenRead($p.FullName)
        try { $input.CopyTo($stream) } finally { $input.Dispose() }
    }
} finally { $stream.Dispose() }
$actual = (Get-FileHash -LiteralPath $outPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actual -ne $ExpectedSha256.ToLowerInvariant()) { throw "SHA256 mismatch: $actual" }
Write-Host "Reassembled and verified: $outPath"
Write-Host "SHA256: $actual"
