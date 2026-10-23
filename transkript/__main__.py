"""Command line:

  python -m transkript ses.mp3                       # -> cikti/<ad>/ : transkript.txt, kelimeler.json, .srt, .vtt
  python -m transkript ses.wav --dil en --cikti out  # language given (default tr; "auto" = detect on first 30 s)
  python -m transkript a.mp3 b.wav --cikti out        # batch: models load once -> out/<ad>/ for each file
  python -m transkript --liste isler.tsv --cikti out   # batch, one file per line: <path>[<TAB><lang>]
  python -m transkript --kontrol                      # environment + model check, prints KONTROL_OK
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from transkript import __version__, ayarlar
from transkript.diller import HF, SINANMIS, TORCHAUDIO, dil_kodu


def kontrol(ayar: dict) -> int:
    import ctranslate2
    import torch

    tipler = sorted(ctranslate2.get_supported_compute_types("cuda")) if ayar.get("cihaz", "cuda") == "cuda" else ["cpu"]
    print(f"ctranslate2-crisperwhisper {ctranslate2.__version__} · CUDA compute types: {', '.join(tipler)}")
    print(f"torch {torch.__version__} · cuda {torch.cuda.is_available()} · {torch.cuda.get_device_name(0) if torch.cuda.is_available() else '-'}")
    if ayar.get("cihaz", "cuda") == "cuda" and (ayar.get("compute_type", "int8") not in tipler or not torch.cuda.is_available()):
        print("KONTROL_HATA: CUDA int8 ya da torch CUDA yok (sürücü ≥ 570, cu126 wheel, WSL2'de nvidia-smi çalışıyor mu?)")
        return 1
    if ayar.get("cihaz", "cuda") == "cuda":
        # is_available() is not enough: a wheel without kernels for this GPU's arch still reports True
        # (Linux cu128 + sm_61 -> "no kernel image is available"), so run one real kernel.
        try:
            x = torch.ones(64, 64, device="cuda")
            assert float((x @ x)[0, 0]) == 64.0
            print(f"torch CUDA kernel OK · arch {torch.cuda.get_device_capability(0)} · wheel {torch.cuda.get_arch_list()}")
        except Exception as e:  # noqa: BLE001
            print(f"KONTROL_HATA: torch CUDA kernel failed ({e}); install the cu126 wheel (requirements.txt)")
            return 1
    kayit = ayarlar.model_dogrula(Path(ayar["model"]))
    print(f"model: {ayar['model']} · kaynak commit {kayit['kaynak_commit'][:12]} · model.bin sha256 {kayit.get('model_bin_sha256', '?')[:12]}…")
    print("KONTROL_OK")
    return 0


def toplu(isler: list[tuple[Path, str]], a, ayar: dict, bicimler: set[str]) -> int:
    from transkript import akis

    kok = Path(a.cikti) if a.cikti else ayarlar.REPO / "cikti" / f"toplu_{time.strftime('%Y%m%d_%H%M%S')}"
    adlar: dict[str, int] = {}
    hedefler = []
    for kaynak, d in isler:
        n = adlar[kaynak.stem] = adlar.get(kaynak.stem, 0) + 1
        hedefler.append((kaynak, kok / (kaynak.stem if n == 1 else f"{kaynak.stem}_{n}"), d))
    sonuclar = akis.calistir_toplu(hedefler, kok / "_toplu", ayar, bicimler, a.hizalama_modeli, a.hizalama_cihazi,
                                   a.zaman_asimi, a.hizalama_revizyon)
    hata = 0
    for (kaynak, klasor, _), s in zip(hedefler, sonuclar):
        if s["durum"] != "ok":
            hata += 1
            print(f"TRANSKRIPT_HATA {kaynak.name}: {s['hata']}")
            continue
        not_ = "" if s["sinanmis_dil"] else " (DENEYSEL dil)"
        print(f"TRANSKRIPT_OK {kaynak.name} dil={s['dil']}{not_} ses={s['ses_sn']} sn kelime={len(s['kelimeler'])} "
              f"asr={s['sureler']['asr_cozumleme_sn']} sn hizalama={s['sureler']['hizalama_sn']} sn CIKTI={klasor}")
    t = sonuclar[0]["toplu"] if sonuclar else {}
    vram = max(t.get("vram_tepe_mb_asr", 0), t.get("vram_tepe_mb_hizalama", 0))
    print(f"TOPLU_OK dosya={len(isler)} hata={hata} toplam={t.get('toplam_sn')} sn asr_sureci={t.get('asr_surec_sn')} sn "
          f"hizalama_sureci={t.get('hizalama_surec_sn')} sn vram_tepe={vram} MB")
    ozet = {"toplu": t, "dosyalar": [{k: s.get(k) for k in ("durum", "kaynak", "dil", "ses_sn", "metin", "hata", "sureler")} for s in sonuclar]}
    (kok / "_toplu" / "ozet.json").write_text(json.dumps(ozet, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 1 if hata else 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="transkript", description="verbatim transkript + kelime zamanı (CrisperWhisper 2.0 Turbo CT2 + wav2vec2 CTC)")
    p.add_argument("ses", nargs="*", help="ses/video dosyası (birden çok verilirse toplu kip: modeller bir kez yüklenir)")
    p.add_argument("--liste", help="toplu kip: her satır <dosya>[<TAB><dil>]; dil yoksa --dil")
    p.add_argument("--dil", default="tr", help="dil kodu (tr, en, ja, ...) ya da auto; varsayılan tr")
    p.add_argument("--cikti", help="çıktı klasörü (varsayılan cikti/<dosya adı>_<zaman>)")
    p.add_argument("--bicim", default="json,srt,vtt", help="virgüllü: json,srt,vtt")
    p.add_argument("--kok", help="kurulum kökü (ayarlar.json / TRANSKRIPT_KOK yerine)")
    p.add_argument("--hizalama-modeli", help="HF wav2vec2 CTC modeli (tablodaki dil modelinin yerine ya da tabloda olmayan dil için)")
    p.add_argument("--hizalama-revizyon", help="--hizalama-modeli için sabit commit (önerilir; verilmezse HF main)")
    p.add_argument("--hizalama-cihazi", choices=("cuda", "cpu"), help="hizalamayı CPU'da koştur (yavaş; GPU belleği yetmezse)")
    p.add_argument("--zaman-asimi", type=int, default=3600)
    p.add_argument("--kontrol", action="store_true", help="ortam ve model kontrolü")
    p.add_argument("--diller", action="store_true", help="hizalama modeli olan dilleri listele")
    p.add_argument("--surum", action="store_true")
    a = p.parse_args(argv)
    for akis in (sys.stdout, sys.stderr):
        try:
            akis.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    if a.surum:
        print(__version__)
        return 0
    if a.diller:
        for kod in sorted(set(TORCHAUDIO) | set(HF)):
            print(f"{kod}\t{'sınanmış' if kod in SINANMIS else 'deneysel'}\t{TORCHAUDIO.get(kod) or HF.get(kod)}")
        return 0
    ayar = ayarlar.yukle(a.kok)
    if a.kontrol:
        return kontrol(ayar)
    dil = a.dil.strip().lower()
    if dil != "auto":
        dil = dil_kodu(dil)
    isler: list[tuple[Path, str]] = [(Path(x), dil) for x in a.ses]
    if a.liste:
        for satir in Path(a.liste).read_text(encoding="utf-8").splitlines():
            parca = [x.strip() for x in satir.split("\t")]
            if not parca[0] or parca[0].startswith("#"):
                continue
            d = parca[1].lower() if len(parca) > 1 and parca[1] else dil
            isler.append((Path(parca[0]), d if d == "auto" else dil_kodu(d)))
    if not isler:
        p.error("ses dosyası verin (ya da --liste / --kontrol / --diller)")
    for kaynak, _ in isler:
        if not kaynak.is_file():
            p.error(f"dosya yok: {kaynak}")
    bicimler = {b.strip() for b in a.bicim.split(",") if b.strip()}
    if len(isler) > 1 or a.liste:
        return toplu(isler, a, ayar, bicimler)
    kaynak, dil = isler[0]
    klasor = Path(a.cikti) if a.cikti else ayarlar.REPO / "cikti" / f"{kaynak.stem}_{time.strftime('%Y%m%d_%H%M%S')}"
    from transkript import akis

    sonuc = akis.calistir(kaynak, klasor, dil, ayar, bicimler, a.hizalama_modeli, a.hizalama_cihazi, a.zaman_asimi, a.hizalama_revizyon)
    not_ = "" if sonuc["sinanmis_dil"] else " (DENEYSEL dil: bizde ölçülmedi)"
    print(f"TRANSKRIPT_OK dil={sonuc['dil']}{not_} ses={sonuc['ses_sn']} sn kelime={len(sonuc['kelimeler'])} "
          f"toplam={sonuc['sureler']['toplam_sn']} sn vram_tepe={max(sonuc['vram_tepe_mb'].values())} MB")
    print(f"CIKTI={klasor}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
