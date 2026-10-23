"""GPU'suz birim testleri / unit tests without GPU:  python -m pytest tests -q"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from transkript import cikti  # noqa: E402
from transkript.akis import dogrula, segmentler_olustur  # noqa: E402
from transkript.diller import birimlere_ayir, bosluksuz_mu, dil_kodu, hizalama_modeli, kucult  # noqa: E402
from transkript.hizalama_isci import _ara_deger, _cakisma_duzelt, _esit_bol  # noqa: E402

KELIMELER = [
    {"kelime": "Merhaba", "start": 0.10, "end": 0.55, "skor": 0.9, "yontem": "ctc"},
    {"kelime": "dünya.", "start": 0.60, "end": 1.00, "skor": 0.8, "yontem": "ctc"},
    {"kelime": "Bugün", "start": 3.00, "end": 3.30, "skor": 0.7, "yontem": "ctc"},
    {"kelime": "hava", "start": 3.35, "end": 3.60, "skor": 0.7, "yontem": "ctc"},
    {"kelime": "güzel.", "start": 3.65, "end": 4.10, "skor": 0.7, "yontem": "ctc"},
]


def test_srt_vtt_bicimi():
    satirlar = cikti.cumleler(KELIMELER)
    assert [s["metin"] for s in satirlar] == ["Merhaba dünya.", "Bugün hava güzel."]
    srt = cikti.srt(satirlar)
    assert srt.startswith("1\n00:00:00,100 --> 00:00:01,000\nMerhaba dünya.\n")
    vtt = cikti.vtt(satirlar)
    assert vtt.startswith("WEBVTT\n\n00:00:00.100 --> 00:00:01.000\nMerhaba dünya.\n")


def test_bosluksuz_satir_birlestirme():
    k = [{"kelime": "今", "start": 0.0, "end": 0.2}, {"kelime": "日", "start": 0.2, "end": 0.4}, {"kelime": "は。", "start": 0.4, "end": 0.6}]
    assert cikti.cumleler(k, bosluksuz=True)[0]["metin"] == "今日は。"


def test_hepsini_yaz(tmp_path):
    sonuc = {"metin": "Merhaba dünya. Bugün hava güzel.", "kelimeler": KELIMELER}
    yollar = cikti.hepsini_yaz(tmp_path, sonuc, {"srt", "vtt"}, False)
    adlar = sorted(p.name for p in yollar)
    assert adlar == ["kelimeler.json", "kelimeler.srt", "kelimeler.vtt", "transkript.srt", "transkript.txt", "transkript.vtt"]
    assert json.loads((tmp_path / "kelimeler.json").read_text(encoding="utf-8"))["kelimeler"][1]["kelime"] == "dünya."
    assert not list(tmp_path.glob("*.part"))


def test_segmentler_ve_dogrulama():
    seg = segmentler_olustur(KELIMELER, 5.0, "tr")
    assert len(seg) == 2 and seg[0]["birimler"] == ["Merhaba", "dünya."] and seg[0]["start"] == 0.0
    assert seg[0]["end"] == 3.0 and seg[1]["end"] == 5.0  # a segment reaches the next one's start; the last one the audio end
    dogrula(KELIMELER, 5.0)


def test_bosluksuz_birimler():
    assert bosluksuz_mu("ja") and not bosluksuz_mu("tr")
    assert birimlere_ayir("今日はAI2つ") == ["今", "日", "は", "AI2", "つ"]
    assert birimlere_ayir("สวัสดี") == list("สวัสดี")
    seg = segmentler_olustur([{"kelime": "今日は。", "start": 0.0, "end": 0.8}], 1.0, "ja")
    assert seg[0]["birimler"] == ["今", "日", "は", "。"][:3] + ["。"] or seg[0]["birimler"][:3] == ["今", "日", "は"]


def test_dil_tablosu():
    assert hizalama_modeli("tr")[0:2] == ("hf", "mpoyraz/wav2vec2-xls-r-300m-cv7-turkish")
    assert hizalama_modeli("en")[0] == "torchaudio"
    assert hizalama_modeli("xx", "ozel/model")[1] == "ozel/model"
    try:
        hizalama_modeli("xx")
        assert False, "KeyError bekleniyordu"
    except KeyError:
        pass
    assert dil_kodu("TR-tr") == "tr"
    assert kucult("IŞIK İzmir", "tr") == "ışık izmir"
    assert kucult("IŞIK", "en") == "işik"


def test_ara_deger_ve_cakisma():
    sonuc = [{"kelime": "a", "start": 0.0, "end": 0.2}, {"kelime": "bbb", "start": None, "end": None}, {"kelime": "c", "start": None, "end": None}, {"kelime": "d", "start": 1.0, "end": 1.2}]
    _ara_deger(sonuc, 0.0, 2.0)
    assert sonuc[1]["start"] == 0.2 and abs(sonuc[2]["end"] - 1.0) < 1e-9 and sonuc[1]["end"] > sonuc[1]["start"]
    esit = _esit_bol([{"kelime": "ab"}, {"kelime": "cd"}], 1.0, 1.0, "esit_bolme")
    assert esit[0]["end"] == 1.5 and esit[1]["yontem"] == "esit_bolme"
    k = [{"kelime": "x", "start": 0.0, "end": 0.6}, {"kelime": "y", "start": 0.5, "end": 0.9}]
    assert _cakisma_duzelt(k) == 1 and k[0]["end"] == k[1]["start"] == 0.55


def test_wav_yaz_part_uzantisi(tmp_path):
    """Regression: writing to <name>.wav.part must not fail on format detection (2026-10-23)."""
    import numpy as np
    from transkript.ses import wav_yaz

    hedef = tmp_path / "ses_16k_mono.wav"
    sure = wav_yaz(hedef, np.zeros(16000, dtype=np.float32))
    assert hedef.is_file() and abs(sure - 1.0) < 1e-6 and not (tmp_path / "ses_16k_mono.wav.part").exists()


def test_ct2_config_yaz(tmp_path):
    """CT2 reads config.json with lang_ids/alignment_heads/suppress_ids; derived from generation_config + added_tokens."""
    import json
    from transkript.donustur import ct2_config_yaz

    (tmp_path / "generation_config.json").write_text(json.dumps({
        "alignment_heads": [[2, 11], [1, 1]], "suppress_tokens": [-1, 1, 2], "begin_suppress_tokens": [220]}), encoding="utf-8")
    added = {f"<|{chr(97 + i // 26)}{chr(97 + i % 26)}|>": 50259 + i for i in range(99)}
    added["<|yue|>"] = 50358
    added["<|startoftranscript|>"] = 50258
    (tmp_path / "added_tokens.json").write_text(json.dumps(added), encoding="utf-8")
    (tmp_path / "config.json").write_text(json.dumps({"d_model": 1280}), encoding="utf-8")
    cfg = ct2_config_yaz(tmp_path)
    assert cfg["lang_ids"][0] == 50259 and cfg["lang_ids"][-1] == 50358 and len(cfg["lang_ids"]) == 100
    assert cfg["suppress_ids"] == [1, 2] and cfg["suppress_ids_begin"] == [220] and cfg["alignment_heads"] == [[2, 11], [1, 1]]
    assert json.loads((tmp_path / "config.json").read_text(encoding="utf-8")) == cfg
    assert (tmp_path / "config_hf.json").is_file()
