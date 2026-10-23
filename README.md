# crisperwhisper-turkce-kelime-zamani

**Verbatim speech-to-text with word timestamps on a 4 GB GPU.** CrisperWhisper 2.0 Turbo (CTranslate2, CUDA int8)
writes down *exactly* what was said (fillers, false starts, repetitions kept); a wav2vec2 CTC forced alignment then
gives every word its start and end time. Output: text, word JSON, SRT and VTT. Built and measured for Turkish, works
for every language the models know (`docs/diller.md`). Linux or Windows via WSL2; one command to install.

[Türkçe README](README.tr.md) · [Languages and word splitting](docs/diller.md) · [Measurements](docs/olcumler.md) · [Install guide for AI agents](AGENTS.md) · [Responsible use](ETHICS.md)

> **Model license:** the CrisperWhisper 2.0 weights are **non-commercial** (nyra health Non-Commercial Research
> License). This repository's code is Apache-2.0, but running it inside a paid product needs a commercial license from
> Nyra Health. Weights are not in this repo; the installer downloads them from a pinned commit. See [NOTICE](NOTICE).

## What you get

```
cikti/kayit_20261023_0210/
  transkript.txt      verbatim text
  kelimeler.json      every word: start, end, score, how it was timed; language; timings; both models' identities
  transkript.srt/vtt  caption lines (sentence or ~7 s)
  kelimeler.srt/vtt   one cue per word (karaoke-style)
  ses_16k_mono.wav    the audio as the models heard it
```

`kelimeler.json` word entry: `{"kelime": "dünya.", "start": 0.62, "end": 1.01, "skor": 0.93, "yontem": "ctc"}`.
`yontem` is `ctc` for a real alignment, `ara_deger` (interpolated between neighbours) when the alignment model's
vocabulary had none of the word's characters, `esit_bolme` when a segment could not be aligned at all.

## Install (Linux, or Windows 10/11 with WSL2)

Needs: NVIDIA GPU with ≥ 4 GB VRAM and driver ≥ 570 (CUDA 12.8), Python 3.10-3.12, `curl`, ~7 GB disk
(torch 3 GB, model 1.6 GB download + 1.6 GB converted, alignment models 0.4-1.3 GB per language). No sudo, no
system CUDA install, no PATH changes; everything goes under the root you choose.

**Linux**
```bash
git clone https://github.com/alexturkey/crisperwhisper-turkce-kelime-zamani.git
cd crisperwhisper-turkce-kelime-zamani
bash scripts/kur.sh --kok ~/stt            # ~15 min, ~6 GB download; markers PYTHON_OK MODEL_OK DONUSUM_OK HIZALAMA_OK AYAR_OK KONTROL_OK KURULUM_OK
.venv/bin/python -m transkript ornek/ornek.mp3 --dil tr
```

**Windows** (the CTranslate2 fork ships Linux wheels only, so the engine runs inside WSL2; the wrappers hide that)
```powershell
wsl --install -d Ubuntu          # once, admin; reboot; then open "Ubuntu" once to create your user
git clone https://github.com/alexturkey/crisperwhisper-turkce-kelime-zamani.git
cd crisperwhisper-turkce-kelime-zamani
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\kur.ps1 -Kok E:\stt
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\stt.ps1 -Ses ornek\ornek.mp3 -Dil tr
```
`-ExecutionPolicy Bypass` applies to that one process only; read `scripts\kur.ps1` and `scripts/kur.sh` before running
them, as with any installer. Re-run after a failure: verified downloads are skipped.

`--diller "tr en ja"` (kur.sh) / `-Diller "tr en ja"` (kur.ps1) chooses which alignment models to pre-download
(default `tr en`); any other language in the table downloads on first use.

## Use

