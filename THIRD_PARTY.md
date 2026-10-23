# Third-party components / Üçüncü taraf bileşenler

This project's own code is Apache-2.0 (`LICENSE`). It builds on the following; each keeps its own license. **Nothing
below is bundled in this repository**: models and packages are downloaded by `scripts/kur.sh` at pinned versions.

| Component | What we use | License | Source |
|---|---|---|---|
| **CrisperWhisper 2.0 Turbo** weights (Nyra Health GmbH) | ASR model, `model.safetensors` at commit `de0369c8…`, converted to CTranslate2 on your machine | **nyra health Non-Commercial Research License v1.0** — non-commercial only; converted weights are derivative works under the same license, not redistributable under an open license | https://huggingface.co/nyralabs/CrisperWhisper2.0_turbo |
| `crisperwhisper` 2.0.x (Nyra Health) | inference code, longform/continuation, hallucination repair, CT2 conversion | MIT | https://github.com/nyrahealth/CrisperWhisper · PyPI |
| `ctranslate2-crisperwhisper` 4.7.1.post3 (Nyra Health fork of CTranslate2, OpenNMT) | CUDA int8 inference runtime (Linux wheels only) | MIT | https://github.com/nyrahealth/CTranslate2 · https://github.com/OpenNMT/CTranslate2 |
| **mpoyraz/wav2vec2-xls-r-300m-cv7-turkish** (commit `708639f5…`) | Turkish CTC alignment model (fine-tuned from facebook/wav2vec2-xls-r-300m on Common Voice 7 + MediaSpeech) | CC BY 4.0 — attribution: Mehmet Poyraz | https://huggingface.co/mpoyraz/wav2vec2-xls-r-300m-cv7-turkish |
| **jonatasgrosman/wav2vec2-large-xlsr-53-japanese** (commit `cf031e02…`) | Japanese CTC alignment model | Apache-2.0 | https://huggingface.co/jonatasgrosman/wav2vec2-large-xlsr-53-japanese |
| torchaudio `WAV2VEC2_ASR_BASE_960H` (fairseq, Meta) | English CTC alignment model | MIT (fairseq weights), BSD-2 (torchaudio) | https://pytorch.org/audio/stable/pipelines.html |
| Other alignment checkpoints in `transkript/diller.py` (VoxPopuli pipelines, jonatasgrosman/*, and others) | experimental languages; downloaded on first use, unpinned | each repository's own license: check the model card before use | listed in `transkript/diller.py` |
| Alignment model table | which checkpoint per language | the table follows WhisperX 3.8.6 (`whisperx/alignment.py`), BSD-2-Clause, © Max Bain; WhisperX code itself is not used | https://github.com/m-bain/whisperX |
| PyTorch, torchaudio (`forced_align`, `merge_tokens`) | CTC forced alignment | BSD-3 / BSD-2 | https://pytorch.org |
| transformers (Hugging Face) | loading wav2vec2 checkpoints | Apache-2.0 | https://github.com/huggingface/transformers |
| NumPy, python-soundfile (libsndfile), python-soxr | audio read/resample | BSD-3 / BSD-3 (libsndfile LGPL-2.1+) / LGPL-2.1+ | PyPI |
| NVIDIA CUDA libraries (`nvidia-*-cu12` wheels pulled by torch and the CT2 fork) | GPU runtime | NVIDIA CUDA EULA | PyPI |

## Example audio (`ornek/`)

`ornek/ornek.mp3` is a synthetic Turkish voice generated with VoxCPM2 in our sister project
(github.com/alexturkey/voxcpm2-turkce-ses-tasarimi, Apache-2.0); no real person's voice. Its text is `ornek/ornek_metin.txt`.

## Measurement data (not in this repository)

`docs/olcumler.md` and the README quote short text excerpts and results from **Google FLEURS** (`google/fleurs`,
tr_tr test split), CC BY 4.0, © Google; Conneau et al., "FLEURS: Few-shot Learning Evaluation of Universal
Representations of Speech", 2022. No FLEURS audio is distributed here.

## Model card notice

The CrisperWhisper license forbids commercial use without a separate license and the use of outputs to train
commercial models. The alignment checkpoints were trained on Common Voice / LibriSpeech / VoxPopuli data; see their
model cards.
