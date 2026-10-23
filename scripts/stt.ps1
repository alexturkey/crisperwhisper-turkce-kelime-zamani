# Windows'tan çalıştırma / run from Windows: ses dosyasını WSL yoluna çevirip CLI'yi WSL venv'inde koşturur.
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\stt.ps1 -Ses C:\ses\kayit.mp3 -Dil tr [-Cikti C:\ses\cikti] [-Dagitim Ubuntu] [-Ek "--bicim json,srt"]
param(
    [Parameter(Mandatory = $true)][string]$Ses,
    [string]$Dil = "tr",
    [string]$Cikti = "",
    [string]$Dagitim = "Ubuntu",
    [string]$Ek = ""
)
# -Ek yalnız kendi bayraklarımız içindir; her parça --bayrak ya da düz değer olmalı

$ErrorActionPreference = "Stop"
$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
function WslYol([string]$p) {
    $tam = (Resolve-Path -LiteralPath $p -ErrorAction SilentlyContinue)
    if ($tam) { $p = $tam.Path }
    if ($p -notmatch '^[A-Za-z]:\\') { throw "mutlak Windows yolu gerekir: $p" }
    return "/mnt/" + $p.Substring(0, 1).ToLower() + ($p.Substring(2) -replace "\\", "/")
}
if (-not (Test-Path -LiteralPath $Ses)) { throw "ses dosyası yok: $Ses" }
$repoW = WslYol $Repo
$argv = @((WslYol $Ses), "--dil", $Dil)
if ($Cikti) { New-Item -ItemType Directory -Force $Cikti | Out-Null; $argv += @("--cikti", (WslYol $Cikti)) }
if ($Ek) { foreach ($parca in ($Ek -split " ")) { if ($parca -notmatch '^[-\w.,/:=]+$') { throw "-Ek içinde izin verilmeyen karakter: $parca" }; $argv += $parca } }
# argümanlar liste olarak geçer, kabuk dizesi kurulmaz (dosya adındaki boşluk ve özel karakter komut olmaz)
& wsl.exe -d $Dagitim --cd $repoW -- .venv/bin/python -m transkript @argv
exit $LASTEXITCODE
