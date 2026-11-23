"""Kurulum düzeni testleri (GPU yok, internet yok) / install layout tests (no GPU, no internet).

scripts/kur.sh içindeki `indir` işlevi yerel sahte sunucuya karşı koşar: yarım .part kaldığı yerden sürer (Range), doğru hedef ve
tam .part yeniden inmez, Range'i reddeden sunucuda baştan iner, sha256 tutmazsa dosya hedefe konmaz. Önbellek değişkenleri yalnız
boşsa köke yönlenir (kullanıcının değeri ezilmez). Betikler kalıcı sistem değişikliği yazmaz.
Needs bash and the download tool on PATH (Linux, WSL, Git Bash); skipped otherwise.   python -m pytest tests -q
"""
import hashlib
import http.server
import re
import shutil
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
KUR_SH = REPO / "scripts" / "kur.sh"
BASH = shutil.which("bash")
CURL = shutil.which("curl")

VERI = bytes((i * 7 + 3) % 251 for i in range(600_000))
SHA = hashlib.sha256(VERI).hexdigest()

# Kalıcı sistem değişikliği desenleri PARÇALI yazılır: bu dosya kendi taramasına takılmasın.
YASAK = (r"\bset" + "x" + r"\b", r"\breg\s+" + "add" + r"\b", "HK" + "CU:|HK" + "LM:", r"\$PRO" + "FILE" + r"\b",
         "Set-Execution" + r"Policy(?![^\n]*-Scope\s+Process)", "SetEnviron" + r"mentVariable\s*\([^)]*,\s*['\"]?(User|Machine)\b",
         r"pip3?\s+install[^\n]*--user")


class Sunucu(http.server.BaseHTTPRequestHandler):
    istekler = []
    range_kabul = True

    def log_message(self, *a):
        pass

    def do_GET(self):
        r = self.headers.get("Range")
        Sunucu.istekler.append(r)
        if r and Sunucu.range_kabul:
            bas = int(re.match(r"bytes=(\d+)-", r).group(1))
            if bas >= len(VERI):
                self.send_response(416)
                self.send_header("Content-Range", "bytes */%d" % len(VERI))
                self.end_headers()
                return
            parca = VERI[bas:]
            self.send_response(206)
            self.send_header("Content-Range", "bytes %d-%d/%d" % (bas, len(VERI) - 1, len(VERI)))
        else:
            parca = VERI
            self.send_response(200)
        self.send_header("Content-Length", str(len(parca)))
        self.end_headers()
        self.wfile.write(parca)


def islev(ad):
    """kur.sh'tan bir bash işlevinin metni (satır başında `ad() {` ... satır başında `}`)."""
    m = re.search(r"^%s\(\) \{.*?^\}\n" % re.escape(ad), KUR_SH.read_text(encoding="utf-8"), re.S | re.M)
    assert m, ad
    return m.group(0)


def posix(p):
    """Windows yolunu Git Bash'in anladığı biçime çevir (Linux'ta değişmez)."""
    s = str(p).replace("\\", "/")
    return re.sub(r"^([A-Za-z]):", lambda m: "/" + m.group(1).lower(), s)


