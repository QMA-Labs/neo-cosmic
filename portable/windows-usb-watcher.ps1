$ErrorActionPreference = "SilentlyContinue"
$launched = @{}
while ($true) {
    Get-PSDrive -PSProvider FileSystem | ForEach-Object {
        $root = $_.Root
        $marker = Join-Path $root "NEO_PORTABLE"
        $launcher = Join-Path $root "START_NEO.cmd"
        if ((Test-Path $marker) -and (Test-Path $launcher) -and -not $launched.ContainsKey($root)) {
            Start-Process -FilePath $launcher -WorkingDirectory $root
            $launched[$root] = $true
        }
    }
    @($launched.Keys) | ForEach-Object {
        if (-not (Test-Path (Join-Path $_ "NEO_PORTABLE"))) { $launched.Remove($_) }
    }
    Start-Sleep -Seconds 5
}
