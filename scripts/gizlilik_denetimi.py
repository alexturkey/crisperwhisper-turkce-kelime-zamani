#!/usr/bin/env python3
"""Gizlilik ve gizli karakter taraması / privacy and hidden-character scan (Python 3.8+, yalnız standart kütüphane, ağ yok).

  python -I -X utf8 scripts/gizlilik_denetimi.py            # depodaki izlenen metin dosyalarını tarar
  python -I -X utf8 scripts/gizlilik_denetimi.py --kok .    # başka kök

Ne arar (bulguda İÇERİK BASILMAZ, yalnız dosya:satır ve tür; kişisel veri günlüğe sızmasın):
  * bidi (Trojan Source) ve sıfır genişlikli karakterler, NUL, ESC ve diğer kontrol baytları (sekme/satır sonu hariç)
  * kişisel yol: Windows, macOS ya da Linux kullanıcı klasörü yolu (sürücü harfi + Users + ad, /home/ad, /Users/ad); <ad>, $USER, %USERNAME% gibi yer tutucular serbest
  * kişisel e-posta (GitHub no-reply ve example alanları serbest)
  * token biçimleri: ghp_/github_pat_/hf_/sk- ile başlayan uzun anahtarlar
  * UTF-16 kodlu dosya (BOM'lu ya da her ikinci bayt NUL): kodu çözülüp aynı desenlerle taranır
Çıkış: 0 temiz, 1 bulgu var, 3 girdi hatası. Son satır tek `SONUC:` satırı.
"""
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

METIN_UZANTI = {".py", ".sh", ".ps1", ".cmd", ".bat", ".md", ".txt", ".json", ".yml", ".yaml", ".toml", ".cfg", ".ini", ".gitignore", ".gitattributes", ""}
ATLA_KLASOR = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "cikti", "model", "hf", "torch", "indirme", "_calisma"}

# U+202A-202E, U+2066-2069 (bidi); U+200B-200D, U+2060, U+FEFF (sıfır genişlik; dosya başındaki BOM ayrı ele alınır)
BIDI = set(chr(c) for c in list(range(0x202A, 0x202F)) + list(range(0x2066, 0x206A)))
SIFIR_GENISLIK = set(chr(c) for c in (0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF))
YER_TUTUCU = re.compile(r"^(<[^>]*>|\$\{?[A-Za-z_]+\}?|%[A-Za-z_]+%|\*|x+|ad|kullanici|kullanıcı|user|username|you|name|me|root|runner)$", re.I)
YOL = re.compile(r"(?:[A-Za-z]:[\\/]Users[\\/]|/mnt/[a-z]/Users/|/home/|/Users/)([^\\/\s\"'`)<>]+)", re.I)
EPOSTA = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)")
EPOSTA_SERBEST_ALAN = ("users.noreply.github.com", "example.com", "example.org", "example.net", "noreply.github.com")
TOKEN = re.compile(r"\b(ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|hf_[A-Za-z0-9]{30,}|sk-[A-Za-z0-9]{32,})\b")


def dosyalar(kok):
    """Önce git'in izlediği dosyalar; git yoksa yürüyüş. (göreli yol listesi)"""
    try:
        cikti = subprocess.run(["git", "-C", kok, "ls-files", "-z"], capture_output=True, timeout=30)
        if cikti.returncode == 0 and cikti.stdout:
            yollar = [y for y in cikti.stdout.decode("utf-8", "replace").split("\0") if y]
            yollar += [y for y in _izlenmeyen(kok)]
            return sorted(set(yollar))
    except (OSError, subprocess.SubprocessError):
        pass
    sonuc = []
    for dizin, altlar, adlar in os.walk(kok):
        altlar[:] = [a for a in altlar if a not in ATLA_KLASOR]
        for ad in adlar:
            sonuc.append(os.path.relpath(os.path.join(dizin, ad), kok).replace(os.sep, "/"))
    return sorted(sonuc)


def _izlenmeyen(kok):
    """Henüz git'e eklenmemiş ama yok sayılmayan dosyalar (yeni dosya da taransın)."""
    try:
        c = subprocess.run(["git", "-C", kok, "ls-files", "-z", "--others", "--exclude-standard"], capture_output=True, timeout=30)
        if c.returncode == 0:
            return [y for y in c.stdout.decode("utf-8", "replace").split("\0") if y]
    except (OSError, subprocess.SubprocessError):
        pass
    return []


