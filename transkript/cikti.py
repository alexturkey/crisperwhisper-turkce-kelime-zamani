"""Output writers: kelimeler.json, transkript.txt, SRT and VTT (sentence lines or one cue per word)."""

from __future__ import annotations

import json
import re
from pathlib import Path

CUMLE_SONU = re.compile(r"[.!?…。！？]$")
AZAMI_SATIR_SN = 7.0
AZAMI_KELIME = 14
BOSLUK_SN = 1.2


def cumleler(kelimeler: list[dict], bosluksuz: bool = False) -> list[dict]:
    """Groups words into caption lines: sentence end, long gap, max duration or max word count."""
    gruplar: list[list[dict]] = []
    su: list[dict] = []
    for k in kelimeler:
        if su and (k["start"] - su[-1]["end"] > BOSLUK_SN or k["start"] - su[0]["start"] > AZAMI_SATIR_SN or len(su) >= AZAMI_KELIME):
            gruplar.append(su)
            su = []
        su.append(k)
        if CUMLE_SONU.search(k["kelime"].strip()):
            gruplar.append(su)
            su = []
    if su:
        gruplar.append(su)
    birlestirici = "" if bosluksuz else " "
    return [{"start": g[0]["start"], "end": g[-1]["end"], "metin": birlestirici.join(x["kelime"] for x in g), "kelimeler": g} for g in gruplar]


def _zaman(sn: float, ayrac: str) -> str:
    ms = int(round(sn * 1000))
    s, ms = divmod(ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}{ayrac}{ms:03d}"


def srt(satirlar: list[dict]) -> str:
    parcalar = []
    for i, s in enumerate(satirlar, 1):
        parcalar.append(f"{i}\n{_zaman(s['start'], ',')} --> {_zaman(s['end'], ',')}\n{s['metin']}\n")
    return "\n".join(parcalar)


def vtt(satirlar: list[dict]) -> str:
    parcalar = ["WEBVTT", ""]
    for s in satirlar:
        parcalar.append(f"{_zaman(s['start'], '.')} --> {_zaman(s['end'], '.')}\n{s['metin']}\n")
    return "\n".join(parcalar)


def kelime_satirlari(kelimeler: list[dict]) -> list[dict]:
    return [{"start": k["start"], "end": k["end"], "metin": k["kelime"]} for k in kelimeler]


def hepsini_yaz(klasor: Path, sonuc: dict, bicimler: set[str], bosluksuz: bool) -> list[Path]:
    klasor.mkdir(parents=True, exist_ok=True)
    yazilan = []

    def yaz(ad: str, icerik: str) -> None:
        yol = klasor / ad
        gecici = yol.with_name(yol.name + ".part")
        gecici.write_text(icerik, encoding="utf-8", newline="\n")
        gecici.replace(yol)
        yazilan.append(yol)

    yaz("transkript.txt", sonuc["metin"] + "\n")
    yaz("kelimeler.json", json.dumps(sonuc, ensure_ascii=False, indent=1) + "\n")
    satirlar = cumleler(sonuc["kelimeler"], bosluksuz)
    if "srt" in bicimler:
        yaz("transkript.srt", srt(satirlar))
        yaz("kelimeler.srt", srt(kelime_satirlari(sonuc["kelimeler"])))
    if "vtt" in bicimler:
        yaz("transkript.vtt", vtt(satirlar))
        yaz("kelimeler.vtt", vtt(kelime_satirlari(sonuc["kelimeler"])))
    return yazilan
