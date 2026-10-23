"""CTC forced-alignment worker (own process; loads torch + a wav2vec2 CTC model, exits when done).

  python -m transkript.hizalama_isci --istek istek.json --yanit yanit.json

Request: {"ses": "<16 kHz mono wav>", "dil": "tr", "cihaz": "cuda", "model": null | "<hf id>", "revizyon": null | "<sha>",
          "segmentler": [{"start", "end", "birimler": ["kelime", ...]}]}
Response: {"durum": "ok", "kelimeler": [{"kelime", "start", "end", "skor", "yontem"}], "profil": {...}}
Batch: {"cihaz", "isler": [{"ses", "dil", "model", "revizyon", "segmentler"}, ...]} -> {"durum": "ok", "sonuclar": [...],
       "sureler": <shared import/load>, "torch_vram_tepe_mb"}; each alignment model loads once.

Method (same idea as the ctc_speech_bounded policy of our production engine, without WhisperX):
  1. per segment, wav2vec2 emissions (log-probs per 20 ms frame);
  2. torchaudio.functional.forced_align over the segment's characters (words separated by the model's "|" token);
  3. merge_tokens -> span of every character; a unit's time = first char start .. last char end. Blank frames are
     outside the spans, so the time is bounded to where the model heard speech (no silence swallowed into words).
  Characters the model vocabulary lacks are dropped for alignment; a unit left with no character is interpolated
  between its neighbours ("yontem": "ara_deger"). If a segment has more characters than frames the units are spread
  evenly ("esit_bolme"). Units with real alignment carry "yontem": "ctc" and a mean per-character probability "skor".
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from transkript.diller import bosluksuz_mu, hizalama_modeli, kucult  # noqa: E402

ORNEKLEME = 16000


def _yaz(yol: Path, veri: dict) -> None:
    gecici = yol.with_name(yol.name + ".part")
    gecici.write_text(json.dumps(veri, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    gecici.replace(yol)


class HizalamaModeli:
    """Uniform wrapper over torchaudio pipelines and Hugging Face Wav2Vec2ForCTC checkpoints."""

    def __init__(self, dil: str, cihaz: str, ozel_model: str | None, ozel_revizyon: str | None):
        import torch

        self.torch = torch
        self.cihaz = cihaz
        kaynak, ad, revizyon = hizalama_modeli(dil, ozel_model)
        self.kaynak, self.ad, self.revizyon = kaynak, ad, (ozel_revizyon or revizyon)
        if kaynak == "torchaudio":
            import torchaudio

            paket = getattr(torchaudio.pipelines, ad)
            self.model = paket.get_model().to(cihaz).eval()
            etiketler = list(paket.get_labels())
            self.sozluk = {e: i for i, e in enumerate(etiketler)}
            self.blank = 0  # torchaudio bundles: index 0 is "-" (blank)
            self.ayirici = "|"
            self.buyuk_harf = True
            self.hf_islemci = None
        else:
            from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

            self.hf_islemci = Wav2Vec2Processor.from_pretrained(ad, revision=self.revizyon)
            self.model = Wav2Vec2ForCTC.from_pretrained(ad, revision=self.revizyon).to(cihaz).eval()
            tok = self.hf_islemci.tokenizer
            self.sozluk = dict(tok.get_vocab())
            self.blank = int(tok.pad_token_id)
            self.ayirici = tok.word_delimiter_token if tok.word_delimiter_token in self.sozluk else None
            self.buyuk_harf = all(k == k.upper() for k in self.sozluk if k.isalpha())

    def emisyon(self, dalga):
        """-> (log_probs [T, V] on CPU, seconds per frame)"""
        torch = self.torch
        with torch.inference_mode():
            x = torch.from_numpy(dalga).to(self.cihaz)[None]
            if self.hf_islemci is not None:
                giris = self.hf_islemci(dalga, sampling_rate=ORNEKLEME, return_tensors="pt")
                x = giris.input_values.to(self.cihaz)
                logits = self.model(x).logits
            else:
                logits, _ = self.model(x)
            logp = torch.log_softmax(logits[0].float(), dim=-1).cpu()
        return logp, (len(dalga) / ORNEKLEME) / logp.shape[0]


def _karakterler(birim: str, m: HizalamaModeli, dil: str) -> list[str]:
    metin = unicodedata.normalize("NFC", birim)
    metin = metin.upper() if m.buyuk_harf else kucult(metin, dil)
    return [ch for ch in metin if ch in m.sozluk and ch != m.ayirici and m.sozluk[ch] != m.blank]


def _segment_hizala(m: HizalamaModeli, dalga, segment: dict, dil: str) -> list[dict]:
    import torchaudio.functional as F

    torch = m.torch
    birimler = [str(b) for b in segment["birimler"]]
    t0 = float(segment["start"])
    sure = float(segment["end"]) - t0
    bosluksuz = bosluksuz_mu(dil)
    hedef: list[int] = []
    sahipler: list[int] = []  # for every target token: index of the unit it belongs to (-1 = delimiter)
    hizalanan: list[bool] = []
    for i, b in enumerate(birimler):
        harfler = _karakterler(b, m, dil)
        hizalanan.append(bool(harfler))
        if harfler and hedef and m.ayirici and not bosluksuz and sahipler[-1] != -1:
            hedef.append(m.sozluk[m.ayirici]); sahipler.append(-1)
        for ch in harfler:
            hedef.append(m.sozluk[ch]); sahipler.append(i)
    sonuc = [{"kelime": b, "start": None, "end": None, "skor": None, "yontem": "ara_deger"} for b in birimler]
    if not hedef:
        return _esit_bol(sonuc, t0, sure, "esit_bolme")
    logp, kare_sn = m.emisyon(dalga)
    if len(hedef) + 1 > logp.shape[0]:
        return _esit_bol(sonuc, t0, sure, "esit_bolme")
    try:
        hiza, skor = F.forced_align(logp[None], torch.tensor([hedef], dtype=torch.int32), blank=m.blank)
    except Exception:  # degenerate emissions (e.g. repeated chars needing more frames than available)
        return _esit_bol(sonuc, t0, sure, "esit_bolme")
    spans = F.merge_tokens(hiza[0], skor[0].exp(), blank=m.blank)
    if len(spans) != len(hedef):
        return _esit_bol(sonuc, t0, sure, "esit_bolme")
    for span, sahip in zip(spans, sahipler):
        if sahip < 0:
            continue
        s, e = t0 + span.start * kare_sn, t0 + span.end * kare_sn
        k = sonuc[sahip]
        k["start"] = s if k["start"] is None else min(k["start"], s)
        k["end"] = e if k["end"] is None else max(k["end"], e)
        k["yontem"] = "ctc"
    sayac: dict[int, list[float]] = {}  # mean per-character probability per unit
    for span, sahip in zip(spans, sahipler):
        if sahip >= 0:
            sayac.setdefault(sahip, []).append(float(span.score))
    for i, sk in sayac.items():
        sonuc[i]["skor"] = round(sum(sk) / len(sk), 4)
    _ara_deger(sonuc, t0, t0 + sure)
    return sonuc


def _esit_bol(sonuc: list[dict], t0: float, sure: float, yontem: str) -> list[dict]:
    n = len(sonuc)
    agirlik = [max(1, len(k["kelime"])) for k in sonuc]
    toplam = float(sum(agirlik))
    t = t0
    for k, a in zip(sonuc, agirlik):
        k["start"], k["end"], k["yontem"], k["skor"] = t, t + sure * a / toplam, yontem, None
        t = k["end"]
    return sonuc


def _ara_deger(sonuc: list[dict], seg_bas: float, seg_son: float) -> None:
    """Units without CTC time are spread between their timed neighbours, proportional to text length."""
    i = 0
    n = len(sonuc)
    while i < n:
        if sonuc[i]["start"] is not None:
            i += 1
            continue
        j = i
        while j < n and sonuc[j]["start"] is None:
            j += 1
        bas = sonuc[i - 1]["end"] if i > 0 else seg_bas
        son = sonuc[j]["start"] if j < n else seg_son
        bos = sonuc[i:j]
        agirlik = [max(1, len(k["kelime"])) for k in bos]
        toplam = float(sum(agirlik))
        t = bas
        for k, a in zip(bos, agirlik):
            k["start"] = t
            k["end"] = t + max(0.0, son - bas) * a / toplam
            t = k["end"]
        i = j


def _cakisma_duzelt(kelimeler: list[dict]) -> int:
    n = 0
    for a, b in zip(kelimeler, kelimeler[1:]):
        if a["end"] > b["start"]:
            orta = round((a["end"] + b["start"]) / 2.0, 3)
            a["end"], b["start"] = orta, orta
            n += 1
    for k in kelimeler:
        if k["end"] <= k["start"]:
            k["end"] = k["start"] + 0.01
    return n


def _hizala(m: "HizalamaModeli", is_: dict, dil: str) -> dict:
    """One file with an already loaded model -> {"kelimeler", "profil"}."""
    import soundfile

    sureler = {}
    ses, hiz = soundfile.read(is_["ses"], dtype="float32", always_2d=False)
    if hiz != ORNEKLEME:
        raise RuntimeError("worker 16 kHz mono wav bekler")
    t = time.perf_counter()
    kelimeler: list[dict] = []
    for seg in is_["segmentler"]:
        a, b = max(0, int(float(seg["start"]) * ORNEKLEME)), min(len(ses), int(float(seg["end"]) * ORNEKLEME))
        if b - a < ORNEKLEME // 10 or not seg["birimler"]:
            kelimeler.extend(_esit_bol([{"kelime": x} for x in seg["birimler"]], float(seg["start"]), float(seg["end"]) - float(seg["start"]), "esit_bolme"))
            continue
        kelimeler.extend(_segment_hizala(m, ses[a:b], {**seg, "end": a / ORNEKLEME + (b - a) / ORNEKLEME, "start": a / ORNEKLEME}, dil))
    sureler["hizalama_sn"] = round(time.perf_counter() - t, 3)
    for k in kelimeler:
        k["start"], k["end"] = round(float(k["start"]), 3), round(float(k["end"]), 3)
    duzeltme = _cakisma_duzelt(kelimeler)
    yontemler = {}
    for k in kelimeler:
        yontemler[k["yontem"]] = yontemler.get(k["yontem"], 0) + 1
    return {"kelimeler": kelimeler, "profil": {
        "yontem": "wav2vec2_ctc_forced_align_v1", "dil": dil, "cihaz": m.cihaz, "sureler": sureler,
        "yontem_sayilari": yontemler, "cakisma_duzeltme": duzeltme} | _model_kimligi(is_, dil)}


def calistir(istek: dict) -> dict:
    """Single file (istek["ses"], ["dil"], ["segmentler"]) or batch (istek["isler"] = [{"ses", "dil", "model",
    "revizyon", "segmentler"}, ...]). In a batch, files are grouped by alignment model; each model loads once and is
    freed before the next one (one model on the GPU at a time)."""
    yuk = {}
    t = time.perf_counter()
    import torch

    yuk["import_sn"] = round(time.perf_counter() - t, 3)
    cihaz = istek.get("cihaz", "cuda")
    if cihaz == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("torch CUDA görmüyor (sürücü / cu126 wheel?)")
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    tekil = "isler" not in istek
    isler = [istek] if tekil else list(istek["isler"])
    sonuclar: list[dict | None] = [None] * len(isler)
    anahtar = lambda i: (str(isler[i]["dil"]).lower(), isler[i].get("model") or "", isler[i].get("revizyon") or "")
    m, m_anahtar, yuk["model_yukleme_sn"], yuk["modeller"] = None, None, 0.0, []
    for i in sorted(range(len(isler)), key=anahtar):
        is_ = isler[i]
        dil = str(is_["dil"]).lower()
        try:
            if anahtar(i) != m_anahtar:
                if m is not None:
                    del m
                    m = None
                    if cihaz == "cuda":
                        torch.cuda.empty_cache()
                t = time.perf_counter()
                m = HizalamaModeli(dil, cihaz, is_.get("model"), is_.get("revizyon"))
                m_anahtar = anahtar(i)
                sn = round(time.perf_counter() - t, 3)
                yuk["model_yukleme_sn"] = round(yuk["model_yukleme_sn"] + sn, 3)
                yuk["modeller"].append({"model": m.ad, "yukleme_sn": sn})
            sonuclar[i] = {"durum": "ok", **_hizala(m, is_, dil)}
        except Exception as hata:
            if tekil:
                raise
            m_anahtar = None if m is None else m_anahtar
            sonuclar[i] = {"durum": "hata", "hata": f"{type(hata).__name__}: {hata}"}
    tepe = int(torch.cuda.max_memory_allocated() // 1048576) if cihaz == "cuda" else 0
    del m
    if cihaz == "cuda":
        torch.cuda.empty_cache()
    if tekil:
        r = sonuclar[0]
        r["profil"]["sureler"] = {"import_sn": yuk["import_sn"], "model_yukleme_sn": yuk["model_yukleme_sn"], **r["profil"]["sureler"]}
        r["profil"]["torch_vram_tepe_mb"] = tepe
        return r
    return {"durum": "ok", "sonuclar": sonuclar, "sureler": yuk, "torch_vram_tepe_mb": tepe}


def _model_kimligi(istek: dict, dil: str) -> dict:
    kaynak, ad, rev = hizalama_modeli(dil, istek.get("model"))
    return {"model": ad, "model_kaynak": kaynak, "revizyon": istek.get("revizyon") or rev or "main"}


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--istek", required=True)
    p.add_argument("--yanit", required=True)
    a = p.parse_args(argv)
    istek = json.loads(Path(a.istek).read_text(encoding="utf-8"))
    try:
        yanit = calistir(istek)
    except Exception as hata:
        import traceback

        _yaz(Path(a.yanit), {"durum": "hata", "hata": f"{type(hata).__name__}: {hata}", "iz": traceback.format_exc()})
        return 1
    _yaz(Path(a.yanit), yanit)
    return 0


if __name__ == "__main__":
    sys.exit(main())
