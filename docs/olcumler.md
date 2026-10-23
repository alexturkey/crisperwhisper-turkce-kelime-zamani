# Measurements / Ölçümler

Machine: GTX 1050 Ti 4 GB (driver 581.29), i7-7700HQ, 16 GB RAM, Windows 10 22H2 + WSL2 Ubuntu 24.04, Python 3.12.3,
venv on an NTFS mount (`/mnt/e`). Date: 2026-10-23. Everything below was produced by `python -m transkript` on this
machine; nothing is quoted from papers or other READMEs.

## Method

- **Audio with known text**: the seven synthetic Turkish voices of our sister project
  (voxcpm2-turkce-ses-tasarimi, `hazir_sesler/*/ornek_okuma.mp3`, Apache-2.0), 13-40 s each, read from
  `ornek_okuma_metni.txt`. English: one 7.9 s edge-tts sentence pair and one 3.4 s VOiCES corpus clip (real room recording). Japanese: one 7.5 s edge-tts sentence pair. Reference texts are the strings that were synthesised / the corpus transcript.
- **WER**: `jiwer`-free plain normaliser: lowercase (Turkish-aware), punctuation and `[...]` event tags removed,
  whitespace collapsed; word-level Levenshtein distance / reference words. Script: `tests/wer_olc.py`.
- **Time**: `kelimeler.json` → `sureler` (wall clock per stage, worker process start to exit, including model load)
  and `asr.sureler` / `hizalama.sureler` (inside the workers). **VRAM**: `vram_tepe_mb` = peak `nvidia-smi memory.used`
  polled every 0.5 s while the worker ran (includes whatever else the GPU held, ~0 MB here).
- **Word times**: not measured against hand labels. The method is described in `docs/diller.md`; `yontem_sayilari`
  in `kelimeler.json` tells how many words got a real CTC alignment.

## Results

Run 2026-10-23, GTX 1050 Ti 4 GB, WSL2 Ubuntu, driver CUDA 12.x, int8, **batch mode** (`--liste`, 12 items in one run:
the 11 files below + `tr_ornek` again with `--dil auto`). Per-file times are the model work only; loading is shared and
listed after the table.

| audio | s | words | WER | ASR decode s | alignment s | words with real CTC time |
|---|---|---|---|---|---|---|
| tr_belgesel_hanim | 32.7 | 65 | 0.0% (0/65) | 4.4 | 1.3 | 65/65 |
| tr_cekici_spiker | 13.3 | 26 | 0.0% (0/26) | 2.0 | 0.4 | 26/26 |
| tr_gizemli_bilge | 27.7 | 56 | 0.0% (0/56) | 2.4 | 1.0 | 56/56 |
| tr_haber_spikeri | 18.0 | 28 | 7.1% (2/28) | 2.2 | 0.6 | 28/28 |
| tr_masal_cadisi | 29.5 | 64 | 0.0% (0/64) | 2.8 | 1.0 | 64/64 |
| tr_ornek | 13.3 | 26 | 0.0% (0/26) | 2.1 | 0.4 | 26/26 |
| tr_tok_anlatici | 28.4 | 55 | 1.8% (1/55) | 2.6 | 1.0 | 55/55 |
| tr_yasli_bilge | 29.1 | 43 | 4.7% (2/43) | 2.6 | 1.0 | 43/43 |
| **Turkish total** | 192.0 | 363 | **0% (0/363)** without circumflex · raw 1.4% (5/363) | 21.1 | 6.9 | 363/363 |
| en_tts | 7.9 | 25 | 0.0% (0/25) | 5.6 | 7.7 | 25/25 |
| en_voices | 3.4 | 9 | 0.0% (0/9) | 1.6 | 0.1 | 9/9 |
| ja_tts | 7.5 | 33 chars | CER 9.4% (3/32 chars) | 3.2 | 0.5 | 31/33 (2 interpolated) |

Language detection (`--dil auto`, first 30 s of `tr_ornek`): `tr` 0.992, `en` 0.003, `es` 0.001 → same transcript as with `--dil tr`.

