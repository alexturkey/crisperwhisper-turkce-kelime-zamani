#!/usr/bin/env bash
# PR öncesi yerel kontrol / pre-PR local check (Linux, WSL2, macOS, Git Bash): tek komut, birkaç saniye, GPU yok, ağ yok.
#   bash scripts/on_kontrol.sh
# 1) hızlı denetim (scripts/denetim.py --hizli)  2) birim testleri (pytest kuruluysa).  Hiçbir dosyayı değiştirmez.
# Python yoksa net ileti verir ve çıkış 3 ile durur (yeşil sayılmaz).
set -u
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY=""
for aday in "$REPO/.venv/bin/python" python3 python; do
  if "$aday" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1; then PY="$aday"; break; fi
done
if [[ -z "$PY" ]]; then
  echo "HATA: Python bulunamadı. Python 3.8+ kurun (Ubuntu: sudo apt install python3) ve yeniden deneyin."
  echo "SONUC: ON KONTROL CALISMADI (cikis 3)"; exit 3
fi
cd "$REPO" || exit 3
"$PY" -I -X utf8 scripts/denetim.py --hizli; KOD=$?
if [[ "$KOD" -ne 0 ]]; then echo "SONUC: ON KONTROL KIRMIZI (cikis $KOD): hızlı denetim"; exit "$KOD"; fi
if "$PY" -c 'import pytest' >/dev/null 2>&1; then
  "$PY" -m pytest tests -q -p no:cacheprovider; KOD=$?
  if [[ "$KOD" -ne 0 ]]; then echo "SONUC: ON KONTROL KIRMIZI (cikis 1): birim testleri"; exit 1; fi
  echo "SONUC: ON KONTROL GECTI (cikis 0): hızlı denetim ve birim testleri"
else
  echo "UYARI: pytest kurulu değil, birim testleri atlandı (pip install pytest numpy soundfile soxr)"
  echo "SONUC: ON KONTROL GECTI (cikis 0): yalnız hızlı denetim"
fi
