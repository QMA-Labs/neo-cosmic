param(
    [string]$Model = "qwen3.5",
    [string]$Tag = "0.8b",
    [string]$Destination = "build\ollama-models"
)

$ErrorActionPreference = "Stop"
$Registry = "https://registry.ollama.ai"
$Repository = "library/$Model"
$ManifestUrl = "$Registry/v2/$Repository/manifests/$Tag"
$Headers = @{ Accept = "application/vnd.docker.distribution.manifest.v2+json" }

$ManifestResponse = Invoke-WebRequest -Uri $ManifestUrl -Headers $Headers
$ManifestText = $ManifestResponse.Content
$Manifest = $ManifestText | ConvertFrom-Json
$BlobDir = Join-Path $Destination "blobs"
$ManifestDir = Join-Path $Destination "manifests\registry.ollama.ai\library\$Model"
New-Item -ItemType Directory -Force $BlobDir, $ManifestDir | Out-Null

$Digests = @($Manifest.config.digest) + @($Manifest.layers | ForEach-Object { $_.digest })
foreach ($Digest in $Digests | Select-Object -Unique) {
    if ($Digest -notmatch '^sha256:[0-9a-f]{64}$') { throw "Unexpected blob digest: $Digest" }
    $BlobName = $Digest.Replace(':', '-')
    $BlobPath = Join-Path $BlobDir $BlobName
    if (-not (Test-Path $BlobPath)) {
        Invoke-WebRequest -Uri "$Registry/v2/$Repository/blobs/$Digest" -OutFile $BlobPath
    }
    $Actual = (Get-FileHash $BlobPath -Algorithm SHA256).Hash.ToLower()
    if ($Actual -ne $Digest.Substring(7)) { throw "Checksum mismatch for $Digest" }
}

$ManifestPath = Join-Path $ManifestDir $Tag
[System.IO.File]::WriteAllText($ManifestPath, $ManifestText, [System.Text.UTF8Encoding]::new($false))
Write-Host "Bundled Ollama model: $Model:$Tag"
