#!/usr/bin/env python3
"""README çeviri eşliği / translation parity (Python 3.8+, yalnız standart kütüphane, ağ yok).

  python -I -X utf8 scripts/dil_eslik_denetimi.py

`scripts/dil_profili.json` kaynağı (README.md) ve çevirileri (README.tr.md) tanımlar. Her çeviri için kaynakla AYNI olmalı:
bölüm başlığı sayısı (## ve ###), kod bloğu sayısı ve kod bloklarının komut/dosya adı kısmı (açıklamalar çevrilebilir), yerel bağlantı hedefleri
(README dosyalarına giden bağlantılar hariç: onlar dile göre değişir). Cümlelerin doğruluğuna BAKMAZ: onu insan okur.
Çıkış: 0 eş, 1 fark var, 3 girdi hatası. Son satır tek `SONUC:` satırı.
"""
import json
import os
import re
import sys

sys.dont_write_bytecode = True
for _akis in (sys.stdout, sys.stderr):
    try:
        _akis.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

KOK = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def oku(yol):
    with open(os.path.join(KOK, yol), encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n")


def kod_ozet(blok):
    """Komut ve dosya adları aynı kalmalı; açıklama (2+ boşluktan sonrası ve # yorumları) çevrilebilir."""
    satirlar = []
    for s in blok.split(chr(10)):
        s = re.split(r"\s{2,}|\s#\s", s.strip(), maxsplit=1)[0]
        if s and not s.startswith("#"):
            satirlar.append(s)
    return chr(10).join(satirlar)


def ozet(metin):
    kodlar = [kod_ozet(k) for k in re.findall(r"```[^\n]*\n(.*?)```", metin, re.S)]
    govde = re.sub(r"```.*?```", "", metin, flags=re.S)
    basliklar = [s for s in govde.split("\n") if re.match(r"^#{2,3} ", s)]
    baglanti = set()
    for hedef in re.findall(r"\]\(([^)\s]+)\)", govde):
        if hedef.startswith(("http://", "https://", "mailto:", "#")):
            continue
        yol = hedef.split("#")[0]
        if re.match(r"^README(\.[A-Za-z-]+)?\.md$", os.path.basename(yol)):
            continue
        baglanti.add(yol)
    return {"baslik": len(basliklar), "kod_blogu": len(kodlar), "kodlar": kodlar, "baglanti": baglanti}


def main():
    try:
        with open(os.path.join(KOK, "scripts", "dil_profili.json"), encoding="utf-8") as f:
            profil = json.load(f)
        kaynak = ozet(oku(profil["kaynak"]))
    except (OSError, ValueError, KeyError) as e:
        print("SONUC: GIRDI HATASI (cikis 3): %s" % type(e).__name__)
        return 3
    sorun = 0
    for c in profil.get("ceviriler", []):
        try:
            hedef = ozet(oku(c["dosya"]))
        except (OSError, KeyError) as e:
            print("KIRMIZI: %s okunamadi (%s)" % (c.get("dosya"), type(e).__name__)); sorun += 1; continue
        if hedef["baslik"] != kaynak["baslik"]:
            print("KIRMIZI: %s baslik sayisi %d, kaynak %d" % (c["dosya"], hedef["baslik"], kaynak["baslik"])); sorun += 1
        if hedef["kod_blogu"] != kaynak["kod_blogu"]:
            print("KIRMIZI: %s kod blogu sayisi %d, kaynak %d" % (c["dosya"], hedef["kod_blogu"], kaynak["kod_blogu"])); sorun += 1
        else:
            for i, (a, b) in enumerate(zip(kaynak["kodlar"], hedef["kodlar"]), 1):
                if a != b:
                    print("KIRMIZI: %s %d. kod blogu kaynakla ayni degil" % (c["dosya"], i)); sorun += 1
        if hedef["baglanti"] != kaynak["baglanti"]:
            print("KIRMIZI: %s yerel baglantilar kaynakla ayni degil: %s" % (c["dosya"], sorted(hedef["baglanti"] ^ kaynak["baglanti"]))); sorun += 1
    if sorun:
        print("SONUC: KIRMIZI (cikis 1): %d fark" % sorun)
        return 1
    print("SONUC: GECTI (cikis 0): %d ceviri kaynakla es" % len(profil.get("ceviriler", [])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
