# Languages and how words are split / Diller ve kelime ayırma

**EN.** The transcript comes from CrisperWhisper 2.0 Turbo (verbatim mode: fillers, false starts and repetitions are
kept, `[UH]`/`[UM]`-style event tags may appear). Word *times* come from a second model: a wav2vec2 CTC checkpoint
for the language, through `torchaudio.functional.forced_align`. What counts as a "word" (the timed unit) depends on
the script:

| Script group | Timed unit | How | Languages |
|---|---|---|---|
| Space-separated scripts (Latin, Cyrillic, Greek, Arabic, Hebrew, Devanagari ...) | the whitespace-separated word as the ASR wrote it, punctuation attached (`dünya.`) | characters of each word are force-aligned; words are separated by the alignment model's word-delimiter token; a word's time = first character start .. last character end | tr, en, de, fr, es, it, nl, pt, ru, uk, pl, cs, sk, sl, hr, ro, hu, fi, da, sv, no, nn, el, ca, eu, gl, lv, ka, ar, he, fa, ur, hi, te, ml, vi, ko, id, tl |
| No-space scripts: CJK ideographs, kana, Thai, Lao, Myanmar, Khmer | **one character** (kanji / kana / hanzi / Thai letter). Latin letters or digits inside such text stay together as one unit (`AI2`) | the ASR token group is split into characters (`transkript.diller.birimlere_ayir`); every character is force-aligned as its own unit, no delimiter token between them; `kelimeler.json` has `"birim": "karakter"` | ja, zh (model in the table); yue, th, lo, my, km (no alignment model in the table: pass `--hizalama-modeli`, otherwise the run stops with a message) |
| Right-to-left scripts (Arabic, Hebrew, Persian, Urdu) | the word | same as space-separated. **The output lists words in spoken (chronological) order**, which is logical order; a viewer renders the glyphs right to left. SRT/VTT lines contain the words in logical order with no direction marks | ar, he, fa, ur |
| Korean | the space-separated eojeol (word + particles), as the ASR wrote it | hangul syllables are characters in the alignment model's vocabulary, so each syllable is aligned and the eojeol spans them | ko |

Morpheme-level splitting (Japanese MeCab/fugashi, Chinese jieba, Thai pythainlp) is **not** built in: the ASR model does
not emit morpheme boundaries and we did not want to ship three more tokenizers with their dictionaries. The character
times in `kelimeler.json` are enough to group characters into morphemes yourself: run any tokenizer over the joined
text and take the first/last character time of each morpheme (the characters are in order, 1:1 with the text).

**Which languages were actually run here** (GTX 1050 Ti 4 GB, WSL2; numbers in `docs/olcumler.md`): **tr, en, ja**.
Every other language in the table is **experimental**: the alignment model id is the one WhisperX 3.8.6 uses, it is
downloaded from the model's `main` revision (not pinned) on first use, and nobody here has listened to the result.
Reports welcome in Discussions. `python -m transkript --diller` prints the table with the tested/experimental flag.

Languages the ASR model knows but the table lacks: pass any Hugging Face wav2vec2 CTC checkpoint with
`--hizalama-modeli <id>`; characters missing from its vocabulary are dropped for alignment and a word with no
alignable character is interpolated between its neighbours (`"yontem": "ara_deger"`).

**Text normalisation before alignment.** Lower-case (Turkish-aware: `I`→`ı`, `İ`→`i` for tr/az; upper-case for the
torchaudio English/VoxPopuli models), Unicode NFC, then every character not in the alignment model's vocabulary is
dropped (punctuation, digits for most models, foreign letters). The output keeps the ASR's original spelling.

**What the times mean.** CTC models emit each character in one or two 20 ms frames ("peaky"); the time of a word is
the span from the first character's frame to the last character's frame. The end of a word therefore sits where its
last sound was recognised, and silence after a word is never inside the word. The native CrisperWhisper
cross-attention times are kept in `kelimeler.json` under `asr_kelimeleri` for comparison only.

---

**TR.** Metin CrisperWhisper 2.0 Turbo'dan gelir (verbatim: dolgu sesleri, yarım kelimeler, tekrarlar korunur;
`[UH]`/`[UM]` gibi olay etiketleri görülebilir). Kelime *zamanları* ikinci bir modelden gelir: dile ait wav2vec2 CTC
modeli ve `torchaudio.functional.forced_align`. "Kelime" (zamanlanan birim) yazı sistemine göre değişir:

| Yazı grubu | Zamanlanan birim | Nasıl | Diller |
|---|---|---|---|
| Boşluklu yazılar (Latin, Kiril, Yunan, Arap, İbrani, Devanagari ...) | ASR'nin yazdığı boşlukla ayrılmış kelime, noktalama bitişik (`dünya.`) | kelimenin harfleri hizalanır, kelimeler hizalama modelinin ayırıcı simgesiyle ayrılır; süre = ilk harfin başı .. son harfin sonu | tr, en, de, fr, es, it, nl, pt, ru, uk, pl, cs, sk, sl, hr, ro, hu, fi, da, sv, no, nn, el, ca, eu, gl, lv, ka, ar, he, fa, ur, hi, te, ml, vi, ko, id, tl |
| Boşluksuz yazılar: CJK ideogramları, kana, Tay, Lao, Myanmar, Khmer | **tek karakter** (kanji / kana / hanzi / Tay harfi). İçerideki Latin harf ya da rakam dizisi tek birim kalır (`AI2`) | ASR token grubu karakterlere bölünür (`transkript.diller.birimlere_ayir`), her karakter ayrı birim olarak hizalanır, aralarına ayırıcı konmaz; `kelimeler.json` içinde `"birim": "karakter"` | ja, zh (tabloda model var); yue, th, lo, my, km (tabloda hizalama modeli yok: `--hizalama-modeli` verin, yoksa mesajla durur) |
| Sağdan sola yazılar (Arapça, İbranice, Farsça, Urduca) | kelime | boşluklu gibi. **Çıktıda kelimeler söylenme (zaman) sırasındadır**, yani mantıksal sıra; görüntüleyici harfleri sağdan sola çizer. SRT/VTT satırları yön işareti içermez | ar, he, fa, ur |
| Korece | ASR'nin yazdığı boşluklu eojeol (kelime + ekler) | hangul heceleri hizalama modelinin sözlüğünde karakterdir; her hece hizalanır, eojeol onları kapsar | ko |

Morfem düzeyinde bölme (Japonca MeCab/fugashi, Çince jieba, Tayca pythainlp) **yerleşik değil**: ASR modeli morfem
sınırı vermez ve üç ayrı sözlüklü ayırıcı taşımak istemedik. `kelimeler.json` içindeki karakter zamanları yeter:
birleşik metni istediğiniz ayırıcıyla bölün, her morfemin ilk/son karakter zamanını alın (karakterler sıralı, metinle
bire bir).

**Burada gerçekten çalıştırılan diller** (GTX 1050 Ti 4 GB, WSL2; sayılar `docs/olcumler.md`): **tr, en, ja**.
Tablodaki öteki diller **deneysel**: model kimliği WhisperX 3.8.6'nın kullandığıdır, ilk kullanımda modelin `main`
sürümünden iner (sabitlenmemiş), sonucu burada kimse dinlemedi. Discussions'a rapor bekleriz.
`python -m transkript --diller` tabloyu sınanmış/deneysel işaretiyle yazar.

ASR'nin bildiği ama tabloda olmayan dil: `--hizalama-modeli <id>` ile herhangi bir Hugging Face wav2vec2 CTC modeli;
sözlüğünde olmayan harfler hizalamada atılır, hiç harfi kalmayan kelime komşuları arasında ara değerle yerleşir
(`"yontem": "ara_deger"`).

**Hizalama öncesi metin düzenleme.** Küçük harf (Türkçe için `I`→`ı`, `İ`→`i`; torchaudio İngilizce/VoxPopuli
modellerinde büyük harf), Unicode NFC, sonra hizalama modelinin sözlüğünde olmayan her karakter atılır (noktalama,
çoğu modelde rakam, yabancı harf). Çıktıda ASR'nin özgün yazımı korunur.

**Zamanlar ne anlama gelir.** CTC modelleri her harfi bir-iki 20 ms'lik karede "sivri" verir; kelimenin zamanı ilk
harfin karesinden son harfin karesine uzanır. Kelimenin sonu son sesin tanındığı yerdir; kelimeden sonraki sessizlik
kelimenin içine girmez. CrisperWhisper'ın kendi cross-attention zamanları yalnız karşılaştırma için
`kelimeler.json` → `asr_kelimeleri` altında durur.
