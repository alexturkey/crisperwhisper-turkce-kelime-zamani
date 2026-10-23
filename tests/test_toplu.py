"""Toplu kip (batch) birim testleri, GPU'suz: modeller sahte, yalnız akış sınanır / batch mode, no GPU (fake models)."""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from transkript import __main__ as cli  # noqa: E402
from transkript import akis, hizalama_isci, motor_isci  # noqa: E402


def test_motor_isci_modeli_bir_kez_yukler_hata_digerini_durdurmaz(monkeypatch):
    yukleme = []

    def sahte_yukle(istek, sureler):
        yukleme.append(1)
        sureler["model_yukleme_sn"] = 1.0
        return "MODEL", {"cihaz": "cpu"}

    def sahte_coz(model, is_, mnt):
        assert model == "MODEL"
        if is_["ses"] == "bozuk.wav":
            raise RuntimeError("okunamadı")
        return {"metin": is_["ses"], "dil": is_["dil"], "dil_adaylari": [], "kelimeler": [], "ses_sn": 1.0, "sureler": {"cozumleme_sn": 0.1}}

    monkeypatch.setattr(motor_isci, "_model_yukle", sahte_yukle)
    monkeypatch.setattr(motor_isci, "_coz", sahte_coz)
    y = motor_isci.calistir({"model": "m", "isler": [{"ses": "a.wav", "dil": "tr"}, {"ses": "bozuk.wav", "dil": "tr"}, {"ses": "c.wav", "dil": "en"}]})
    assert len(yukleme) == 1
    assert [r["durum"] for r in y["sonuclar"]] == ["ok", "hata", "ok"]
    assert y["sonuclar"][2]["dil"] == "en" and y["sureler"]["model_yukleme_sn"] == 1.0
    tekil = motor_isci.calistir({"model": "m", "ses": "a.wav", "dil": "tr"})  # single-file response keeps its old shape
    assert tekil["metin"] == "a.wav" and "sonuclar" not in tekil and tekil["sureler"]["model_yukleme_sn"] == 1.0


def test_hizalama_isci_dil_basina_bir_model(monkeypatch):
    yuklenen = []

    class SahteModel:
        def __init__(self, dil, cihaz, ozel, rev):
            yuklenen.append(dil)
            self.ad, self.cihaz = f"m_{dil}", cihaz

    monkeypatch.setattr(hizalama_isci, "HizalamaModeli", SahteModel)
    monkeypatch.setattr(hizalama_isci, "_hizala", lambda m, is_, dil: {"kelimeler": [{"kelime": is_["ses"]}], "profil": {"model": m.ad, "sureler": {}}})
    isler = [{"ses": s, "dil": d, "segmentler": []} for s, d in [("t1", "tr"), ("e1", "en"), ("t2", "tr"), ("j1", "ja"), ("e2", "en")]]
    y = hizalama_isci.calistir({"cihaz": "cpu", "isler": isler})
    assert sorted(yuklenen) == ["en", "ja", "tr"]  # each language model loaded once
    assert [r["kelimeler"][0]["kelime"] for r in y["sonuclar"]] == ["t1", "e1", "t2", "j1", "e2"]  # input order kept
    assert [r["profil"]["model"] for r in y["sonuclar"]] == ["m_tr", "m_en", "m_tr", "m_ja", "m_en"]


