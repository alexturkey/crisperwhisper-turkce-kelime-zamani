"""Settings: where the models live. `kur.sh` writes ayarlar.json next to this package's repo root; the environment
variable TRANSKRIPT_KOK or --kok on the command line overrides it."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
AYAR_DOSYASI = REPO / "ayarlar.json"
MANIFEST = REPO / "ayarlar" / "manifest.json"


def yukle(kok: str | None = None) -> dict:
    ayar = {}
    if AYAR_DOSYASI.is_file():
        ayar = json.loads(AYAR_DOSYASI.read_text(encoding="utf-8"))
    kok = kok or os.environ.get("TRANSKRIPT_KOK") or ayar.get("kok")
    if not kok:
        raise SystemExit("kurulum kökü bilinmiyor: önce scripts/kur.sh çalıştırın ya da --kok verin")
    k = Path(kok)
    ayar.setdefault("kok", str(k))
    ayar.setdefault("model", str(k / "model" / "ct2_turbo"))
    ayar.setdefault("hf_home", str(k / "hf"))
    ayar.setdefault("cihaz", "cuda")
    ayar.setdefault("compute_type", "int8")
    return ayar


def manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def sha256(yol: Path) -> str:
    h = hashlib.sha256()
    with yol.open("rb") as f:
        while parca := f.read(8 * 1024 * 1024):
            h.update(parca)
    return h.hexdigest()


def model_dogrula(model_dizini: Path) -> dict:
    """Checks the converted CT2 model against the local conversion record (written by kur.sh)."""
    kayit = model_dizini / "donusum_kaydi.json"
    if not (model_dizini / "model.bin").is_file():
        raise SystemExit(f"CT2 modeli yok: {model_dizini} (scripts/kur.sh --adim model)")
    if not kayit.is_file():
        raise SystemExit(f"dönüşüm kaydı yok: {kayit} (kurulum yarım kalmış olabilir; kur.sh --adim model)")
    veri = json.loads(kayit.read_text(encoding="utf-8"))
    beklenen = manifest()["asr"]
    if veri.get("kaynak_commit") != beklenen["commit"] or veri.get("kaynak_sha256") != beklenen["safetensors_sha256"]:
        raise SystemExit("CT2 modeli manifestteki kaynak commit/sha ile dönüştürülmemiş; kur.sh --adim model")
    return veri