```bash
.venv/bin/python -m transkript kayit.mp3                       # Turkish (default), output under cikti/
.venv/bin/python -m transkript kayit.wav --dil en --cikti out  # English
.venv/bin/python -m transkript a.mp3 b.wav c.mp3 --cikti out   # batch: models load once, out/<name>/ per file
.venv/bin/python -m transkript --liste isler.tsv --cikti out   # batch from a list: <path>[<TAB><lang>] per line
.venv/bin/python -m transkript kayit.m4a --dil auto            # detect on the first 30 s (needs ffmpeg for m4a/mp4)
.venv/bin/python -m transkript --diller                        # languages with an alignment model (tested / experimental)
.venv/bin/python -m transkript --kontrol                       # environment check -> KONTROL_OK
```
Input: anything libsndfile decodes (wav, flac, ogg, mp3); video or other containers need `ffmpeg` on PATH.
Options: `--bicim json,srt,vtt`, `--hizalama-modeli <HF wav2vec2 CTC id>` (other language or your own checkpoint),
`--hizalama-cihazi cpu` (alignment on CPU if the GPU is too small; slower), `--zaman-asimi`.

## How it works

1. Audio → 16 kHz mono WAV (soundfile + soxr; ffmpeg only for video containers).
2. **ASR worker** (own process): `crisperwhisper` CT2 backend, `compute_type=int8`, verbatim mode, longform
   "continuation" chunking with hallucination repair and early-EOT recovery, native word timestamps on. The process
   exits and frees the GPU.
3. **Alignment worker** (own process): the ASR words are grouped into ≤ 18 s segments (sentence ends, > 2.5 s gaps);
   each segment's characters are force-aligned with the language's wav2vec2 CTC model
   (`torchaudio.functional.forced_align` + `merge_tokens`), so a word's time spans from its first to its last recognised
   character; silence is never swallowed into a word. CJK/Thai text is timed per character (`docs/diller.md`).
4. Checks (chronological, inside the audio, no overlaps) and outputs. The native CrisperWhisper times stay in
   `kelimeler.json` → `asr_kelimeleri` for comparison.

Two processes instead of one so a 4 GB card never holds both models: CT2 turbo int8 ≈ 1371 MB peak, the
Turkish alignment model ≤ 1653 MB peak (nvidia-smi, GTX 1050 Ti).

## Languages and word splitting

`--dil xx` for any Whisper language (`--dil auto` detects from the first 30 s). What a "word" is depends on the script
(full table and reasoning: [docs/diller.md](docs/diller.md)):

| Script | Unit in `kelimeler.json` | Alignment model | Status |
|---|---|---|---|
| Space-separated (tr, en, de, fr, es, ru, ar, he, ...) | whitespace token, punctuation attached | per-language wav2vec2 CTC (`ayarlar/manifest.json` table) | **tr, en tested**; others experimental (table from WhisperX, not run here) |
| Japanese, Chinese, Thai, Lao, Burmese, Khmer | **one character** (kanji/kana/hanzi; Latin and digits inside stay whole) | ja/zh wav2vec2 CTC in the table; th/lo/my/km/yue have none: pass `--hizalama-modeli <HF id>` or the run stops with a clear message | **ja tested**; zh experimental; the rest need your own model |
| Korean | eojeol (space-separated block) | ko wav2vec2 | experimental |
| Arabic, Hebrew, Persian, Urdu (RTL) | word, kept in **logical (spoken) order**, no reordering | ar/he/fa/ur wav2vec2 | experimental |

No bundled morpheme splitter: if you need Japanese words (MeCab/fugashi), Chinese words (jieba) or Thai words
(pythainlp), run the tokenizer on `metin` and regroup the per-character times (first char start → last char end);
`docs/diller.md` shows the 10-line recipe. Every word carries `yontem`: `ctc` (aligned), `ara_deger` (interpolated
between neighbours when a character is missing from the model's vocabulary), `esit_bolme` (the whole segment could not be
aligned; its words share the segment time equally).

## Speed and accuracy (measured here, not quoted)

GTX 1050 Ti 4 GB, WSL2 Ubuntu 24.04, i7-7700HQ. Method and the full table: [docs/olcumler.md](docs/olcumler.md).

| set | audio | WER normalised (main) | WER raw | note | model work (ASR + alignment) |
|---|---|---|---|---|---|
| Turkish, 8 files (clean synthetic TTS) | 192 s | **0% (0/363)** | 1.4% (5/363) | all 5 raw errors are the circumflex (`hâlâ` → `hala`) | 21.1 s + 6.9 s |
| **Turkish, FLEURS tr_tr test, 10 real recordings** | 122 s | **6.2% (11/176)** | 10.1% (18/178) | 7 raw errors are spelling conventions (below) | 17.2 s + 3.6 s |
| English, 2 files (1 TTS, 1 real room recording) | 11.3 s | 0% (0/34) | 0% (0/34) | | 7.2 s + 7.8 s |
| Japanese, 1 file (TTS) | 7.5 s | CER 9.4% (3/32 chars) | same | `今日` written as `きょう` (same reading) | 3.2 s + 0.5 s |

