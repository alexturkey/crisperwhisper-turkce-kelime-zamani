# crisperwhisper-turkce-kelime-zamani

**4 GB ekran kartında verbatim konuşma-metin ve kelime zamanı.** CrisperWhisper 2.0 Turbo (CTranslate2, CUDA int8)
söyleneni *olduğu gibi* yazar (dolgu sesleri, yarım kelimeler, tekrarlar korunur); sonra wav2vec2 CTC zorlamalı
hizalama her kelimeye başlangıç ve bitiş saniyesi verir. Çıktı: metin, kelime JSON'u, SRT ve VTT. Türkçe için kurulup
ölçüldü; modellerin bildiği her dilde çalışır (`docs/diller.md`). Linux ya da WSL2 ile Windows; tek komutla kurulum.

[English README](README.md) · [Diller ve kelime ayırma](docs/diller.md) · [Ölçümler](docs/olcumler.md) · [Yapay zekâ ajanı için kurulum](AGENTS.md) · [Sorumlu kullanım](ETHICS.md)

> **Model lisansı:** CrisperWhisper 2.0 ağırlıkları **ticari olmayan** kullanım içindir (nyra health Non-Commercial
> Research License). Bu deponun kodu Apache-2.0'dır ama aracı ücretli bir üründe çalıştırmak Nyra Health'ten ticari
> lisans ister. Ağırlıklar depoda yok; kurulum betiği sabit bir commit'ten indirir. Bkz. [NOTICE](NOTICE).

## Ne alırsınız

```
cikti/kayit_20261023_0210/
  transkript.txt      verbatim metin
  kelimeler.json      her kelime: start, end, skor, nasıl zamanlandı; dil; süreler; iki modelin kimliği
  transkript.srt/vtt  altyazı satırları (cümle ya da ~7 sn)
  kelimeler.srt/vtt   kelime başına bir satır (karaoke tarzı)
  ses_16k_mono.wav    modellerin duyduğu ses
```

`kelimeler.json` kelime girdisi: `{"kelime": "dünya.", "start": 0.62, "end": 1.01, "skor": 0.93, "yontem": "ctc"}`.
`yontem`: `ctc` gerçek hizalama; `ara_deger` hizalama modelinin sözlüğünde kelimenin hiç harfi yoksa komşular arasında
ara değer; `esit_bolme` segment hiç hizalanamadıysa.

## Kurulum (Linux ya da WSL2 ile Windows 10/11)

Gereken: NVIDIA ekran kartı ≥ 4 GB VRAM, sürücü ≥ 570 (CUDA 12.8), Python 3.10-3.12, `curl`, ~7 GB disk
(torch 3 GB, model 1,6 GB indirme + 1,6 GB dönüşüm, dil başına 0,4-1,3 GB hizalama modeli). sudo yok, sistem CUDA
kurulumu yok, PATH değişmez; her şey seçtiğiniz kökün altına iner.

**Linux**
```bash
git clone https://github.com/alexturkey/crisperwhisper-turkce-kelime-zamani.git
cd crisperwhisper-turkce-kelime-zamani
bash scripts/kur.sh --kok ~/stt            # ~15 dk, ~6 GB indirme; işaretler PYTHON_OK MODEL_OK DONUSUM_OK HIZALAMA_OK AYAR_OK KONTROL_OK KURULUM_OK
.venv/bin/python -m transkript ornek/ornek.mp3 --dil tr
```

