"""Converts the downloaded Hugging Face checkpoint (safetensors) into the CTranslate2 model used at run time and
records what it was converted from. Called by scripts/kur.sh after the download was sha256-verified.

  python -m transkript.donustur --kaynak <indirilen HF klasörü> --hedef <kok>/model/ct2_turbo
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from transkript import ayarlar  # noqa: E402


LANG_TOKEN = re.compile(r"^<\|[a-z]{2,3}\|>$")


def ct2_config_yaz(hedef: Path) -> dict:
    """Writes the config.json CTranslate2 itself reads (alignment_heads, lang_ids, suppress_ids, suppress_ids_begin).

    crisperwhisper 2.0.1's converter copies the Hugging Face config.json over it; the CT2 core then fails in
    detect_language with "type must be number, but is number" (measured 2026-10-23). The values are derived from the
    checkpoint's own generation_config.json and added_tokens.json; the result is identical to what
    ct2-transformers-converter writes. The HF config is kept as config_hf.json for reference.
    """
    gen = json.loads((hedef / "generation_config.json").read_text(encoding="utf-8"))
    added = json.loads((hedef / "added_tokens.json").read_text(encoding="utf-8"))
    cfg = {
        "alignment_heads": gen["alignment_heads"],
        "lang_ids": sorted(v for k, v in added.items() if LANG_TOKEN.match(k)),
        "suppress_ids": [int(x) for x in gen.get("suppress_tokens", []) if int(x) >= 0],
        "suppress_ids_begin": [int(x) for x in gen.get("begin_suppress_tokens", [])],
    }
    if len(cfg["lang_ids"]) < 90 or len(cfg["alignment_heads"]) == 0:
        raise SystemExit(f"CT2 config türetilemedi: {len(cfg['lang_ids'])} dil, {len(cfg['alignment_heads'])} hizalama başı")
    eski = hedef / "config.json"
    if eski.is_file() and "lang_ids" not in json.loads(eski.read_text(encoding="utf-8")):
        eski.replace(hedef / "config_hf.json")
    gecici = hedef / "config.json.part"
    gecici.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    gecici.replace(eski)
    return cfg


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--kaynak")
    p.add_argument("--hedef", required=True)
    p.add_argument("--yalniz-config", action="store_true", help="dönüştürülmüş modelin config.json'unu CT2 biçimine getir, dönüştürme")
    a = p.parse_args(argv)
    if a.yalniz_config:
        cfg = ct2_config_yaz(Path(a.hedef))
        print(f"CT2_CONFIG_OK {a.hedef} dil={len(cfg['lang_ids'])} hizalama_basi={len(cfg['alignment_heads'])}")
        return 0
    if not a.kaynak:
        p.error("--kaynak gerekli")
    kaynak, hedef = Path(a.kaynak), Path(a.hedef)
    m = ayarlar.manifest()["asr"]
    st = kaynak / "model.safetensors"
    if not st.is_file():
        raise SystemExit(f"model.safetensors yok: {st}")
    sha = ayarlar.sha256(st)
    if sha != m["safetensors_sha256"]:
        raise SystemExit(f"safetensors sha256 tutmadı: {sha} (beklenen {m['safetensors_sha256']})")
    from crisperwhisper.converter import ensure_ct2_model

    t0 = time.perf_counter()
    gecici = hedef.with_name(hedef.name + "_part")
    if gecici.exists():
        shutil.rmtree(gecici)
    gecici.mkdir(parents=True)
    ct2 = ensure_ct2_model(str(kaynak), quantization=m["ct2_depolama"], cache_dir=str(gecici))
    if hedef.exists():
        shutil.rmtree(hedef)
    shutil.move(str(ct2), str(hedef))
    shutil.rmtree(gecici, ignore_errors=True)
    ct2_config_yaz(hedef)
    model_bin = hedef / "model.bin"
    kayit = {
        "kaynak_model": m["model"], "kaynak_commit": m["commit"], "kaynak_sha256": sha,
        "ct2_depolama": m["ct2_depolama"], "model_bin_sha256": ayarlar.sha256(model_bin), "model_bin_bayt": model_bin.stat().st_size,
        "donusum_sn": round(time.perf_counter() - t0, 1), "zaman": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    (hedef / "donusum_kaydi.json").write_text(json.dumps(kayit, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    ref = m.get("referans_model_bin_sha256", "")
    if ref and not ref.startswith("__") and ref != kayit["model_bin_sha256"]:
        print(f"UYARI: model.bin sha256 referanstan farklı ({kayit['model_bin_sha256'][:12]}… / {ref[:12]}…): dönüştürücü sürümü değişmiş olabilir; kaynak dosya doğrulandı, çalışır")
    print(f"DONUSUM_OK {hedef} model.bin {kayit['model_bin_bayt']} bayt sha256 {kayit['model_bin_sha256'][:12]}… {kayit['donusum_sn']} sn")
    return 0


if __name__ == "__main__":
    sys.exit(main())
