"""Language table: which alignment model, which word unit, which direction.

Alignment models per language follow the table WhisperX (BSD-2-Clause, github.com/m-bain/whisperX) uses; the
models themselves are third-party wav2vec2 CTC checkpoints on Hugging Face or torchaudio (licenses in THIRD_PARTY.md).
Only the languages in SINANMIS were run end to end by us; everything else is EXPERIMENTAL (model downloaded from the
`main` revision, unpinned, never measured here). See docs/diller.md for how words are split per language group.
"""

from __future__ import annotations

import re

# ASR word unit for these languages is not whitespace-separated: the transcript is split into characters
# (CJK ideographs / kana / hangul-free scripts) with Latin or digit runs kept together. See docs/diller.md.
BOSLUKSUZ = frozenset({"ja", "zh", "yue", "th", "lo", "my", "km"})

# Right-to-left scripts: the output keeps the spoken (chronological) order; viewers render the glyphs right to left.
SAGDAN_SOLA = frozenset({"ar", "he", "fa", "ur", "ps", "yi"})

# torchaudio pipelines (weights from download.pytorch.org; en = LibriSpeech, others = VoxPopuli)
TORCHAUDIO = {
    "en": "WAV2VEC2_ASR_BASE_960H",
    "fr": "VOXPOPULI_ASR_BASE_10K_FR",
    "de": "VOXPOPULI_ASR_BASE_10K_DE",
    "es": "VOXPOPULI_ASR_BASE_10K_ES",
    "it": "VOXPOPULI_ASR_BASE_10K_IT",
}

# Hugging Face wav2vec2 CTC checkpoints (same choices as WhisperX 3.8.6)
HF = {
    "tr": "mpoyraz/wav2vec2-xls-r-300m-cv7-turkish",
    "ja": "jonatasgrosman/wav2vec2-large-xlsr-53-japanese",
    "zh": "jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn",
    "nl": "jonatasgrosman/wav2vec2-large-xlsr-53-dutch",
    "uk": "Yehor/wav2vec2-xls-r-300m-uk-with-small-lm",
    "pt": "jonatasgrosman/wav2vec2-large-xlsr-53-portuguese",
    "ar": "jonatasgrosman/wav2vec2-large-xlsr-53-arabic",
    "cs": "comodoro/wav2vec2-xls-r-300m-cs-250",
    "ru": "jonatasgrosman/wav2vec2-large-xlsr-53-russian",
    "pl": "jonatasgrosman/wav2vec2-large-xlsr-53-polish",
    "hu": "jonatasgrosman/wav2vec2-large-xlsr-53-hungarian",
    "fi": "jonatasgrosman/wav2vec2-large-xlsr-53-finnish",
    "fa": "jonatasgrosman/wav2vec2-large-xlsr-53-persian",
    "el": "jonatasgrosman/wav2vec2-large-xlsr-53-greek",
    "da": "saattrupdan/wav2vec2-xls-r-300m-ftspeech",
    "he": "imvladikon/wav2vec2-xls-r-300m-hebrew",
    "vi": "nguyenvulebinh/wav2vec2-base-vi-vlsp2020",
    "ko": "kresnik/wav2vec2-large-xlsr-korean",
    "ur": "kingabzpro/wav2vec2-large-xls-r-300m-Urdu",
    "te": "anuragshas/wav2vec2-large-xlsr-53-telugu",
    "hi": "theainerd/Wav2Vec2-large-xlsr-hindi",
    "ca": "softcatala/wav2vec2-large-xlsr-catala",
    "ml": "gvs/wav2vec2-large-xlsr-malayalam",
    "no": "NbAiLab/nb-wav2vec2-1b-bokmaal-v2",
    "nn": "NbAiLab/nb-wav2vec2-1b-nynorsk",
    "sk": "comodoro/wav2vec2-xls-r-300m-sk-cv8",
    "sl": "anton-l/wav2vec2-large-xlsr-53-slovenian",
    "hr": "classla/wav2vec2-xls-r-parlaspeech-hr",
    "ro": "gigant/romanian-wav2vec2",
    "eu": "stefan-it/wav2vec2-large-xlsr-53-basque",
    "gl": "ifrz/wav2vec2-large-xlsr-galician",
    "ka": "xsway/wav2vec2-large-xlsr-georgian",
    "lv": "jimregan/wav2vec2-large-xlsr-latvian-cv",
    "tl": "Khalsuu/filipino-wav2vec2-l-xls-r-300m-official",
    "sv": "KBLab/wav2vec2-large-voxrex-swedish",
    "id": "cahya/wav2vec2-large-xlsr-indonesian",
}

