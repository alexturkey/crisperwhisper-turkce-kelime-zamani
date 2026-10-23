"""End-to-end flow: audio -> 16 kHz wav -> ASR worker -> alignment worker -> outputs. Runs the two workers as
subprocesses of the same interpreter so the GPU holds one model at a time (4 GB cards)."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

from transkript import __version__, ayarlar, cikti, ses
from transkript.diller import SINANMIS, birimlere_ayir, bosluksuz_mu, dil_kodu, hizalama_modeli

CUMLE_SONU = re.compile(r"[.!?…。！？]$")
GIZLI = getattr(subprocess, "CREATE_NO_WINDOW", 0)  # Windows: child processes open no console window


class VramGozcu:
    """Polls nvidia-smi while a worker runs; reports the peak memory.used in MB (0 if nvidia-smi is missing)."""

    def __init__(self):
        self.tepe = 0
        self._dur = threading.Event()
        self._yol = shutil.which("nvidia-smi")
        self._t = threading.Thread(target=self._kos, daemon=True)

    def _kos(self):
        while not self._dur.is_set():
            try:
                c = subprocess.run([self._yol, "--query-gpu=memory.used", "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=5, creationflags=GIZLI)
                deger = max(int(x.strip()) for x in c.stdout.splitlines() if x.strip())
                self.tepe = max(self.tepe, deger)
            except Exception:
                pass
            self._dur.wait(0.5)

    def __enter__(self):
        if self._yol:
            self._t.start()
        return self

    def __exit__(self, *_):
        self._dur.set()
        if self._yol:
            self._t.join(timeout=6)


def _isci(modul: str, istek: dict, klasor: Path, ad: str, ortam: dict, zaman_asimi: int) -> tuple[dict, float, int]:
    istek_yolu, yanit_yolu = klasor / f"{ad}_istek.json", klasor / f"{ad}_yanit.json"
    istek_yolu.write_text(json.dumps(istek, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if yanit_yolu.exists():
        yanit_yolu.unlink()
    t0 = time.perf_counter()
    with VramGozcu() as vram:
        proc = subprocess.run([sys.executable, "-m", modul, "--istek", str(istek_yolu), "--yanit", str(yanit_yolu)],
                              cwd=str(ayarlar.REPO), env=ortam, capture_output=True, text=True, timeout=zaman_asimi, encoding="utf-8", errors="replace", creationflags=GIZLI)
    sure = time.perf_counter() - t0
    (klasor / f"{ad}_log.txt").write_text((proc.stdout or "") + "\n--- stderr ---\n" + (proc.stderr or ""), encoding="utf-8")
    if not yanit_yolu.is_file():
        raise RuntimeError(f"{ad}: yanıt üretilmedi (rc={proc.returncode}); son satırlar:\n{(proc.stderr or '')[-1500:]}")
    yanit = json.loads(yanit_yolu.read_text(encoding="utf-8"))
    if yanit.get("durum") != "ok":
        raise RuntimeError(f"{ad}: {yanit.get('hata')}\n{str(yanit.get('iz', ''))[-1500:]}")
    return yanit, sure, vram.tepe


def segmentler_olustur(kelimeler: list[dict], sure: float, dil: str) -> list[dict]:
    """Groups ASR words into alignment segments (<= ~18 s, <= 80 words, split on sentence end or > 2.5 s gaps),
    padded by 0.25 s; then splits each word into alignment units (characters for no-space scripts)."""
    gruplar: list[list[dict]] = []
    su: list[dict] = []
    onceki_son = None
    for k in kelimeler:
        if su:
            bosluk = k["start"] - (onceki_son if onceki_son is not None else su[0]["start"])
            if bosluk > 2.5 or k["start"] - su[0]["start"] > 18.0 or len(su) >= 80:
                gruplar.append(su)
                su = []
        su.append(k)
        onceki_son = k["end"]
        if CUMLE_SONU.search(k["kelime"].strip()):
            gruplar.append(su)
            su = []
    if su:
        gruplar.append(su)
    bosluksuz = bosluksuz_mu(dil)
    segmentler = []
    for i, g in enumerate(gruplar):
        bas = max(0.0, g[0]["start"] - 0.25)
        sonraki = gruplar[i + 1][0]["start"] if i + 1 < len(gruplar) else sure
        son = min(sure, max(sonraki, g[-1]["end"] + 0.25))
        if son <= bas:
            son = min(sure, bas + 0.25)
        birimler = []
        for k in g:
            birimler.extend(birimlere_ayir(k["kelime"]) if bosluksuz else [k["kelime"]])
        segmentler.append({"start": round(bas, 3), "end": round(son, 3), "birimler": birimler})
    return segmentler


def dogrula(kelimeler: list[dict], sure: float) -> None:
    onceki = -1.0
    for i, k in enumerate(kelimeler):
        if k["end"] < k["start"] or k["start"] < 0 or k["start"] + 1e-6 < onceki:
            raise RuntimeError(f"kelime zamanı kronolojik değil: {i} {k}")
        if k["end"] > sure + 1.0:
            raise RuntimeError(f"kelime ses süresini aşıyor: {i} {k}")
        onceki = k["start"]


def calistir(kaynak: Path, klasor: Path, dil: str, ayar: dict, bicimler: set[str], hizalama_modeli_ozel: str | None,
             hizalama_cihazi: str | None, zaman_asimi: int = 3600, hizalama_revizyon: str | None = None) -> dict:
    t_toplam = time.perf_counter()
    klasor.mkdir(parents=True, exist_ok=True)
    model_dizini = Path(ayar["model"])
    donusum = ayarlar.model_dogrula(model_dizini)
    ortam = dict(os.environ)
    ortam.update({"HF_HOME": ayar["hf_home"], "HF_HUB_OFFLINE": ortam.get("HF_HUB_OFFLINE", "0"), "PYTHONIOENCODING": "utf-8",
                  "TOKENIZERS_PARALLELISM": "false", "PYTHONPATH": str(ayarlar.REPO)})

    t = time.perf_counter()
    dalga = ses.yukle(kaynak)
    wav = klasor / "ses_16k_mono.wav"
    sure = ses.wav_yaz(wav, dalga)
    sureler = {"ses_hazirlama_sn": round(time.perf_counter() - t, 3)}

    asr, asr_sure, asr_vram = _isci("transkript.motor_isci", {
        "ses": str(wav), "dil": dil, "model": str(model_dizini), "cihaz": ayar.get("cihaz", "cuda"),
        "compute_type": ayar.get("compute_type", "int8"), "max_new_tokens": 400}, klasor, "asr", ortam, zaman_asimi)
    sureler["asr_surec_sn"] = round(asr_sure, 3)
    kod = dil_kodu(asr["dil"])
    try:
        _, _, hiz_revizyon = hizalama_modeli(kod, hizalama_modeli_ozel, hizalama_revizyon)
    except KeyError:
        raise SystemExit(f"'{kod}' için hizalama modeli yok; --hizalama-modeli <HF wav2vec2 CTC modeli> verin (docs/diller.md)")
    segmentler = segmentler_olustur(asr["kelimeler"], sure, kod)
    hiz, hiz_sure, hiz_vram = _isci("transkript.hizalama_isci", {
        "ses": str(wav), "dil": kod, "cihaz": hizalama_cihazi or ayar.get("cihaz", "cuda"), "model": hizalama_modeli_ozel,
        "revizyon": hiz_revizyon, "segmentler": segmentler}, klasor, "hizalama", ortam, zaman_asimi)
    sureler["hizalama_surec_sn"] = round(hiz_sure, 3)
    kelimeler = hiz["kelimeler"]
    dogrula(kelimeler, sure)
    bosluksuz = bosluksuz_mu(kod)
    metin = asr["metin"]
    sonuc = {
        "surum": __version__, "kaynak": str(kaynak), "ses_sn": round(sure, 3), "dil": kod,
        "dil_kaynagi": "verilen" if dil != "auto" else "tespit", "dil_adaylari": asr.get("dil_adaylari", []),
        "birim": "karakter" if bosluksuz else "kelime", "sinanmis_dil": kod in SINANMIS,
        "metin": metin, "kelimeler": kelimeler,
        "asr": {"motor": "CrisperWhisper 2.0 Turbo / CTranslate2", "model_commit": donusum["kaynak_commit"], **asr["kimlik"], "sureler": asr["sureler"]},
        "hizalama": hiz["profil"],
        "asr_kelimeleri": asr["kelimeler"],  # native cross-attention times: diagnostics only
        "sureler": {**sureler, "toplam_sn": round(time.perf_counter() - t_toplam, 3)},
        "vram_tepe_mb": {"asr": asr_vram, "hizalama": hiz_vram},
    }
    sonuc["sureler"]["toplam_sn"] = round(time.perf_counter() - t_toplam, 3)
    cikti.hepsini_yaz(klasor, sonuc, bicimler, bosluksuz)
    return sonuc


def calistir_toplu(isler: list[tuple[Path, Path, str]], calisma: Path, ayar: dict, bicimler: set[str],
                   hizalama_modeli_ozel: str | None, hizalama_cihazi: str | None, zaman_asimi: int = 3600,
                   hizalama_revizyon: str | None = None, ilerleme=print) -> list[dict]:
    """Batch: isler = [(source, output folder, language|"auto"), ...]. One ASR process for all files (CrisperWhisper loads
    once), then one alignment process (each wav2vec2 model loads once). Outputs per file are the same as calistir();
    the shared import/load time is reported once under sonuc["toplu"]. A failing file does not stop the others:
    its entry is {"durum": "hata", "kaynak", "hata"}."""
    t_toplam = time.perf_counter()
    calisma.mkdir(parents=True, exist_ok=True)
    model_dizini = Path(ayar["model"])
    donusum = ayarlar.model_dogrula(model_dizini)
    ortam = dict(os.environ)
    ortam.update({"HF_HOME": ayar["hf_home"], "HF_HUB_OFFLINE": ortam.get("HF_HUB_OFFLINE", "0"), "PYTHONIOENCODING": "utf-8",
                  "TOKENIZERS_PARALLELISM": "false", "PYTHONPATH": str(ayarlar.REPO)})
    durum: list[dict] = []
    for kaynak, klasor, dil in isler:
        t = time.perf_counter()
        try:
            klasor.mkdir(parents=True, exist_ok=True)
            wav = klasor / "ses_16k_mono.wav"
            sure = ses.wav_yaz(wav, ses.yukle(kaynak))
            durum.append({"kaynak": kaynak, "klasor": klasor, "dil": dil, "wav": wav, "sure": sure,
                          "sureler": {"ses_hazirlama_sn": round(time.perf_counter() - t, 3)}})
        except Exception as hata:
            durum.append({"kaynak": kaynak, "klasor": klasor, "hata": f"ses: {type(hata).__name__}: {hata}"})
    hazir = [d for d in durum if "hata" not in d]
    toplu = {"dosya": len(isler), "ses_hazirlama_sn": round(time.perf_counter() - t_toplam, 3)}
    ilerleme(f"TOPLU ses hazır: {len(hazir)}/{len(isler)} dosya", flush=True)

    asr, asr_sure, asr_vram = _isci("transkript.motor_isci", {
        "isler": [{"ses": str(d["wav"]), "dil": d["dil"]} for d in hazir], "model": str(model_dizini),
        "cihaz": ayar.get("cihaz", "cuda"), "compute_type": ayar.get("compute_type", "int8"), "max_new_tokens": 400},
        calisma, "asr", ortam, zaman_asimi)
    toplu.update({"asr_surec_sn": round(asr_sure, 3), "asr_yukleme": asr["sureler"], "vram_tepe_mb_asr": asr_vram})
    ilerleme(f"TOPLU ASR bitti: {round(asr_sure, 1)} sn (yükleme {asr['sureler']})", flush=True)
    hiz_isler, hiz_sahip = [], []
    for d, r in zip(hazir, asr["sonuclar"]):
        if r["durum"] != "ok":
            d["hata"] = f"asr: {r['hata']}"
            continue
        d["asr"] = r
        kod = dil_kodu(r["dil"])
        try:
            _, _, rev = hizalama_modeli(kod, hizalama_modeli_ozel, hizalama_revizyon)
        except KeyError:
            d["hata"] = f"'{kod}' için hizalama modeli yok; --hizalama-modeli verin (docs/diller.md)"
            continue
        d["kod"] = kod
        hiz_isler.append({"ses": str(d["wav"]), "dil": kod, "model": hizalama_modeli_ozel, "revizyon": rev,
                          "segmentler": segmentler_olustur(r["kelimeler"], d["sure"], kod)})
        hiz_sahip.append(d)
    if hiz_isler:
        hiz, hiz_sure, hiz_vram = _isci("transkript.hizalama_isci", {
            "cihaz": hizalama_cihazi or ayar.get("cihaz", "cuda"), "isler": hiz_isler}, calisma, "hizalama", ortam, zaman_asimi)
        toplu.update({"hizalama_surec_sn": round(hiz_sure, 3), "hizalama_yukleme": hiz["sureler"], "vram_tepe_mb_hizalama": hiz_vram})
        ilerleme(f"TOPLU hizalama bitti: {round(hiz_sure, 1)} sn", flush=True)
        for d, r in zip(hiz_sahip, hiz["sonuclar"]):
            if r["durum"] != "ok":
                d["hata"] = f"hizalama: {r['hata']}"
            else:
                d["hiz"] = r
    toplu["toplam_sn"] = round(time.perf_counter() - t_toplam, 3)
    sonuclar = []
    for d in durum:
        if "hata" in d or "hiz" not in d:
            sonuclar.append({"durum": "hata", "kaynak": str(d["kaynak"]), "hata": d.get("hata", "bilinmeyen"), "toplu": toplu})
            continue
        try:
            kelimeler = d["hiz"]["kelimeler"]
            dogrula(kelimeler, d["sure"])
            kod, a = d["kod"], d["asr"]
            bosluksuz = bosluksuz_mu(kod)
            sonuc = {
                "durum": "ok", "surum": __version__, "kaynak": str(d["kaynak"]), "ses_sn": round(d["sure"], 3), "dil": kod,
                "dil_kaynagi": "verilen" if d["dil"] != "auto" else "tespit", "dil_adaylari": a.get("dil_adaylari", []),
                "birim": "karakter" if bosluksuz else "kelime", "sinanmis_dil": kod in SINANMIS,
                "metin": a["metin"], "kelimeler": kelimeler,
                "asr": {"motor": "CrisperWhisper 2.0 Turbo / CTranslate2", "model_commit": donusum["kaynak_commit"], **asr["kimlik"], "sureler": a["sureler"]},
                "hizalama": d["hiz"]["profil"],
                "asr_kelimeleri": a["kelimeler"],  # native cross-attention times: diagnostics only
                "sureler": {**d["sureler"], "asr_cozumleme_sn": a["sureler"].get("cozumleme_sn"),
                            "hizalama_sn": d["hiz"]["profil"]["sureler"].get("hizalama_sn")},
                "vram_tepe_mb": {"asr": asr_vram, "hizalama": toplu.get("vram_tepe_mb_hizalama", 0)},
                "toplu": toplu,
            }
            cikti.hepsini_yaz(d["klasor"], sonuc, bicimler, bosluksuz)
            sonuclar.append(sonuc)
        except Exception as hata:
            sonuclar.append({"durum": "hata", "kaynak": str(d["kaynak"]), "hata": f"çıktı: {type(hata).__name__}: {hata}", "toplu": toplu})
    return sonuclar

