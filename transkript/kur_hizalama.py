"""Downloads the alignment models for the languages you ask for (default: tr en) at the pinned revision and verifies
the pinned sha256 values. Other languages are fetched on first use from their `main` revision (experimental).

  python -m transkript.kur_hizalama --kok <kok> --diller tr en ja
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from transkript import ayarlar  # noqa: E402
from transkript.diller import HF, TORCHAUDIO  # noqa: E402


def hf_indir(kod: str, kayit: dict, hf_home: Path) -> None:
    from huggingface_hub import hf_hub_download

    model = kayit["model"]
    commit = kayit.get("commit")
    if not commit or commit.startswith("__"):
        print(f"  {kod}: {model} sabit commit yok, main (deneysel)")
        commit = None
    for dosya, sha in kayit["dosyalar"].items():
        yol = Path(hf_hub_download(model, dosya, revision=commit, cache_dir=str(hf_home / "hub")))
        if sha and not sha.startswith("__"):
            got = ayarlar.sha256(yol)
            if got != sha:
                raise SystemExit(f"{kod}: {dosya} sha256 tutmadı: {got} (beklenen {sha})")
            print(f"  {kod}: {dosya} sha256 doğru")
        else:
            print(f"  {kod}: {dosya} indirildi (sha sabit değil)")


def torchaudio_indir(kod: str, kayit: dict, torch_home: Path) -> None:
    import torchaudio

    os.environ["TORCH_HOME"] = str(torch_home)
    paket = getattr(torchaudio.pipelines, TORCHAUDIO[kod])
    paket.get_model()  # downloads into TORCH_HOME/hub/checkpoints
    ad = kayit["url"].rsplit("/", 1)[-1]
    yol = torch_home / "hub" / "checkpoints" / ad
    sha = kayit.get("sha256", "")
    if yol.is_file() and sha and not sha.startswith("__"):
        got = ayarlar.sha256(yol)
        if got != sha:
            raise SystemExit(f"{kod}: {ad} sha256 tutmadı: {got} (beklenen {sha})")
        print(f"  {kod}: {ad} sha256 doğru")
    else:
        print(f"  {kod}: {ad} indirildi" + ("" if yol.is_file() else " (yol bulunamadı, torchaudio önbelleği farklı olabilir)"))


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--kok", required=True)
    p.add_argument("--diller", nargs="*", default=["tr", "en"])
    a = p.parse_args(argv)
    kok = Path(a.kok)
    hf_home, torch_home = kok / "hf", kok / "torch"
    os.environ["HF_HOME"] = str(hf_home)
    m = ayarlar.manifest()["hizalama"]
    for kod in a.diller:
        kod = kod.lower()
        if kod in TORCHAUDIO:
            torchaudio_indir(kod, m.get(kod, {"url": "https://download.pytorch.org/torchaudio/models/" + TORCHAUDIO[kod].lower() + ".pth"}), torch_home)
        elif kod in m:
            hf_indir(kod, m[kod], hf_home)
        elif kod in HF:
            hf_indir(kod, {"model": HF[kod], "commit": None, "dosyalar": {"pytorch_model.bin": None, "config.json": None, "vocab.json": None, "preprocessor_config.json": None, "tokenizer_config.json": None, "special_tokens_map.json": None}}, hf_home)
        else:
            raise SystemExit(f"{kod}: hizalama modeli tablosunda yok (python -m transkript --diller)")
    print("HIZALAMA_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
