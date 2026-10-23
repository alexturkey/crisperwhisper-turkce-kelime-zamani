#!/usr/bin/env bash
# Kurulum / installer (Linux ya da Windows WSL2 Ubuntu; NVIDIA GPU >= 4 GB, sürücü >= 570):
#   bash scripts/kur.sh --kok /mnt/e/stt            # her şey: venv + paketler + model (1,6 GB) + CT2 dönüşümü + hizalama modelleri + kontrol
#   bash scripts/kur.sh --kok /mnt/e/stt --adim python,model,hizalama,ayar,kontrol   # adım seç
#   bash scripts/kur.sh --kok /mnt/e/stt --diller "tr en ja"                       # hangi dillerin hizalama modeli insin
# Her adım yeniden çalıştırılabilir: sha256'sı doğru dosya atlanır. Hiçbir sistem ayarı, PATH ya da sudo gerekmez.
# Disk: ~7 GB (torch cu126 ~3 GB, model 1,6 GB indirme + 1,6 GB CT2, hizalama modelleri 0,4-1,3 GB/dil).
set -euo pipefail
KOK=""
ADIM=""
DILLER="tr en"
PY="${PYTHON:-python3}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --kok) KOK="$2"; shift 2 ;;
    --adim) ADIM="$2"; shift 2 ;;
    --diller) DILLER="$2"; shift 2 ;;
    --python) PY="$2"; shift 2 ;;
    *) echo "bilinmeyen seçenek: $1"; exit 2 ;;
  esac
done
[[ -z "$KOK" ]] && { echo "--kok <kurulum kökü> gerekli (ör. /mnt/e/stt ya da ~/stt)"; exit 2; }
[[ -z "$ADIM" ]] && ADIM="python,model,hizalama,ayar,kontrol"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$KOK"/{indirme,model,hf,torch,pip}
export HF_HOME="$KOK/hf" PIP_CACHE_DIR="$KOK/pip" TORCH_HOME="$KOK/torch" HF_HUB_DISABLE_SYMLINKS_WARNING=1 TMPDIR="$KOK/indirme"
VENV="$REPO/.venv"
VPY="$VENV/bin/python"
echo "adımlar: $ADIM · kök: $KOK · diller: $DILLER"

adim() { [[ ",$ADIM," == *",$1,"* ]]; }

# --- sabitler: ayarlar/manifest.json (commit + sha256) ---------------------------------------------------------------
manifest() { "$PY" - "$REPO/ayarlar/manifest.json" "$1" <<'EOF'
import json, sys
m = json.load(open(sys.argv[1], encoding="utf-8"))
for k in sys.argv[2].split("."):
    m = m[k]
print(m if not isinstance(m, list) else " ".join(m))
EOF
}
sha256() { sha256sum "$1" | cut -d' ' -f1; }
indir() {  # indir <url> <hedef> [<sha256>]: .part + doğrulama; var ve doğruysa atlar
  local url="$1" hedef="$2" sha="${3:-}"
  if [[ -f "$hedef" && -n "$sha" && "$(sha256 "$hedef")" == "$sha" ]]; then echo "  var ve doğru: $(basename "$hedef")"; return; fi
  echo "  indiriliyor: $url"
  curl -L --proto "=https" --tlsv1.2 --fail --retry 3 --retry-delay 5 --progress-bar -o "$hedef.part" "$url"
  if [[ -n "$sha" ]]; then
    local got; got="$(sha256 "$hedef.part")"
    if [[ "$got" != "$sha" ]]; then rm -f "$hedef.part"; echo "sha256 tutmadı: $hedef"; echo "  beklenen $sha"; echo "  gelen    $got"; exit 1; fi
  fi
  mv -f "$hedef.part" "$hedef"
  echo "  tamam$( [[ -n "$sha" ]] && echo ', sha256 doğru'): $(basename "$hedef")"
}

