"""WER normaliser rules (tests/wer_olc.py docstring): each rule has one test, and real errors still count."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from wer_olc import normalize, sayi_yazi, wer  # noqa: E402


def test_sayi_yazi():
    assert sayi_yazi(40000) == ["kırk", "bin"]
    assert sayi_yazi(1000) == ["bin"]
    assert sayi_yazi(1996) == ["bin", "dokuz", "yüz", "doksan", "altı"]
    assert sayi_yazi(2_100_017) == ["iki", "milyon", "yüz", "bin", "on", "yedi"]
    assert sayi_yazi(0) == ["sıfır"]


def test_sayi_ekli_ve_ondalik():
    assert normalize("40.000'in biraz altında") == ["kırk", "binin", "biraz", "altında"]
    assert normalize("3,5 kilo") == ["üç", "virgül", "beş", "kilo"]


def test_sapka_kesme_ile():
    assert normalize("Hâlâ") == normalize("hala")
    assert normalize("Okulu'ndan") == normalize("okulundan")
    assert normalize("yöntemi ile") == normalize("yöntemiyle")
    assert normalize("kalem ile") == ["kalemle"]
    assert normalize("araba ile") == ["arabayla"]


def test_gercek_hata_sayilir_ve_ham_degismez():
    assert wer("Meşhed'deki bir pisti", "Meşet'teki bir pisti", "tr")[1] == 1
    assert wer("çevrimiçi", "çevrim içi", "tr")[1] == 2
    assert normalize("Hâlâ 40.000'in", kip="ham") == ["hâlâ", "40", "000'in"]


def test_baska_dil_yalniz_ham_kurallar():
    assert normalize("Hello, World 40", dil="en") == ["hello", "world", "40"]
