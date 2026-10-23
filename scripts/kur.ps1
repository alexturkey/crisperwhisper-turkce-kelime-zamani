# Windows sarmalayıcı / Windows wrapper: kurulumu WSL2 Ubuntu içinde çalıştırır (CTranslate2 çatalının yalnız Linux wheel'i var).
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\kur.ps1 -Kok E:\stt            # kök Windows yolu, WSL'de /mnt/e/stt olur
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\kur.ps1 -Kok E:\stt -Diller "tr en ja" -Dagitim Ubuntu
# Gerekenler: WSL2 + Ubuntu 22.04/24.04 (`wsl --install -d Ubuntu`, bir kez yönetici), Windows NVIDIA sürücüsü >= 570 (WSL'de nvidia-smi çalışır).
param(
    [string]$Kok = "",
    [string]$Dagitim = "Ubuntu",
    [string]$Diller = "tr en",
    [string]$Adim = ""
)
$ErrorActionPreference = "Stop"
if (-not $Kok) { throw "-Kok <Windows yolu> verin, ör. -Kok E:\stt (kısa, boşluksuz)" }
if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) { throw "wsl.exe yok. WSL2 kurun: wsl --install -d Ubuntu (yönetici, bir kez), sonra yeniden deneyin" }
$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
function WslYol([string]$p) {
    $tam = (Resolve-Path -LiteralPath $p -ErrorAction SilentlyContinue)
    if ($tam) { $p = $tam.Path }
    if ($p -notmatch '^[A-Za-z]:\\') { throw "mutlak Windows yolu gerekir: $p" }
    return "/mnt/" + $p.Substring(0, 1).ToLower() + ($p.Substring(2) -replace "\\", "/")
}
New-Item -ItemType Directory -Force $Kok | Out-Null
$repoW = WslYol $Repo; $kokW = WslYol $Kok
$argv = @("--kok", $kokW, "--diller", $Diller)
if ($Adim) { $argv += @("--adim", $Adim) }
Write-Output "WSL '$Dagitim' içinde: bash $repoW/scripts/kur.sh $($argv -join ' ')"
& wsl.exe -d $Dagitim -- bash "$repoW/scripts/kur.sh" @argv
if ($LASTEXITCODE -ne 0) { throw "kurulum WSL içinde başarısız (çıkış $LASTEXITCODE); üstteki son satırlara bakın" }
Write-Output "Windows'tan kullanım:  powershell -File scripts\stt.ps1 -Ses C:\ses\kayit.mp3 -Dil tr"
