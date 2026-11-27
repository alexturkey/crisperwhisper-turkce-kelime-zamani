# Sürüm notları / Release notes

## Unreleased

**TR**
- Ajan karşılama (kit KL-23): `AGENTS_HIZLI.md` ve `AGENTS.md` tepesinde "önce bunu yap" bloğu (önce `bash scripts/tani.sh`, git dışı `DURUM.md` defteri, ASLA/ÖNCE SOR listeleri, aynı hata iki kez dur), README'de tek cümlelik "ajanınıza verin" bloğu, `scripts/tani.sh`'a salt okur SAPMA bölümü (değişken değerleri basılmaz). Kalite ve çalışma davranışı değişmedi.
- Kurulumda `--kuru` (Windows: `kur.ps1 -Kuru`, çift tık: `scripts/kur.cmd`): hiçbir şey yazmaz ya da indirmez; kart, sürücü, disk, RAM ve araç eksiklerini tek listede, `[STT-E-...]` kodlarıyla basar (eksik varsa çıkış 3). Varsayılan kurulum davranışı değişmedi.
- Yerel teşhis `scripts/tani.sh` (kişisel ad ve yolları siler, ağa çıkmaz); hata kodları `docs/hata_imzalari.json` ve `docs/SIK_HATALAR.md`.
- Hızlı denetim `scripts/denetim.py --hizli` (gizlilik ve gizli karakter taraması, sabit sürümler, manifest, kalite sabitleri, README çeviri eşliği), `scripts/on_kontrol.sh`, CI (rapor modu, eylemler SHA'ya sabit).
- Belgeler: CONTRIBUTING, PRIVACY, SUPPORT, CODE_OF_CONDUCT, AGENTS_HIZLI, llms.txt, GEMINI/CLAUDE/Copilot yönlendiricileri (tek kaynak AGENTS.md), PR şablonu, Donanım testi ve Soru/fikir issue formları, SECURITY'ye desteklenen sürümler ve ajan prompt-injection paragrafı, README'ye Hızlı başlangıç ve Disk düzeni ve kaldırma.
- Kurulum düzeni: pip/HF/torch önbelleği yalnız boşsa köke yönlenir (sizin değeriniz ezilmez), yarım indirme `.part`'tan devam eder, mevcut `.venv`/`ayarlar.json` taşınmaz; `tests/test_kurulum_duzeni.py`.
- Boş issue kapalı; güvenlik bildirimi ve destek bağlantıları issue ekranında.

**EN**
- Agent onboarding (kit KL-23): a do-this-first block at the top of `AGENTS_HIZLI.md` and `AGENTS.md` (run `bash scripts/tani.sh` first, git-ignored `DURUM.md` notebook, NEVER / ASK lists, same error twice stop), a one-sentence "give this to your agent" block in the README, and a read-only DEVIATIONS section in `scripts/tani.sh` (variable values are never printed). Quality and run behaviour unchanged.
- Install gets `--kuru` (Windows: `kur.ps1 -Kuru`, double-click: `scripts/kur.cmd`): writes and downloads nothing; lists missing GPU, driver, disk, RAM and tools in one list with `[STT-E-...]` codes (exit 3 if anything is missing). The default install behaviour is unchanged.
- Local diagnosis `scripts/tani.sh` (strips personal names and paths, no network); error codes in `docs/hata_imzalari.json` and `docs/SIK_HATALAR.md`.
- Quick checks `scripts/denetim.py --hizli` (privacy and hidden-character scan, pinned versions, manifest, quality constants, README translation parity), `scripts/on_kontrol.sh`, CI (report mode, actions pinned to SHAs).
- Docs: CONTRIBUTING, PRIVACY, SUPPORT, CODE_OF_CONDUCT, AGENTS_HIZLI, llms.txt, GEMINI/CLAUDE/Copilot pointers (single source AGENTS.md), PR template, Hardware test and Question/idea issue forms, supported versions and an agent prompt-injection paragraph in SECURITY, Quick start and Disk layout and removal in the README.
- Install layout: pip/HF/torch caches point into the root only when empty (your own value is kept), interrupted downloads resume from `.part`, an existing `.venv`/`ayarlar.json` is never moved; `tests/test_kurulum_duzeni.py`.
- Blank issues are off; security reporting and support links are on the issue chooser.

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
- Ölçümler GTX 1050 Ti 4 GB'da (`docs/olcumler.md`); WER iki sayı: normalize (ana, kurallar `tests/wer_olc.py`) ve ham.
  FLEURS tr_tr 10 gerçek kayıt: normalize %6,2, ham %10,1.

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
- Measurements on a GTX 1050 Ti 4 GB (`docs/olcumler.md`); WER as two numbers: normalised (main, rules in
  `tests/wer_olc.py`) and raw. FLEURS tr_tr, 10 real recordings: normalised 6.2%, raw 10.1%.
