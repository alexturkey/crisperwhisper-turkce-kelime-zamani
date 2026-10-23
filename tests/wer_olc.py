"""WER ölçümü / WER measurement for a folder of (audio, reference text) pairs that were already transcribed.

  python tests/wer_olc.py --cikti cikti/olcum --ref sesler/   # every <ad>.txt next to a transcribed cikti/olcum/<ad>/ folder
  python tests/wer_olc.py --hyp cikti/ilk/transkript.txt --ref ornek/ornek_metin.txt

Every result is printed twice, and both numbers are published:

- **raw** (`ham`): lowercase (Turkish-aware), `[event]` tags and punctuation removed (apostrophe kept), whitespace
  collapsed.
- **normalised** (`normalize`, the headline number): raw, plus spelling conventions that do not change what was said.
  Applied identically to reference and hypothesis. Turkish/Azerbaijani only (other languages: same as raw):
  1. circumflex folded: â/î/û -> a/i/u (`hâlâ` = `hala`);
  2. numbers written out in Turkish words, a suffix after the apostrophe stays on the last word
     (`40.000'in` -> `kırk binin`, `1996` -> `bin dokuz yüz doksan altı`, `3,5` -> `üç virgül beş`);
  3. apostrophe removed and the suffix joined (`Okulu'ndan` = `okulundan`, `Meşhed'deki` -> `meşheddeki`);
  4. the postposition `ile` joined to the previous word with vowel harmony (`yöntemi ile` = `yöntemiyle`,
     `kalem ile` = `kalemle`).
  Nothing else is merged: compound spacing (`çevrimiçi` / `çevrim içi`), names and wrong words still count.

Word-level Levenshtein. Prints per file and total; also reads kelimeler.json for timings and VRAM when present.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from transkript.diller import dil_kodu, kucult  # noqa: E402

NOKTALAMA = re.compile(r"[^\w\s']", re.UNICODE)
ETIKET = re.compile(r"\[[^\]]*\]")
SAPKA = str.maketrans("âîûÂÎÛ", "aiuAIU")
SAYI = re.compile(r"(?<![\w.,])(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d+))?(?:['’](\w+))?")
BIRLER = ["", "bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz"]
ONLAR = ["", "on", "yirmi", "otuz", "kırk", "elli", "altmış", "yetmiş", "seksen", "doksan"]
BUYUK = [(10**12, "trilyon"), (10**9, "milyar"), (10**6, "milyon"), (1000, "bin")]
INCE, KALIN = set("eiöü"), set("aıou")


def _uc_basamak(n: int) -> list[str]:
    s = []
    if n >= 100:
        s += ([] if n // 100 == 1 else [BIRLER[n // 100]]) + ["yüz"]
    s += [w for w in (ONLAR[(n // 10) % 10], BIRLER[n % 10]) if w]
    return s


def sayi_yazi(n: int) -> list[str]:
    """Turkish number words: 40000 -> ['kırk', 'bin'], 1000 -> ['bin'], 0 -> ['sıfır']."""
    if n == 0:
        return ["sıfır"]
    s = []
    for deger, ad in BUYUK:
        if n >= deger:
            k, n = divmod(n, deger)
            s += ([] if (k == 1 and ad == "bin") else sayi_yazi(k)) + [ad]
    return s + _uc_basamak(n)


def _sayi_degistir(m: re.Match) -> str:
    kelimeler = sayi_yazi(int(m.group(1).replace(".", "")))
    if m.group(2):
        kelimeler += ["virgül"] + sayi_yazi(int(m.group(2)))
    if m.group(3):
        kelimeler[-1] += m.group(3)
    return " ".join(kelimeler)


def _ile_ekle(kelime: str) -> str:
    unluler = [c for c in kelime if c in INCE | KALIN]
    ek = "la" if unluler and unluler[-1] in KALIN else "le"
    return kelime + ("y" if kelime[-1] in INCE | KALIN else "") + ek


def normalize(metin: str, dil: str = "tr", kip: str = "normalize") -> list[str]:
    metin = ETIKET.sub(" ", metin)
    turkce = kip == "normalize" and dil_kodu(dil) in {"tr", "az"}
    if turkce:
        metin = SAYI.sub(_sayi_degistir, metin.translate(SAPKA))
    metin = kucult(metin, dil)
    if turkce:
        metin = re.sub(r"(\w)['’](\w)", r"\1\2", metin)
    kelimeler = NOKTALAMA.sub(" ", metin).replace("_", " ").split()
    if not turkce:
        return kelimeler
    cikti: list[str] = []
    for k in kelimeler:
        if k == "ile" and cikti:
            cikti[-1] = _ile_ekle(cikti[-1])
        else:
            cikti.append(k)
    return cikti


def levenshtein(a: list[str], b: list[str]) -> int:
    onceki = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        su = [i]
        for j, y in enumerate(b, 1):
            su.append(min(onceki[j] + 1, su[j - 1] + 1, onceki[j - 1] + (x != y)))
        onceki = su
    return onceki[-1]


def wer(ref: str, hyp: str, dil: str, kip: str = "normalize") -> tuple[float, int, int]:
    r, h = normalize(ref, dil, kip), normalize(hyp, dil, kip)
    d = levenshtein(r, h)
    return (d / len(r) if r else 0.0), d, len(r)


def _iki(ref: str, hyp: str, dil: str) -> str:
    w, d, n = wer(ref, hyp, dil, "normalize")
    w2, d2, n2 = wer(ref, hyp, dil, "ham")
    return f"{w*100:.1f}% ({d}/{n}) | {w2*100:.1f}% ({d2}/{n2})"


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--hyp")
    p.add_argument("--ref")
    p.add_argument("--cikti", help="klasör: her alt klasörde transkript.txt + kelimeler.json")
    p.add_argument("--dil", default="tr")
    a = p.parse_args(argv)
    if a.hyp:
        print("WER normalised | raw: " + _iki(Path(a.ref).read_text(encoding="utf-8"), Path(a.hyp).read_text(encoding="utf-8"), a.dil))
        return 0
    toplam = {"normalize": [0, 0], "ham": [0, 0]}
    satirlar = []
    for klasor in sorted(Path(a.cikti).iterdir()):
        hyp = klasor / "transkript.txt"
        ref = Path(a.ref) / f"{klasor.name}.txt"
        if not hyp.is_file() or not ref.is_file():
            continue
        kj = json.loads((klasor / "kelimeler.json").read_text(encoding="utf-8"))
        rt, ht, dl = ref.read_text(encoding="utf-8"), hyp.read_text(encoding="utf-8"), kj.get("dil", a.dil)
        for kip in toplam:
            _, d, n = wer(rt, ht, dl, kip)
            toplam[kip][0] += d; toplam[kip][1] += n
        s = kj["sureler"]; v = kj["vram_tepe_mb"]; y = kj["hizalama"]["yontem_sayilari"]
        satirlar.append(f"| {klasor.name} | {kj['ses_sn']:.1f} | {len(kj['kelimeler'])} | {_iki(rt, ht, dl)} | {s.get('asr_surec_sn', s.get('asr_cozumleme_sn', 0)):.1f} | {s.get('hizalama_surec_sn', s.get('hizalama_sn', 0)):.1f} | {v['asr']} / {v['hizalama']} | {y.get('ctc', 0)}/{len(kj['kelimeler'])} |")
    print("| ses | sn | kelime | WER normalised | WER raw | ASR sn | hizalama sn | VRAM tepe MB (asr / hizalama) | ctc kelime |")
    print("|---|---|---|---|---|---|---|---|---|")
    print("\n".join(satirlar))
    (dn, nn), (dh, nh) = toplam["normalize"], toplam["ham"]
    if nn:
        print(f"\nToplam WER normalised {dn/nn*100:.1f}% ({dn}/{nn}) · raw {dh/nh*100:.1f}% ({dh}/{nh})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
