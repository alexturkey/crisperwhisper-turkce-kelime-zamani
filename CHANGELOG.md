# Sürüm notları / Release notes

## v0.1.0 — 2026-10-23

İlk sürüm / first release.

**TR**
- CrisperWhisper 2.0 Turbo (CTranslate2, CUDA int8, verbatim) + wav2vec2 CTC zorlamalı hizalama ile kelime zamanı;
  çıktı txt / JSON / SRT / VTT (cümle ve kelime düzeyi).
- Tek komut kurulum `scripts/kur.sh` (Linux, WSL2); Windows sarmalayıcıları `kur.ps1`, `stt.ps1`. Her indirme sabit
  commit + sha256; ağırlık depoda yok; model lisansı ticari değil (NOTICE).
- Dil tablosu (`docs/diller.md`): tr/en/ja burada ölçüldü, 35+ dil deneysel; CJK/Tay karakter birimi; sağdan sola
  diller mantıksal sırada.
- Toplu kip: `python -m transkript a.mp3 b.wav` ya da `--liste isler.tsv`; modeller bir kez yüklenir, bir dosyanın
  hatası diğerlerini durdurmaz.
- `--kontrol` gerçek bir CUDA çekirdeği koşturur (yalnız `is_available` değil).
- Ölçümler GTX 1050 Ti 4 GB'da (`docs/olcumler.md`).

**EN**
- CrisperWhisper 2.0 Turbo (CTranslate2, CUDA int8, verbatim) + wav2vec2 CTC forced alignment for word times;
  txt / JSON / SRT / VTT output (sentence and word level).
- One-command install `scripts/kur.sh` (Linux, WSL2); Windows wrappers `kur.ps1`, `stt.ps1`. Every download pinned
  by commit + sha256; no weights in the repo; non-commercial model license (NOTICE).
- Language table (`docs/diller.md`): tr/en/ja measured here, 35+ languages experimental; CJK/Thai per-character
  units; right-to-left languages in logical order.
- Batch mode: `python -m transkript a.mp3 b.wav` or `--liste jobs.tsv`; models load once, one file's failure does not
  stop the others.
- `--kontrol` runs a real CUDA kernel (not only `is_available`).
- Measurements on a GTX 1050 Ti 4 GB (`docs/olcumler.md`).