@unittest.skipUnless(BASH and CURL, "bash and the download tool needed")
class IndirDevam(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Sunucu)
        cls.url = "http://127.0.0.1:%d/dosya.bin" % cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def setUp(self):
        Sunucu.istekler = []
        Sunucu.range_kabul = True
        self._t = tempfile.TemporaryDirectory()
        self.addCleanup(self._t.cleanup)
        self.t = Path(self._t.name)
        self.hedef = self.t / "dosya.bin"

    def kos(self, sha=SHA):
        # Yerel sahte sunucu http konuşur: yalnız bu testte "=https" kısıtı gevşetilir; betikteki metin değişmez.
        kod = "set -u\n" + islev("sha256") + islev("indir").replace('"=https"', '"=http,https"') + \
            '( indir "%s" "%s" "%s" ) >/dev/null 2>&1 && echo SONUC:TAMAM || echo SONUC:HATA\n' % (self.url, posix(self.hedef), sha)
        r = subprocess.run([BASH, "-c", kod], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        son = [s.strip() for s in r.stdout.splitlines() if s.startswith("SONUC:")]
        self.assertTrue(son, r.stdout + r.stderr)
        return son[-1]

    def test_sifirdan_iner(self):
        self.assertEqual(self.kos(), "SONUC:TAMAM")
        self.assertEqual(hashlib.sha256(self.hedef.read_bytes()).hexdigest(), SHA)
        self.assertFalse((self.t / "dosya.bin.part").exists())

    def test_yarim_part_kaldigi_yerden_surer(self):
        (self.t / "dosya.bin.part").write_bytes(VERI[:250_000])
        self.assertEqual(self.kos(), "SONUC:TAMAM")
        self.assertEqual(hashlib.sha256(self.hedef.read_bytes()).hexdigest(), SHA)
        self.assertEqual(Sunucu.istekler, ["bytes=250000-"], "yalnız kalan kısım istenmeli, baştan değil")

    def test_dogru_hedef_yeniden_inmez(self):
        self.hedef.write_bytes(VERI)
        self.assertEqual(self.kos(), "SONUC:TAMAM")
        self.assertEqual(Sunucu.istekler, [], "doğru dosya varken ağa çıkılmamalı")

    def test_tam_part_yeniden_inmez(self):
        (self.t / "dosya.bin.part").write_bytes(VERI)
        self.assertEqual(self.kos(), "SONUC:TAMAM")
        self.assertEqual(Sunucu.istekler, [], "tam ve doğru .part yeniden indirilmemeli")
        self.assertTrue(self.hedef.exists())

    def test_range_kabul_etmeyen_sunucuda_bastan(self):
        Sunucu.range_kabul = False
        (self.t / "dosya.bin.part").write_bytes(VERI[:100_000])
        self.assertEqual(self.kos(), "SONUC:TAMAM")
        self.assertEqual(hashlib.sha256(self.hedef.read_bytes()).hexdigest(), SHA)

    def test_yanlis_sha_kabul_edilmez(self):
        self.assertEqual(self.kos(sha="0" * 64), "SONUC:HATA")
        self.assertFalse(self.hedef.exists(), "sha tutmayan dosya hedefe konmamalı")


@unittest.skipUnless(BASH, "bash needed")
class OnbellekDegiskenleri(unittest.TestCase):
    satir = next(s for s in KUR_SH.read_text(encoding="utf-8").splitlines() if s.startswith("export HF_HOME="))

    def kos(self, **env):
        kod = 'KOK=/kok/deneme\n' + self.satir + '\necho "$PIP_CACHE_DIR|$HF_HOME|$TORCH_HOME|$TMPDIR"\n'
        ortam = {"PATH": __import__("os").environ.get("PATH", ""), **env}
        r = subprocess.run([BASH, "-c", kod], capture_output=True, text=True, env=ortam, timeout=30)
        return r.stdout.strip().split("|")

    def test_bos_degisken_koke_yonlenir(self):
        pip, hf, torch, tmp = self.kos()
        self.assertEqual((pip, hf, torch, tmp), ("/kok/deneme/pip", "/kok/deneme/hf", "/kok/deneme/torch", "/kok/deneme/indirme"))

    def test_kullanicinin_degeri_ezilmez(self):
        pip, hf, torch, tmp = self.kos(PIP_CACHE_DIR="/benim/pip", HF_HOME="/benim/hf", TORCH_HOME="/benim/torch", TMPDIR="/benim/tmp")
        self.assertEqual((pip, hf, torch), ("/benim/pip", "/benim/hf", "/benim/torch"))
        self.assertEqual(tmp, "/kok/deneme/indirme", "TMPDIR her zaman köke gider")


class BetikKurallari(unittest.TestCase):
    def test_kalici_sistem_degisikligi_yok(self):
        for ad in ("kur.sh", "kur.ps1", "kur.cmd", "tani.sh", "on_kontrol.sh"):
            metin = (REPO / "scripts" / ad).read_text(encoding="utf-8-sig")
            for d in YASAK:
                self.assertIsNone(re.search(d, metin), "%s: %s" % (ad, d))

    def test_kur_sh_dosya_kokunun_disina_yazmaz_kuruda(self):
        metin = KUR_SH.read_text(encoding="utf-8")
        kuru = metin[metin.index('if [[ "$KURU" == 1 ]]'):metin.index('mkdir -p "$KOK"')]
        self.assertNotIn("mkdir", kuru)
        self.assertNotIn("curl", kuru.replace("sha256sum curl", ""))

    def test_venv_ve_ayar_yerinde(self):
        """Eski kullanıcı bozulmasın: .venv ve ayarlar.json depo klasöründe kalır (taşınmadı)."""
        metin = KUR_SH.read_text(encoding="utf-8")
        self.assertIn('VENV="$REPO/.venv"', metin)
        self.assertIn('"$REPO/ayarlar.json"', metin)


if __name__ == "__main__":
    unittest.main()
