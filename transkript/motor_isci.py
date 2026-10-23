"""ASR worker (runs in its own process, exits when done so the GPU memory is released before alignment).

  python -m transkript.motor_isci --istek istek.json --yanit yanit.json

Request: {"ses": "<16 kHz mono wav>", "dil": "tr" | "auto", "model": "<CT2 model dir>", "cihaz": "cuda",
          "compute_type": "int8", "max_new_tokens": 400}
Response: {"durum": "ok", "metin", "dil", "dil_adaylari", "kelimeler": [{"kelime","start","end"}], "sureler", "kimlik"}
Batch: {"isler": [{"ses", "dil"}, ...], "model", ...} -> {"durum": "ok", "sonuclar": [per-file result or
       {"durum": "hata"}], "sureler": <shared import/load>, "kimlik"}; the model is loaded once for all files.
Transcription parameters are the ones our production engine uses: verbatim mode, temperature fallback, hallucination
repair, early-EOT recovery, native word timestamps on (kept as diagnostics; delivered times come from CTC alignment).
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
import sys
import time
from pathlib import Path

ORNEKLEME = 16000
ILK_PENCERE_SN = 30.0


def _yaz(yol: Path, veri: dict) -> None:
    gecici = yol.with_name(yol.name + ".part")
    gecici.write_text(json.dumps(veri, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    gecici.replace(yol)


def _dil_tespit(model, ses) -> tuple[str, list[dict]]:
    """Language id on the first 30 s via the CTranslate2 Whisper model (private attributes of crisperwhisper 2.0.x)."""
    pencere = ses[: int(ILK_PENCERE_SN * ORNEKLEME)]
    motor = model._engine  # crisperwhisper.engine.CT2Engine
    ozellik = motor.extract_features(pencere)
    sonuc = motor.model.detect_language(ozellik)
    adaylar = []
    for token, olasilik in (sonuc[0] if sonuc else []):
        kod = str(token).strip()
        if kod.startswith("<|") and kod.endswith("|>"):
            kod = kod[2:-2]
        adaylar.append({"dil": kod.lower(), "olasilik": round(float(olasilik), 4)})
    adaylar.sort(key=lambda a: -a["olasilik"])
    if not adaylar:
        raise RuntimeError("dil tespiti aday döndürmedi")
    return adaylar[0]["dil"], adaylar[:5]


def _model_yukle(istek: dict, sureler: dict):
    t0 = time.perf_counter()
    import ctranslate2
    from crisperwhisper import CrisperWhisperModel

    sureler["import_sn"] = round(time.perf_counter() - t0, 3)
    cihaz = istek.get("cihaz", "cuda")
    compute = istek.get("compute_type", "int8")
    if cihaz == "cuda":
        destek = sorted(ctranslate2.get_supported_compute_types("cuda"))
        if compute not in destek:
            raise RuntimeError(f"CUDA {compute} desteklenmiyor; desteklenen: {destek}")
    t0 = time.perf_counter()
    model = CrisperWhisperModel(str(istek["model"]), backend="ct2", device=cihaz, compute_type=compute)
    sureler["model_yukleme_sn"] = round(time.perf_counter() - t0, 3)
    kimlik = {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "crisperwhisper": importlib.metadata.version("crisperwhisper"),
        "ctranslate2_crisperwhisper": importlib.metadata.version("ctranslate2-crisperwhisper"),
        "cihaz": cihaz,
        "compute_type": compute,
        "mod": "verbatim",
    }
    return model, kimlik


def _coz(model, is_: dict, max_new_tokens: int) -> dict:
    """One file with an already loaded model -> {"metin", "dil", "dil_adaylari", "kelimeler", "ses_sn", "sureler"}."""
    import soundfile

    sureler = {}
    ses, hiz = soundfile.read(is_["ses"], dtype="float32", always_2d=False)
    if hiz != ORNEKLEME or getattr(ses, "ndim", 1) != 1:
        raise RuntimeError("worker 16 kHz mono wav bekler")
    dil = str(is_.get("dil") or "auto").lower()
    adaylar: list[dict] = []
    if dil == "auto":
        t0 = time.perf_counter()
        dil, adaylar = _dil_tespit(model, ses)
        sureler["dil_tespit_sn"] = round(time.perf_counter() - t0, 3)
    t0 = time.perf_counter()
    sonuc = model.transcribe(
        ses, sr=ORNEKLEME, language=dil, mode="verbatim", word_timestamps=True, temperature_fallback=True,
        max_new_tokens=max_new_tokens, speculative_decoding=False,
        hallucination_mitigation=True, early_eot_recovery=True, suppress_tokens=None,
    )
    sureler["cozumleme_sn"] = round(time.perf_counter() - t0, 3)
    kelimeler = [
        {"kelime": str(w.word), "start": float(w.start), "end": float(w.end)}
        for w in (sonuc.words or []) if w.start is not None and w.end is not None and str(w.word).strip()
    ]
    return {
        "metin": str(sonuc.text).strip(),
        "dil": str(sonuc.language or dil),
        "dil_adaylari": adaylar,
        "kelimeler": kelimeler,
        "ses_sn": round(len(ses) / ORNEKLEME, 3),
        "sureler": sureler,
    }


def calistir(istek: dict) -> dict:
    """Single file (istek["ses"], istek["dil"]) or batch (istek["isler"] = [{"ses", "dil"}, ...]): the model loads once."""
    yuk: dict = {}
    model, kimlik = _model_yukle(istek, yuk)
    mnt = int(istek.get("max_new_tokens", 400))
    if "isler" not in istek:
        r = _coz(model, istek, mnt)
        return {"durum": "ok", **r, "sureler": {**yuk, **r["sureler"]}, "kimlik": kimlik}
    sonuclar = []
    for is_ in istek["isler"]:
        try:
            sonuclar.append({"durum": "ok", **_coz(model, is_, mnt)})
        except Exception as hata:  # one bad file does not stop the batch
            sonuclar.append({"durum": "hata", "hata": f"{type(hata).__name__}: {hata}"})
    return {"durum": "ok", "sonuclar": sonuclar, "sureler": yuk, "kimlik": kimlik}


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--istek", required=True)
    p.add_argument("--yanit", required=True)
    a = p.parse_args(argv)
    istek = json.loads(Path(a.istek).read_text(encoding="utf-8"))
    try:
        yanit = calistir(istek)
    except Exception as hata:  # the parent reads the error from the response file
        import traceback

        _yaz(Path(a.yanit), {"durum": "hata", "hata": f"{type(hata).__name__}: {hata}", "iz": traceback.format_exc()})
        return 1
    _yaz(Path(a.yanit), yanit)
    return 0


if __name__ == "__main__":
    sys.exit(main())