# Pinned revisions (Hugging Face commit) for the languages we ran. Unpinned languages resolve `main` and are experimental.
SABIT_REVIZYON = {
    "tr": "708639f50559d7970f462e13ec64d3f059ca89f6",
    "ja": "cf031e020336460d15a417eba710bbc5bb43be9a",
}

# Languages run end to end on our machine (GTX 1050 Ti 4 GB, WSL2). Everything else: EXPERIMENTAL.
SINANMIS = frozenset({"tr", "en", "ja"})

# Lower-casing that keeps Turkish dotted/dotless i correct (`I` -> `ı`, `İ` -> `i`).
TURKCE_KUCUK = str.maketrans({"I": "ı", "İ": "i"})


def dil_kodu(value: str) -> str:
    return str(value or "").strip().lower().split("-", 1)[0].split("_", 1)[0]


HF_KIMLIK = re.compile(r"^[A-Za-z0-9][\w.-]*/[\w.-]+$")


def hizalama_modeli(dil: str, ozel: str | None = None, revizyon: str | None = None) -> tuple[str, str, str | None]:
    """-> (kaynak, model_adi, revizyon). kaynak: 'torchaudio' | 'hf'. Raises for languages without a model."""
    if ozel:
        if not HF_KIMLIK.match(ozel):
            raise ValueError(f"--hizalama-modeli HF kimliği olmalı (kullanici/model): {ozel!r}")
        if revizyon is not None and not re.fullmatch(r"[\w.-]+", revizyon):
            raise ValueError(f"--hizalama-revizyon geçersiz: {revizyon!r}")
        return "hf", ozel, revizyon
    dil = dil_kodu(dil)
    if dil in TORCHAUDIO:
        return "torchaudio", TORCHAUDIO[dil], None
    if dil in HF:
        return "hf", HF[dil], SABIT_REVIZYON.get(dil)
    raise KeyError(dil)


def kucult(metin: str, dil: str) -> str:
    if dil_kodu(dil) in {"tr", "az"}:
        return metin.translate(TURKCE_KUCUK).lower()
    return metin.lower()


def bosluksuz_mu(dil: str) -> bool:
    return dil_kodu(dil) in BOSLUKSUZ


def ayirici_karakter_mi(ch: str) -> bool:
    """CJK ideographs, kana, Thai/Lao/Myanmar/Khmer: one character = one unit."""
    v = ord(ch)
    return (
        0x0E00 <= v <= 0x0EFF  # Thai, Lao
        or 0x1000 <= v <= 0x109F  # Myanmar
        or 0x1780 <= v <= 0x17FF  # Khmer
        or 0x3040 <= v <= 0x30FF  # hiragana, katakana
        or 0x3400 <= v <= 0x9FFF  # CJK ideographs
        or 0xF900 <= v <= 0xFAFF
        or 0x20000 <= v <= 0x323AF
    )


def birimlere_ayir(kelime: str) -> list[str]:
    """Split one ASR token group into alignment units: each CJK/Thai character alone, other runs kept together."""
    birimler: list[str] = []
    latin = ""
    for ch in kelime:
        if ayirici_karakter_mi(ch):
            if latin.strip():
                birimler.append(latin)
            latin = ""
            birimler.append(ch)
        else:
            latin += ch
    if latin.strip():
        birimler.append(latin)
    return birimler or [kelime]