Shared cost of the whole 12-item run (one ASR process, one alignment process): total 602 s wall clock;
ASR process 326 s (import 80 s, CrisperWhisper load 200 s, decoding the rest); alignment process 268 s
(import 34 s, model loads 167 s: English 16 s, Japanese 108 s, Turkish 43 s). Peak VRAM 1371 MB (ASR) / 1653 MB (alignment).

## Real recordings: FLEURS Turkish

Run 2026-10-23 09:29-09:32, same machine, **fresh venv from a clean copy of this repo** (`kur.sh --adim python,ayar`),
batch mode, 11 items (`ornek/ornek.mp3` + 10 FLEURS clips). Data: Google FLEURS (`google/fleurs`, revision `70bb2e8`),
`tr_tr` test split, the first 10 clips in `audio/test.tar.gz` order, reference = `raw_transcription`. License CC BY 4.0
(dataset card). Audio is not in this repo.

| clip | s | words | WER |
|---|---|---|---|
| 1 | 14.2 | 20 | 5.0% (1/20) |
| 2 | 12.4 | 14 | 0.0% (0/14) |
| 3 | 11.1 | 11 | 27.3% (3/11) |
| 4 | 16.6 | 24 | 0.0% (0/24) |
| 5 | 15.8 | 26 | 3.8% (1/26) |
| 6 | 4.2 | 6 | 0.0% (0/6) |
| 7 | 10.2 | 14 | 35.7% (5/14) |
| 8 | 9.1 | 17 | 11.8% (2/17) |
| 9 | 5.8 | 11 | 9.1% (1/11) |
| 10 | 22.2 | 35 | 14.3% (5/35) |
| **total** | 121.6 | 178 | **10.1% (18/178)**, same with or without the circumflex |

Every recognised word got a real CTC time (`ctc` for all of them). ASR decode 17.2 s, alignment 3.6 s for 121.6 s of audio. Whole
11-item run 180 s wall clock (ASR process 90 s: import 17 s, model load 51 s; alignment process 89 s). Peak VRAM
1371 MB (ASR) / 2411 MB (alignment). Roughly half of the errors are spelling conventions, not mishearing: `40.000'in`
written as `kırk binin` (verbatim model writes numbers as spoken), `yöntemi ile` → `yöntemiyle`, `çevrimiçi` →
`çevrim içi`, `Okulu'ndan` → `okulundan`; the rest are names and rare words (`Meşhed` → `Meşet`, `Upolu` → `Upol`,
`sezyum` → `sezium`, `iyodin` → `iodin`, `nispeten` → `nispeden`, `Şehir` → `Şiir`). Ten clips is a smoke test,
not a benchmark.

## Reading the numbers

- **All five Turkish "errors" are the circumflex**: the reference writes `hâlâ`, `hikâye`; the model writes `hala`,
  `hikaye` (the common modern spelling). The headline number does not count the circumflex
  as an error (0/363); the per-file rows and `tests/wer_olc.py` show the raw count (5/363).
- **Japanese**: word WER means nothing for unspaced text, so the row gives character error rate. All three character
  errors are one word: `今日` (kanji) was written `きょう` (the same reading in kana).
- **Synthetic audio is easy audio.** Every file except `en_voices` is clean synthetic (TTS) speech. This set shows the pipeline
  works end to end and the times; it is not a benchmark for noisy, overlapping or accented speech.
- **Loading dominates on this machine**: the venv and models live on a Windows drive mounted into WSL2 (`/mnt/e`,
  9P file sharing), so importing torch and reading 1.6 GB of model weights takes minutes. The model work for 192 s of
  Turkish audio is about 28 s. Use batch mode (`--liste` or several files) so loading is paid once; installing the
  venv and models on the Linux filesystem (`~/`) should shorten loading further (not measured here).
- One file at a time (same machine, earlier run): 459 s for the 7.9 s English file, 727 s for the Japanese one,
  almost all of it loading.