**Windows** (CTranslate2 çatalının yalnız Linux wheel'i var; motor WSL2 içinde çalışır, sarmalayıcılar bunu gizler)
```powershell
wsl --install -d Ubuntu          # bir kez, yönetici; yeniden başlatın; "Ubuntu"yu bir kez açıp kullanıcı oluşturun
git clone https://github.com/alexturkey/crisperwhisper-turkce-kelime-zamani.git
cd crisperwhisper-turkce-kelime-zamani
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\kur.ps1 -Kok E:\stt
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\stt.ps1 -Ses ornek\ornek.mp3 -Dil tr
```
`-ExecutionPolicy Bypass` yalnız o sürece etki eder; her kurulum betiği gibi `scripts\kur.ps1` ve `scripts/kur.sh`'ı
çalıştırmadan önce okuyun. Hata sonrası yeniden çalıştırın: doğrulanmış indirmeler atlanır.

`--diller "tr en ja"` (kur.sh) / `-Diller "tr en ja"` (kur.ps1) hangi dillerin hizalama modelinin önceden ineceğini
seçer (varsayılan `tr en`); tablodaki öteki diller ilk kullanımda iner.

## Kullanım

```bash
.venv/bin/python -m transkript kayit.mp3                       # Türkçe (varsayılan), çıktı cikti/ altına
.venv/bin/python -m transkript kayit.wav --dil en --cikti out  # İngilizce
.venv/bin/python -m transkript a.mp3 b.wav c.mp3 --cikti out   # toplu kip: modeller bir kez yüklenir, her dosya out/<ad>/
.venv/bin/python -m transkript --liste isler.tsv --cikti out   # listeden toplu: her satır <dosya>[<TAB><dil>]
.venv/bin/python -m transkript kayit.m4a --dil auto            # ilk 30 sn'den dil tespiti (m4a/mp4 için ffmpeg gerekir)
.venv/bin/python -m transkript --diller                        # hizalama modeli olan diller (sınanmış / deneysel)
.venv/bin/python -m transkript --kontrol                       # ortam kontrolü -> KONTROL_OK
```
Girdi: libsndfile'ın çözdüğü her şey (wav, flac, ogg, mp3); video ve öteki kaplar için PATH'te `ffmpeg` gerekir.
Seçenekler: `--bicim json,srt,vtt`, `--hizalama-modeli <HF wav2vec2 CTC kimliği>` (başka dil ya da kendi modeliniz),
`--hizalama-cihazi cpu` (GPU belleği yetmezse hizalama CPU'da; yavaş), `--zaman-asimi`.

## Nasıl çalışır

1. Ses → 16 kHz mono WAV (soundfile + soxr; ffmpeg yalnız video kapları için).
2. **ASR işçisi** (ayrı süreç): `crisperwhisper` CT2 arka ucu, `compute_type=int8`, verbatim kip, "continuation" uzun
   ses parçalama, hallucination onarımı ve erken-bitiş kurtarma, kendi kelime zamanları açık. Süreç biter, GPU boşalır.
3. **Hizalama işçisi** (ayrı süreç): ASR kelimeleri ≤ 18 sn'lik segmentlere gruplanır (cümle sonu, > 2,5 sn boşluk);
   her segmentin harfleri dilin wav2vec2 CTC modeliyle zorlamalı hizalanır (`torchaudio.functional.forced_align` +
   `merge_tokens`); kelimenin süresi ilk tanınan harfinden son harfine uzanır, sessizlik kelimenin içine girmez.
   CJK/Tay metni karakter karakter zamanlanır (`docs/diller.md`).
4. Denetim (kronolojik, ses içinde, çakışmasız) ve çıktılar. CrisperWhisper'ın kendi zamanları karşılaştırma için
   `kelimeler.json` → `asr_kelimeleri` altında kalır.

Tek yerine iki süreç: 4 GB kart iki modeli aynı anda tutmaz. CT2 turbo int8 tepe ≈ 1371 MB, Türkçe hizalama
modeli tepe ≤ 1653 MB (nvidia-smi, GTX 1050 Ti).

## Diller ve kelime ayırma

`--dil xx` ile Whisper'ın tanıdığı her dil (`--dil auto` ilk 30 sn'den tespit eder). "Kelime"nin ne olduğu yazıya göre
değişir (tam tablo ve gerekçe: [docs/diller.md](docs/diller.md)):

| Yazı | `kelimeler.json`'daki birim | Hizalama modeli | Durum |
|---|---|---|---|
| Boşlukla ayrılan (tr, en, de, fr, es, ru, ar, he, ...) | boşluk arası parça, noktalama kelimeye yapışık | dile göre wav2vec2 CTC (`ayarlar/manifest.json` tablosu) | **tr, en sınandı**; diğerleri deneysel (tablo WhisperX'ten, burada koşulmadı) |
| Japonca, Çince, Tayca, Laoca, Birmanca, Khmerce | **tek karakter** (kanji/kana/hanzi; içindeki Latin harf ve rakam bütün kalır) | tabloda ja/zh wav2vec2 CTC var; th/lo/my/km/yue için yok: `--hizalama-modeli <HF kimliği>` verin, yoksa açık mesajla durur | **ja sınandı**; zh deneysel; kalanı kendi modelinizi ister |
| Korece | eojeol (boşlukla ayrılan öbek) | ko wav2vec2 | deneysel |
| Arapça, İbranice, Farsça, Urduca (sağdan sola) | kelime, **mantıksal (söyleniş) sırada**, yeniden sıralama yok | ar/he/fa/ur wav2vec2 | deneysel |

Paketli biçimbirim ayırıcı yok: Japonca kelime (MeCab/fugashi), Çince kelime (jieba) ya da Tayca kelime (pythainlp)
gerekiyorsa ayırıcıyı `metin` üstünde çalıştırıp karakter zamanlarını yeniden gruplayın (ilk karakterin başı → son
karakterin sonu); `docs/diller.md`'de 10 satırlık tarif var. Her kelimede `yontem` alanı: `ctc` (hizalandı), `ara_deger`
(karakter modelin sözlüğünde yoksa komşulardan ara değer), `esit_bolme` (segmentin tamamı hizalanamadı; kelimeler segment
süresini eşit paylaşır).

## Hız ve doğruluk (burada ölçüldü, alıntı değil)

GTX 1050 Ti 4 GB, WSL2 Ubuntu 24.04, i7-7700HQ. Yöntem ve tam tablo: [docs/olcumler.md](docs/olcumler.md).

| set | ses | WER normalize (ana) | WER ham | not | model işi (ASR + hizalama) |
|---|---|---|---|---|---|
| Türkçe, 8 dosya (temiz yapay TTS) | 192 sn | **%0 (0/363)** | %1,4 (5/363) | 5 ham hatanın hepsi şapka (`hâlâ` → `hala`) | 21,1 sn + 6,9 sn |
| **Türkçe, FLEURS tr_tr test, 10 gerçek kayıt** | 122 sn | **%6,2 (11/176)** | %10,1 (18/178) | 7 ham hata yazım geleneği (aşağıda) | 17,2 sn + 3,6 sn |
| İngilizce, 2 dosya (1 TTS, 1 gerçek oda kaydı) | 11,3 sn | %0 (0/34) | %0 (0/34) | | 7,2 sn + 7,8 sn |
| Japonca, 1 dosya (TTS) | 7,5 sn | CER %9,4 (3/32 karakter) | aynı | `今日` → `きょう` (aynı okunuş) | 3,2 sn + 0,5 sn |

Toplu kip, 12 öğe tek koşuda: 602 sn; bunun yaklaşık 480 sn'si torch'un açılması ve modellerin WSL2'ye bağlı Windows
diskinden yüklenmesi. Tek dosyalık koşu bu yüklemeyi her seferinde öder (burada dosya başı 459-727 sn); birden çok
dosya ya da `--liste` verin. VRAM tepe: 1371 MB (ASR) / en çok 2411 MB (hizalama).

**"Normalize" nasıl hesaplanır** (`tests/wer_olc.py`; gerçek metne ve bizim çıktıya aynen uygulanır; iki sayı da her
zaman yazılır):

1. küçük harf (Türkçe `I`/`İ` doğru), noktalama ve `[olay]` etiketleri silinir (yalnız bu adım = ham sayı);
2. şapka kalkar: `â/î/û` → `a/i/u` (`hâlâ` = `hala`);
3. sayılar Türkçe yazıya çevrilir, ek korunur (`40.000'in` = `kırk binin`);
4. kesme işareti kalkar, ek birleşir (`Okulu'ndan` = `okulundan`);
5. `ile` önceki kelimeye bitişir (`yöntemi ile` = `yöntemiyle`).

Başka hiçbir şey affedilmez: özel ad, yanlış kelime ve birleşik yazım (`çevrimiçi` → `çevrim içi`) hata sayılır.

| FLEURS gerçek metin | bizim çıktı | sayıldı mı? |
|---|---|---|
| … ve **40.000'in** biraz altında … | … ve **kırk binin** biraz altında … | hayır: aynı kelimeler (kural 3) |
| … yorumlama **yöntemi ile** … | … yorumlama **yöntemiyle** … | hayır: aynı kelime (kural 5) |
| … **Eyalet Başkenti'ne** … | … **eyalet başkentine** … | hayır: büyük harf ve kesme (kural 1, 4) |
| … uçağı **Meşhed'deki** bir pisti … | … uçağı **Meşet'teki** bir pisti … | **evet**: yanlış özel ad |
| … radyoaktif **sezyum** ve **iyodin** tespit **edildi** | … radyoaktif **sezium** ve **iodin** tespit **edilir** | **evet**: 3 hata |
| … **Şehir Upolu** adasındadır … | … **Şiir, Upol** Adası'ndadır … | **evet**: 2 hata |

Yapay satırlar temiz TTS sesleridir: hattın uçtan uca çalıştığını gösterir, gerçek ya da gürültülü kayıttaki başarıyı
göstermez. FLEURS (Google, tr_tr test bölümü, ilk 10 kayıt, CC BY 4.0) gerçek okuma kaydıdır; 10 kayıt bir duman
testidir, benchmark değildir. Kelime zamanı doğruluğu elle işaretli veriyle **ölçülmedi**; yöntemin davranışı
`docs/diller.md`'de. Nyra, CrisperWhisper 2.0 sayılarını kendi benchmark'ında verir
(`github.com/nyrahealth/CrisperWhisper`); o sayılar onların, bizim değil.

## Sınırlar

- Ticari olmayan model lisansı (yukarıda). Verbatim çıktı kişisel veridir: [ETHICS.md](ETHICS.md).
- Aynı anda tek GPU işi; dönüşüm ve hizalamada ~4,5 GB boş RAM.
- Windows'ta WSL2 şart (CT2 çatalının Windows yolu yok). Yalnız Linux + CUDA 12; AMD/Intel yok; ASR için CPU yolu
  ölçülmedi (`ayarlar.json` → `"cihaz": "cpu"` ile denenebilir).
- Uzun sessizlik ya da müzik yine tekrar eden ya da uydurma metin üretebilir; kütüphanenin onarımı çoğunu yakalar, hepsini değil.
- Üst üste konuşma ve konuşmacı ayrımı yok. tr/en/ja dışındaki diller deneysel (`docs/diller.md`).

## Lisans ve emek

Kod: Apache-2.0, Copyright 2026 Ali Haydar Ozturk. Modeller: CrisperWhisper 2.0 Turbo (Nyra Health, ticari olmayan
araştırma lisansı; çıkarım kodu MIT), wav2vec2 hizalama modelleri (mpoyraz CC BY 4.0, jonatasgrosman Apache-2.0,
torchaudio/fairseq MIT), CTranslate2 (OpenNMT, MIT), PyTorch. Tam liste: [THIRD_PARTY.md](THIRD_PARTY.md).
Kardeş proje: [voxcpm2-turkce-ses-tasarimi](https://github.com/alexturkey/voxcpm2-turkce-ses-tasarimi) (Türkçe ses
tasarımı; örnek ses oradan). Nyra Health ya da OpenNMT ile bağımız yok.
