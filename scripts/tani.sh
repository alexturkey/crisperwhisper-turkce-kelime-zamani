#!/usr/bin/env bash
# Yerel teşhis raporu / local diagnosis report (Linux ya da WSL2):
#   bash scripts/tani.sh                # kısa rapor: sistem, kart, Python, disk, RAM, depo sürümü, kurulum işaretleri
#   bash scripts/tani.sh --kart-satiri  # tek satır: issue formundaki "makine" alanı için
# Yalnız okur: hiçbir şey yazmaz, ağa çıkmaz, kendiliğinden hiçbir yere göndermez. Çıktıdan ev klasörü yolu, kullanıcı adı ve
# makine adı silinir (<HOME>, <USER>, <HOST>); yine de issue'ya koymadan önce kendiniz bir kez okuyun.
set -u
KART=0
[[ "${1:-}" == "--kart-satiri" ]] && KART=1
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KULLANICI="$(id -un 2>/dev/null || echo "")"
MAKINE="$(hostname 2>/dev/null || echo "")"

suz() {  # kişisel adı/yolu silen süzgeç
  local satir
  while IFS= read -r satir; do
    satir="${satir//$HOME/<HOME>}"
    [[ -n "$KULLANICI" && ${#KULLANICI} -ge 3 ]] && satir="${satir//$KULLANICI/<USER>}"
    [[ -n "$MAKINE" && ${#MAKINE} -ge 3 ]] && satir="${satir//$MAKINE/<HOST>}"
    # /mnt/c/Users/<ad>/... gibi Windows kullanıcı yolu
    satir="$(printf '%s' "$satir" | sed -E 's#(/mnt/[a-z]/[Uu]sers/)[^/ ]+#\1<USER>#g; s#([A-Za-z]:\\[Uu]sers\\)[^\\ ]+#\1<USER>#g')"
    printf '%s\n' "$satir"
  done
}

GPU="nvidia-smi yok"
if command -v nvidia-smi >/dev/null 2>&1; then
  GPU="$(nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader 2>/dev/null | head -n 1)"
  [[ -z "$GPU" ]] && GPU="nvidia-smi çalışıyor ama kart göstermiyor"
fi
if grep -qi microsoft /proc/version 2>/dev/null; then ORTAM="WSL2"; else ORTAM="Linux"; fi
SISTEM="$(. /etc/os-release 2>/dev/null && echo "${PRETTY_NAME:-linux}" || uname -sr)"
RAM_KB="$(awk '/^MemTotal:/ {print $2}' /proc/meminfo 2>/dev/null || true)"
RAM="?"; [[ "$RAM_KB" =~ ^[0-9]+$ ]] && RAM="$((RAM_KB / 1048576)) GiB"

if [[ "$KART" == 1 ]]; then
  echo "$GPU | $ORTAM, $SISTEM | RAM $RAM" | suz
  exit 0
fi

rapor() {
echo "== STT tanı raporu (yerel, hiçbir yere gönderilmez)"
echo "sistem: $ORTAM, $SISTEM, $(uname -m)"
echo "kart: $GPU"
echo "RAM: $RAM"
PYV="$(python3 -c 'import sys; print(sys.version.split()[0])' 2>/dev/null || echo "python3 yok")"
echo "python3: $PYV"
for arac in ffmpeg sha256sum curl; do
  if command -v "$arac" >/dev/null 2>&1; then echo "$arac: var"; else echo "$arac: yok"; fi
done
BOS="$(df -Pk "$REPO" 2>/dev/null | awk 'NR==2 {printf "%d GiB", $4/1048576}')"
echo "boş disk (depo klasörü): ${BOS:-?}"
if [[ -d "$REPO/.git" ]] && command -v git >/dev/null 2>&1; then
  echo "depo sürümü: $(git -C "$REPO" log -1 --format='%h %cs' 2>/dev/null || echo '?')"
fi
echo "ayarlar.json: $([[ -f "$REPO/ayarlar.json" ]] && echo var || echo yok)"
echo ".venv: $([[ -x "$REPO/.venv/bin/python" ]] && echo var || echo yok)"
if [[ -x "$REPO/.venv/bin/python" ]]; then
  echo "torch/ct2: $("$REPO/.venv/bin/python" -I -c 'import torch, ctranslate2; print("torch", torch.__version__, "cuda", torch.cuda.is_available(), "| ctranslate2", ctranslate2.__version__)' 2>&1 | tail -n 1)"
fi
echo "SAPMA / DEVIATIONS (salt okur):"
echo "  PATH'te ilk python3: $(command -v python3 2>/dev/null || echo yok) ($PYV)"
if [[ -d "$REPO/.git" ]] && command -v git >/dev/null 2>&1; then
  DEG="$(git --no-optional-locks -C "$REPO" status --short -uno 2>/dev/null | head -40)"
  if [[ -z "$DEG" ]]; then echo "  git: izlenen dosyalar değişmemiş"; else echo "  git: değişmiş izlenen dosyalar (yalnız adlar):"; echo "$DEG" | sed 's/^/    /'; fi
fi
SENV="$(env | awk -F= '/^(STT_|HF_|PIP_|TORCH_|CT2_)/ {print $1}' | sort | tr '
' ' ')"
echo "  STT_/HF_/PIP_/TORCH_ ortam değişkenleri (yalnız adlar, değerler basılmaz): ${SENV:-yok}"
echo "-- sorun için: docs/SIK_HATALAR.md; kurulum öncesi denetim: bash scripts/kur.sh --kok <kök> --kuru"
echo "-- Bu çıktıyı issue'ya koymadan önce kendiniz okuyun; kişisel ad ve yollar <HOME>/<USER>/<HOST> ile silindi."
}
rapor | suz