def test_calistir_toplu_akis(monkeypatch, tmp_path):
    istekler = {}

    def sahte_isci(modul, istek, klasor, ad, ortam, zaman_asimi):
        istekler[ad] = istek
        if ad == "asr":
            return {"durum": "ok", "kimlik": {"cihaz": "cpu"}, "sureler": {"model_yukleme_sn": 2.0}, "sonuclar": [
                {"durum": "ok", "metin": "Merhaba dünya.", "dil": "tr", "dil_adaylari": [], "sureler": {"cozumleme_sn": 0.2},
                 "kelimeler": [{"kelime": "Merhaba", "start": 0.1, "end": 0.5}, {"kelime": "dünya.", "start": 0.6, "end": 0.9}]},
                {"durum": "hata", "hata": "RuntimeError: x"}]}, 5.0, 900
        return {"durum": "ok", "sureler": {"model_yukleme_sn": 1.0}, "sonuclar": [
            {"durum": "ok", "kelimeler": [{"kelime": "Merhaba", "start": 0.1, "end": 0.5, "skor": 0.9, "yontem": "ctc"},
                                          {"kelime": "dünya.", "start": 0.6, "end": 0.9, "skor": 0.9, "yontem": "ctc"}],
             "profil": {"sureler": {"hizalama_sn": 0.3}}}]}, 3.0, 800

    monkeypatch.setattr(akis, "_isci", sahte_isci)
    monkeypatch.setattr(akis.ayarlar, "model_dogrula", lambda p: {"kaynak_commit": "abc"})
    monkeypatch.setattr(akis.ses, "yukle", lambda k: np.zeros(16000, dtype=np.float32))
    isler = [(Path("a.mp3"), tmp_path / "a", "tr"), (Path("b.mp3"), tmp_path / "b", "en")]
    ayar = {"model": str(tmp_path), "hf_home": str(tmp_path)}
    sonuclar = akis.calistir_toplu(isler, tmp_path / "_toplu", ayar, {"srt"}, None, None, ilerleme=lambda *a, **k: None)
    assert len(istekler["asr"]["isler"]) == 2 and len(istekler["hizalama"]["isler"]) == 1
    assert istekler["hizalama"]["isler"][0]["dil"] == "tr" and istekler["hizalama"]["isler"][0]["segmentler"]
    assert sonuclar[0]["durum"] == "ok" and sonuclar[0]["metin"] == "Merhaba dünya." and sonuclar[0]["toplu"]["asr_surec_sn"] == 5.0
    assert sonuclar[1]["durum"] == "hata" and sonuclar[1]["hata"].startswith("asr:")
    assert (tmp_path / "a" / "kelimeler.json").is_file() and (tmp_path / "a" / "transkript.srt").is_file()


def test_cli_liste_ve_ad_cakismasi(monkeypatch, tmp_path):
    for ad in ("x.mp3", "y.wav"):
        (tmp_path / ad).write_bytes(b"0")
    (tmp_path / "alt").mkdir()
    (tmp_path / "alt" / "x.mp3").write_bytes(b"0")
    liste = tmp_path / "isler.tsv"
    liste.write_text(f"# yorum\n{tmp_path / 'x.mp3'}\tja\n{tmp_path / 'alt' / 'x.mp3'}\n\n{tmp_path / 'y.wav'}\tauto\n", encoding="utf-8")
    yakalanan = {}

    def sahte_toplu(hedefler, calisma, ayar, bicimler, *a, **k):
        yakalanan["hedefler"] = hedefler
        calisma.mkdir(parents=True, exist_ok=True)
        t = {"toplam_sn": 1.0}
        return [{"durum": "ok", "sinanmis_dil": True, "dil": d if d != "auto" else "tr", "ses_sn": 1.0, "kelimeler": [], "toplu": t,
                 "sureler": {"asr_cozumleme_sn": 0.1, "hizalama_sn": 0.1}} for _, _, d in hedefler]

    monkeypatch.setattr(cli.ayarlar, "yukle", lambda kok: {})
    monkeypatch.setattr(akis, "calistir_toplu", sahte_toplu)
    kod = cli.main(["--liste", str(liste), "--dil", "en", "--cikti", str(tmp_path / "out")])
    assert kod == 0
    h = yakalanan["hedefler"]
    assert [d for _, _, d in h] == ["ja", "en", "auto"]
    assert [k.name for _, k, _ in h] == ["x", "x_2", "y"]  # same stem twice -> distinct folders
    assert json.loads((tmp_path / "out" / "_toplu" / "ozet.json").read_text(encoding="utf-8"))["toplu"]["toplam_sn"] == 1.0
