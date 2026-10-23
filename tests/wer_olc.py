"""WER ölçümü / WER measurement for a folder of (audio, reference text) pairs that were already transcribed.

  python tests/wer_olc.py --cikti cikti/olcum --ref sesler/   # every <ad>.txt next to a transcribed cikti/olcum/<ad>/ folder
  python tests/wer_olc.py --hyp cikti/ilk/transkript.txt --ref ornek/ornek_metin.txt

Normaliser: lowercase (Turkish-aware), [event] tags and punctuation removed, whitespace collapsed. Word-level
Levenshtein. Prints per file and total; also reads kelimeler.json for timings and VRAM when present.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from transkript.diller import kucult  # noqa: E402

NOKTALAMA = re.compile(r"[^\w\s']", re.UNICODE)
ETIKET = re.compile(r"\[[^\]]*\]")


def normalize(metin: str, dil: str = "tr") -> list[str]:
    metin = ETIKET.sub(" ", metin)
    metin = kucult(metin, dil)
    metin = NOKTALAMA.sub(" ", metin).replace("_", " ")
    return metin.split()


def levenshtein(a: list[str], b: list[str]) -> int:
    onceki = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        su = [i]
        for j, y in enumerate(b, 1):
            su.append(min(onceki[j] + 1, su[j - 1] + 1, onceki[j - 1] + (x != y)))
        onceki = su
    return onceki[-1]


def wer(ref: str, hyp: str, dil: str) -> tuple[float, int, int]:
    r, h = normalize(ref, dil), normalize(hyp, dil)
    d = levenshtein(r, h)
    return (d / len(r) if r else 0.0), d, len(r)


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--hyp")
    p.add_argument("--ref")
    p.add_argument("--cikti", help="klasör: her alt klasörde transkript.txt + kelimeler.json")
    p.add_argument("--dil", default="tr")
    a = p.parse_args(argv)
    if a.hyp:
        w, d, n = wer(Path(a.ref).read_text(encoding="utf-8"), Path(a.hyp).read_text(encoding="utf-8"), a.dil)
        print(f"WER {w*100:.1f}% ({d}/{n})")
        return 0
    toplam_d = toplam_n = 0
    satirlar = []
    for klasor in sorted(Path(a.cikti).iterdir()):
        hyp = klasor / "transkript.txt"
        ref = Path(a.ref) / f"{klasor.name}.txt"
        if not hyp.is_file() or not ref.is_file():
            continue
        kj = json.loads((klasor / "kelimeler.json").read_text(encoding="utf-8"))
        w, d, n = wer(ref.read_text(encoding="utf-8"), hyp.read_text(encoding="utf-8"), kj.get("dil", a.dil))
        toplam_d += d; toplam_n += n
        s = kj["sureler"]; v = kj["vram_tepe_mb"]; y = kj["hizalama"]["yontem_sayilari"]
        satirlar.append(f"| {klasor.name} | {kj['ses_sn']:.1f} | {len(kj['kelimeler'])} | {w*100:.1f}% ({d}/{n}) | {s.get('asr_surec_sn', s.get('asr_cozumleme_sn', 0)):.1f} | {s.get('hizalama_surec_sn', s.get('hizalama_sn', 0)):.1f} | {s.get('toplam_sn', 0):.1f} | {v['asr']} / {v['hizalama']} | {y.get('ctc', 0)}/{len(kj['kelimeler'])} |")
    print("| ses | sn | kelime | WER | ASR sn | hizalama sn | toplam sn (toplu kipte 0: ortak süre ozet.json) | VRAM tepe MB (asr / hizalama) | ctc kelime |")
    print("|---|---|---|---|---|---|---|---|---|")
    print("\n".join(satirlar))
    if toplam_n:
        print(f"\nToplam WER {toplam_d/toplam_n*100:.1f}% ({toplam_d}/{toplam_n})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