if adim python; then
  echo "== python (.venv + requirements.txt; torch cu126 ~3 GB; cu128 Linux wheels have no Pascal/sm_61 kernels)"
  "$PY" -c 'import sys; assert sys.version_info >= (3, 10), "Python 3.10+ gerekir"; print("python", sys.version.split()[0])'
  [[ -x "$VPY" ]] || "$PY" -m venv "$VENV"
  "$VPY" -m pip install --quiet --disable-pip-version-check --upgrade pip
  "$VPY" -m pip install --quiet --disable-pip-version-check -r "$REPO/requirements.txt" --extra-index-url https://download.pytorch.org/whl/cu126
  "$VPY" -m pip check
  "$VPY" -c 'import ctranslate2, torch, crisperwhisper; print("ctranslate2", ctranslate2.__version__, "torch", torch.__version__, "crisperwhisper", crisperwhisper.__version__)'
  echo "PYTHON_OK"
fi

if adim model; then
  echo "== model: nyralabs/CrisperWhisper2.0_turbo (sabit commit; ağırlık lisansı: ticari olmayan araştırma, bkz. NOTICE)"
  COMMIT="$(manifest asr.commit)"; SHA="$(manifest asr.safetensors_sha256)"
  SRC="$KOK/model/hf_turbo_$COMMIT"; mkdir -p "$SRC"
  for f in $(manifest asr.dosyalar); do
    if [[ "$f" == "model.safetensors" ]]; then indir "https://huggingface.co/nyralabs/CrisperWhisper2.0_turbo/resolve/$COMMIT/$f" "$SRC/$f" "$SHA"
    else indir "https://huggingface.co/nyralabs/CrisperWhisper2.0_turbo/resolve/$COMMIT/$f" "$SRC/$f"; fi
  done
  [[ "$(stat -c %s "$SRC/model.safetensors")" == "$(manifest asr.safetensors_bayt)" ]] || { echo "model boyutu beklenen değil"; exit 1; }
  echo "MODEL_OK"
  echo "== CT2 dönüşümü (float16 depolama, int8 çalışma; ~1-3 dk, RAM ~4 GB)"
  if [[ -f "$KOK/model/ct2_turbo/donusum_kaydi.json" ]] && "$VPY" - "$KOK/model/ct2_turbo/donusum_kaydi.json" "$COMMIT" "$SHA" <<'EOF'
import json, sys
k = json.load(open(sys.argv[1], encoding="utf-8"))
sys.exit(0 if k.get("kaynak_commit") == sys.argv[2] and k.get("kaynak_sha256") == sys.argv[3] else 1)
EOF
  then echo "  CT2 modeli var ve kaynağı doğru"; else "$VPY" -m transkript.donustur --kaynak "$SRC" --hedef "$KOK/model/ct2_turbo"; fi
  # CT2 çekirdeğinin okuduğu config.json (lang_ids ...) eksikse türet (eski dönüşümler için de)
  grep -q '"lang_ids"' "$KOK/model/ct2_turbo/config.json" 2>/dev/null || "$VPY" -m transkript.donustur --yalniz-config --hedef "$KOK/model/ct2_turbo"
  echo "DONUSUM_OK"
fi

if adim hizalama; then
  echo "== hizalama modelleri (wav2vec2 CTC): $DILLER"
  # shellcheck disable=SC2086
  "$VPY" -m transkript.kur_hizalama --kok "$KOK" --diller $DILLER
fi

if adim ayar; then
  echo "== ayarlar.json"
  "$VPY" - "$REPO/ayarlar.json" "$KOK" <<'EOF'
import json, sys
kok = sys.argv[2]
json.dump({"kok": kok, "model": kok + "/model/ct2_turbo", "hf_home": kok + "/hf", "torch_home": kok + "/torch", "cihaz": "cuda", "compute_type": "int8"},
          open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
EOF
  echo "  yazıldı: $REPO/ayarlar.json"
  echo "AYAR_OK"
fi

if adim kontrol; then
  echo "== kontrol: CUDA int8 + torch CUDA + model"
  (cd "$REPO" && "$VPY" -m transkript --kontrol)
fi
echo "KURULUM_OK"
echo "Deneme:  $VPY -m transkript ornek/ornek.mp3 --dil tr"