Batch mode, all 12 items in one run: 602 s wall clock, of which about 480 s is importing torch and loading models from a
Windows drive mounted into WSL2. Single-file runs pay that loading every time (459-727 s per file here), so pass
several files or `--liste`. Peak VRAM: 1371 MB (ASR) / up to 2411 MB (alignment).

**How "normalised" is computed** (`tests/wer_olc.py`, applied the same way to reference and our output; both numbers
are always printed):

1. lowercase (Turkish `I`/`İ` aware), punctuation and `[event]` tags removed (this alone is the raw number);
2. circumflex folded: `â/î/û` → `a/i/u` (`hâlâ` = `hala`);
3. numbers written out in Turkish words, suffix kept (`40.000'in` = `kırk binin`);
4. apostrophe removed, suffix joined (`Okulu'ndan` = `okulundan`);
5. `ile` joined to the previous word (`yöntemi ile` = `yöntemiyle`).

Nothing else is forgiven: names, wrong words and compound spacing (`çevrimiçi` → `çevrim içi`) still count.

| FLEURS reference | ours | counted? |
|---|---|---|
| … ve **40.000'in** biraz altında … | … ve **kırk binin** biraz altında … | no: same words (rule 3) |
| … yorumlama **yöntemi ile** … | … yorumlama **yöntemiyle** … | no: same word (rule 5) |
| … **Eyalet Başkenti'ne** … | … **eyalet başkentine** … | no: case and apostrophe (rules 1, 4) |
| … uçağı **Meşhed'deki** bir pisti … | … uçağı **Meşet'teki** bir pisti … | **yes**: wrong name |
| … radyoaktif **sezyum** ve **iyodin** tespit **edildi** | … radyoaktif **sezium** ve **iodin** tespit **edilir** | **yes**: 3 errors |
| … **Şehir Upolu** adasındadır … | … **Şiir, Upol** Adası'ndadır … | **yes**: 2 errors |

The synthetic rows are clean TTS voices: they show the pipeline works end to end, not how it does on real or noisy
recordings. FLEURS (Google, tr_tr test split, first 10 clips, CC BY 4.0) is real read speech; ten clips is a smoke
test, not a benchmark. Word-time accuracy was **not** measured against hand labels; the method's behaviour is
described in `docs/diller.md`. Nyra reports CrisperWhisper 2.0's numbers on their own benchmark
(`github.com/nyrahealth/CrisperWhisper`); those are theirs, not ours.

## Limits

- Non-commercial model license (above). Verbatim output is personal data: see [ETHICS.md](ETHICS.md).
- One GPU job at a time; ~4.5 GB free RAM during conversion and alignment.
- Windows needs WSL2 (no native Windows path for the CT2 fork). Linux + CUDA 12 only; no AMD/Intel, no CPU path for
  the ASR (CTranslate2 int8 on CPU runs but we did not measure it; set `"cihaz": "cpu"` in `ayarlar.json` to try).
- Long silence or music can still produce repeated or invented text; the library's repair catches most of it, not all.
- Overlapping speakers, no diarization. Languages other than tr/en/ja are experimental (`docs/diller.md`).

## License and credits

Code: Apache-2.0, Copyright 2026 Ali Haydar Ozturk. Models: CrisperWhisper 2.0 Turbo (Nyra Health, non-commercial
research license; inference code MIT), wav2vec2 alignment checkpoints (mpoyraz CC BY 4.0, jonatasgrosman Apache-2.0,
torchaudio/fairseq MIT), CTranslate2 (OpenNMT, MIT), PyTorch. Full list: [THIRD_PARTY.md](THIRD_PARTY.md).
Sister project: [voxcpm2-turkce-ses-tasarimi](https://github.com/alexturkey/voxcpm2-turkce-ses-tasarimi) (Turkish
voice design, the source of the example audio). Not affiliated with Nyra Health or OpenNMT.
