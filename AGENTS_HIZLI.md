# AGENTS_HIZLI.md: quick card for AI coding agents / Yapay zeka ajanları için hızlı kart

English first, Türkçe below. Full rules and evidence: [`AGENTS.md`](AGENTS.md) (it wins if the two ever differ). Error codes: `docs/hata_imzalari.json`, `docs/SIK_HATALAR.md`.

## English: decision tree (12 steps)
1. Goal: verbatim speech-to-text with word timestamps on Linux or Windows via WSL2 with an NVIDIA card of 4 GB or more. Anything else: tell the user and stop.
2. Quality is fixed (pinned model commits and sha256, CT2 int8 compute, the cu126 torch wheel, the two-process ASR then alignment design). Never lower it to save time or memory.
3. Dry run first, it writes nothing: `bash scripts/kur.sh --kok ~/stt --kuru`. Read every `HATA:` / `UYARI:` line; each carries a code such as `[STT-E-DISK]`.
4. A non-zero exit or any `HATA` in that list: take it to the user with the code and its first step from `docs/hata_imzalari.json`. Do not use a force flag to get past it.
5. The model license is non-commercial: tell the user (`NOTICE`) before downloading the weights and let the user answer (legal or consent steps belong to the human; never type the acceptance yourself).
6. Install: `bash scripts/kur.sh --kok ~/stt` (safe to re-run; verified files are skipped; an interrupted download continues).
7. First success: `.venv/bin/python -m transkript ornek/ornek.mp3 --dil tr --cikti cikti/ilk` (about 1 min on the Linux filesystem, several minutes when the root is on a mounted Windows drive [read from AGENTS.md and docs/olcumler.md]). Long runs: start hidden in the background and poll; do not block.
8. Exit 0 means the gate passed, nothing more: `KONTROL_OK` only shows the environment works; the word times are not checked against hand labels, read the output yourself.
9. A rejected or not-run gate means the result is NOT accepted. Never report success.
10. A line with a code: look it up in `docs/hata_imzalari.json`, give the user its first step, quote the code. Same error twice: stop, do not try a third time.
11. Paths and files are only what the user gave you. Never pick a file yourself.
12. Report in the user's language, with the code and the first 20 log lines. No personal paths, user names, e-mail addresses or tokens: write `<ROOT>`.

### Exit code -> action
| Script | Exit | Meaning | What you do | Codes |
|---|---|---|---|---|
| `kur.sh` | 0 | `KURULUM_OK` (with `--kuru`: no HATA) | Go to the first success step | - |
| `kur.sh` | 3 | only with `--kuru`: hardware, disk or tool missing | **Take it to the user**; do not edit the script | `STT-E-GPU` `STT-E-DISK` `STT-E-ARAC` |
| `kur.sh` | 1 | download, sha256 or check failed | Look up the line in `docs/hata_imzalari.json`; take it to the user | `STT-E-SHA` `STT-E-KONTROL` |

## Türkçe: karar ağacı (12 adım)
1. Amaç: Linux ya da WSL2 üzerinden Windows'ta, 4 GB ya da üstü NVIDIA kartla kelime zamanlı birebir yazıya döküm. Başka bir ortamsa kullanıcıya söyle ve dur.
2. Kalite sabit (pinned model commits and sha256, CT2 int8 compute, the cu126 torch wheel, the two-process ASR then alignment design). Zaman ya da bellek için asla düşürme.
3. Önce kuru çalıştır, hiçbir şey yazmaz: `bash scripts/kur.sh --kok ~/stt --kuru`. Her `HATA:` / `UYARI:` satırını oku; her biri `[STT-E-DISK]` gibi bir kod taşır.
4. Sıfır olmayan çıkış ya da listede herhangi bir `HATA`: kodu ve `docs/hata_imzalari.json`'ndaki ilk adımı kullanıcıya götür. Zorlayıcı bayrakla geçme.
5. Model lisansı ticari değildir: ağırlıkları indirmeden önce kullanıcıya söyle (`NOTICE`), cevabı kullanıcı versin (hukuki ya da onay adımları insanındır; kabulü asla kendin yazma).
6. Kurulum: `bash scripts/kur.sh --kok ~/stt` (tekrar çalıştırmak güvenli; doğrulanmış dosya atlanır; yarım indirme sürer).
7. İlk başarı: `.venv/bin/python -m transkript ornek/ornek.mp3 --dil tr --cikti cikti/ilk` (Linux dosya sisteminde yaklaşık 1 dk, kök bağlanmış Windows sürücüsündeyse birkaç dakika [AGENTS.md ve docs/olcumler.md'den okudum]). Uzun işleri gizli arka planda başlat, yoklayarak izle; bekleyerek kilitlenme.
8. Çıkış 0 yalnız kapının geçtiği demektir: `KONTROL_OK` yalnız ortamın çalıştığını gösterir; kelime zamanları elle etiketle karşılaştırılmaz, çıktıyı kendin oku.
9. Reddedilen ya da çalışmayan kapı: sonuç KABUL EDİLMEZ. Asla başarı bildirme.
10. Kodlu satır: `docs/hata_imzalari.json`'nda ara, ilk adımı kullanıcıya ver, kodu yaz. Aynı hata iki kez: dur, üçüncü kez deneme.
11. Yol ve dosya yalnız kullanıcının sana verdiğidir. Kendin dosya seçme.
12. Kullanıcının dilinde, kodla ve log'un ilk 20 satırıyla bildir. Kişisel yol, kullanıcı adı, e-posta, token yazma: `<ROOT>` yaz.

### Çıkış kodu -> eylem
| Betik | Çıkış | Anlam | Ne yaparsın | Kodlar |
|---|---|---|---|---|
| `kur.sh` | 0 | `KURULUM_OK` (`--kuru` ile: HATA yok) | İlk başarı adımına geç | - |
| `kur.sh` | 3 | yalnız `--kuru`: donanım, disk ya da araç eksik | **Kullanıcıya götür**; betiği değiştirme | `STT-E-GPU` `STT-E-DISK` `STT-E-ARAC` |
| `kur.sh` | 1 | indirme, sha256 ya da kontrol düştü | Satırı `docs/hata_imzalari.json`'da ara; kullanıcıya götür | `STT-E-SHA` `STT-E-KONTROL` |