def metne_cevir(veri):
    """(metin, utf16_mi) ya da (None, False) ikili dosya için."""
    if veri[:2] in (b"\xff\xfe", b"\xfe\xff"):
        try:
            return veri.decode("utf-16"), True
        except UnicodeDecodeError:
            return None, False
    if len(veri) >= 4 and veri[1:2] == b"\x00" and veri[3:4] == b"\x00" and veri[0:1] != b"\x00":
        try:
            return veri.decode("utf-16-le"), True
        except UnicodeDecodeError:
            return None, False
    try:
        return veri.decode("utf-8"), False
    except UnicodeDecodeError:
        return None, False


def tara_metin(yol, metin, utf16=False):
    bulgu = []
    if utf16:
        bulgu.append((yol, 0, "UTF-16 kodlu dosya (UTF-8 kullanın)"))
    satirlar = metin.split("\n")
    for no, satir in enumerate(satirlar, 1):
        govde = satir[1:] if (no == 1 and satir[:1] == "\ufeff") else satir  # dosya başı BOM serbest
        for ch in govde:
            if ch in BIDI:
                bulgu.append((yol, no, "bidi (çift yönlü) Unicode karakteri")); break
        else:
            if any(ch in SIFIR_GENISLIK for ch in govde):
                bulgu.append((yol, no, "sıfır genişlikli karakter"))
        if any((ord(ch) < 32 and ch not in "\t\r\n\f") or ord(ch) == 127 for ch in govde):
            bulgu.append((yol, no, "kontrol karakteri (NUL/ESC/...)"))
        for m in YOL.finditer(govde):
            if not YER_TUTUCU.match(m.group(1)):
                bulgu.append((yol, no, "kişisel yol deseni")); break
        for m in EPOSTA.finditer(govde):
            alan = m.group(1).lower()
            if not alan.endswith(EPOSTA_SERBEST_ALAN):
                bulgu.append((yol, no, "e-posta adresi")); break
        if TOKEN.search(govde):
            bulgu.append((yol, no, "token biçimi"))
    return bulgu


def tara(kok):
    bulgu = []
    taranan = 0
    for yol in dosyalar(kok):
        tam = os.path.join(kok, yol)
        if not os.path.isfile(tam):
            continue
        ad = os.path.basename(yol)
        uzanti = os.path.splitext(ad)[1].lower()
        if uzanti not in METIN_UZANTI and ad not in (".gitignore", ".gitattributes"):
            continue
        with open(tam, "rb") as f:
            veri = f.read()
        metin, utf16 = metne_cevir(veri)
        if metin is None:
            if b"\x00" in veri:
                bulgu.append((yol, 0, "metin dosyası ikili ya da çözülemiyor (NUL)"))
            continue
        taranan += 1
        # bu betiğin kendisi desen tanımı içerir: kendi satırlarını kişisel yol/e-posta için tarama, bidi/kontrol için tara
        bulgu += tara_metin(yol, metin, utf16) if os.path.basename(yol) != "gizlilik_denetimi.py" else [b for b in tara_metin(yol, metin, utf16) if "yol" not in b[2] and "e-posta" not in b[2] and "token" not in b[2]]
    return taranan, bulgu


def main(argv):
    kok = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    if "--kok" in argv:
        i = argv.index("--kok")
        if i + 1 >= len(argv) or not os.path.isdir(argv[i + 1]):
            print("SONUC: GIRDI HATASI (cikis 3): --kok bir klasor olmali")
            return 3
        kok = os.path.abspath(argv[i + 1])
    taranan, bulgu = tara(kok)
    for yol, no, tur in bulgu:
        print("BULGU: %s:%s %s" % (yol, no, tur))
    if bulgu:
        print("SONUC: KIRMIZI (cikis 1): %d bulgu, %d dosya tarandi (icerik basilmaz)" % (len(bulgu), taranan))
        return 1
    print("SONUC: GECTI (cikis 0): %d dosya tarandi, bulgu yok" % taranan)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
