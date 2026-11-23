#!/usr/bin/env python3
"""Hızlı denetim / quick checks (Python 3.8+, yalnız standart kütüphane, ağ yok, GPU yok, birkaç saniye).

  python -I -X utf8 scripts/denetim.py --hizli

Kapılar: gizlilik + gizli karakter taraması, zorunlu dosyalar, requirements.txt sabit sürüm (==), ayarlar/manifest.json
sabitleri (commit + 64 haneli sha256), kalite sabitleri (scripts/repo_kapi.json), .gitignore ağırlık kuralları,
PowerShell dosyalarında BOM (Windows PowerShell 5.1 Türkçe iletiyi doğru göstersin), README çeviri eşliği.
Çıkış kodları: 0 hepsi GEÇTİ, 1 en az bir kapı KIRMIZI, 3 girdi/ortam eksik, 6 bir kapı ÇALIŞMADI. Son satır tek `SONUC:` satırı.
Bu betik hiçbir dosyayı değiştirmez; model ağırlığına ya da kalite ayarına dokunmaz.
"""
import json
import os
import re
import subprocess
import sys

sys.dont_write_bytecode = True
for _akis in (sys.stdout, sys.stderr):
    try:
        _akis.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

KOK = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
BETIK = os.path.join(KOK, "scripts")
ZORUNLU = ["README.md", "README.tr.md", "LICENSE", "NOTICE", "SECURITY.md", "CONTRIBUTING.md", "AGENTS.md", "requirements.txt",
           "ayarlar/manifest.json", ".gitignore", "scripts/kur.sh", "scripts/kur.ps1"]
AGIRLIK_KURALI = ["*.safetensors", "*.bin", "model/", "ayarlar.json", "cikti/", ".venv/"]


def yol(*p):
    return os.path.join(KOK, *p)


def kapi_dosyalar():
    eksik = [d for d in ZORUNLU if not os.path.isfile(yol(*d.split("/")))]
    return (not eksik, "eksik dosya: %s" % ", ".join(eksik) if eksik else "%d zorunlu dosya var" % len(ZORUNLU))


def kapi_requirements():
    kotu = []
    with open(yol("requirements.txt"), encoding="utf-8") as f:
        for no, s in enumerate(f, 1):
            s = s.strip()
            if s and not s.startswith("#") and "==" not in s:
                kotu.append(str(no))
    return (not kotu, "sabit olmayan satir: %s" % ", ".join(kotu) if kotu else "her paket == ile sabit")


def kapi_manifest():
    with open(yol("ayarlar", "manifest.json"), encoding="utf-8") as f:
        m = json.load(f)
    sha = re.compile(r"^[0-9a-f]{64}$")
    kotu = []

    def gez(d, ad=""):
        if isinstance(d, dict):
            for k, v in d.items():
                if k.endswith("sha256") and isinstance(v, str) and not sha.match(v):
                    kotu.append(ad + k)
                if k == "commit" and isinstance(v, str) and not re.match(r"^[0-9a-f]{40}$", v):
                    kotu.append(ad + k)
                gez(v, ad + k + ".")
        elif isinstance(d, list):
            for i, v in enumerate(d):
                gez(v, ad + str(i) + ".")
    gez(m)
    return (not kotu, "gecersiz sabit: %s" % ", ".join(kotu) if kotu else "commit ve sha256 sabitleri bicimli")


def kapi_kalite():
    with open(yol("scripts", "repo_kapi.json"), encoding="utf-8") as f:
        ayar = json.load(f)
    kotu = []
    for k in ayar.get("kalite_sabitleri", []):
        desen = re.compile(k["yasak_desen"])
        for d in k.get("dosyalar", []):
            tam = yol(*d.split("/"))
            if os.path.isfile(tam):
                with open(tam, encoding="utf-8", errors="replace") as f:
                    if desen.search(f.read()):
                        kotu.append("%s: %s" % (k["ad"], d))
    return (not kotu, "kalite sabiti ihlali: %s" % "; ".join(kotu) if kotu else "kalite sabitleri yerinde")


def kapi_gitignore():
    with open(yol(".gitignore"), encoding="utf-8") as f:
        icerik = f.read()
    eksik = [k for k in AGIRLIK_KURALI if k not in icerik]
    return (not eksik, ".gitignore'da eksik: %s" % ", ".join(eksik) if eksik else ".gitignore agirlik/cikti kurallari var")


def kapi_bom():
    kotu = []
    for d in sorted(os.listdir(BETIK)):
        if d.lower().endswith(".ps1"):
            with open(os.path.join(BETIK, d), "rb") as f:
                b = f.read()
            if b[:3] != b"\xef\xbb\xbf" and any(x > 127 for x in b):
                kotu.append(d)
    return (not kotu, "BOM'suz ASCII-disi .ps1: %s" % ", ".join(kotu) if kotu else ".ps1 dosyalari BOM'lu ya da ASCII")


def alt_betik(ad):
    s = subprocess.run([sys.executable, "-I", "-X", "utf8", os.path.join(BETIK, ad)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    son = [x for x in s.stdout.strip().split("\n") if x][-1:] or [""]
    ilk = [x for x in s.stdout.strip().split("\n") if x.startswith(("BULGU", "KIRMIZI"))][:5]
    if s.returncode not in (0, 1):
        raise RuntimeError("%s cikis %d" % (ad, s.returncode))
    return (s.returncode == 0, "%s %s" % (son[0], "; ".join(ilk)) if ilk else son[0])


KAPILAR = [
    ("dosyalar", kapi_dosyalar),
    ("requirements", kapi_requirements),
    ("manifest", kapi_manifest),
    ("kalite", kapi_kalite),
    ("gitignore", kapi_gitignore),
    ("powershell-bom", kapi_bom),
    ("gizlilik", lambda: alt_betik("gizlilik_denetimi.py")),
    ("dil-eslik", lambda: alt_betik("dil_eslik_denetimi.py")),
]


def main(argv):
    if "--hizli" not in argv:
        print("kullanim: python -I -X utf8 scripts/denetim.py --hizli")
        print("SONUC: GIRDI HATASI (cikis 3): --hizli gerekli")
        return 3
    if sys.version_info < (3, 8):
        print("SONUC: GIRDI HATASI (cikis 3): Python 3.8+ gerekir")
        return 3
    kirmizi = calismadi = 0
    for ad, f in KAPILAR:
        try:
            tamam, ozet = f()
        except Exception as e:  # bir kapi cokerse yesil sayilmaz
            calismadi += 1
            print("CALISMADI: %s (%s: %s)" % (ad, type(e).__name__, str(e)[:120]))
            continue
        if tamam:
            print("GECTI: %s: %s" % (ad, ozet))
        else:
            kirmizi += 1
            print("KIRMIZI: %s: %s" % (ad, ozet))
    if calismadi:
        print("SONUC: CALISMADI (cikis 6): %d kapi calismadi, %d kirmizi" % (calismadi, kirmizi))
        return 6
    if kirmizi:
        print("SONUC: KIRMIZI (cikis 1): %d kapi kirmizi" % kirmizi)
        return 1
    print("SONUC: GECTI (cikis 0): %d kapi gecti" % len(KAPILAR))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
