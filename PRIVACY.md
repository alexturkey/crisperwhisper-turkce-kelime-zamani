# Privacy / Gizlilik

## English (authoritative)

**Short version: crisperwhisper-turkce-kelime-zamani has no telemetry. Its scripts use the network only for the downloads listed below, and only from the hosts listed below.** Nothing about you, your machine or your data is uploaded.

### What the scripts fetch
| Host | What | Which script, when |
|---|---|---|
| `huggingface.co` and `hf.co` sub-hosts | model files at a pinned commit; alignment checkpoints | `scripts/kur.sh`, install; an experimental language downloads its alignment model on first use |
| `download.pytorch.org` | torch and torchaudio wheels (cu126); the English torchaudio alignment bundle | `scripts/kur.sh`, install |
| `pypi.org` and `files.pythonhosted.org` | Python packages from `requirements.txt` | `scripts/kur.sh`, install |

Every download is checked against a pinned sha256 where one exists and stops on a mismatch. Like any download, the host sees your IP address and the ordinary request headers. We send nothing else: no account, no usernames, no system information, no usage data.

### What it does not do
No telemetry or analytics, no crash reports, no update check, no accounts or cookies, no network ports opened. The transcription runs fully on your machine: your audio and the text never leave it.

### What stays on your computer
The install root you choose (`--kok`: models, caches, downloads), the `.venv/` and `ayarlar.json` in the repository folder, and the `cikti/` folders with your transcripts (verbatim text is personal data: see `ETHICS.md`). Logs can contain your folder path: remove it before you post a log in an issue.

### Outside our scripts
- GitHub processes what you post here (issues, pull requests, stars) under the GitHub Privacy Statement; it is public.
- The model weights are under the Nyra Health non-commercial license, not under this policy (`NOTICE`).

### Check it yourself (a few seconds, nothing is downloaded)
Every network call in the code: `grep -rnE "https?://" transkript scripts ayarlar --exclude=repo_kapi.json --exclude=dil_eslik_denetimi.py`. Expected today: the hosts above and nothing else. If you find a call that is not listed here, please report it as in `SECURITY.md`. When a release adds a host, this file is updated in the same change.

## Türkçe

**Kısaca: crisperwhisper-turkce-kelime-zamani'da telemetri yok. Betikler ağı yalnız aşağıdaki indirmeler için, yalnız aşağıdaki adreslerden kullanır.** Sizin, makinenizin ya da verinizin hiçbir bilgisi yüklenmez.

### Betiklerin indirdikleri
| Adres | Ne | Hangi betik, ne zaman |
|---|---|---|
| `huggingface.co` ve `hf.co` alt adresleri | sabit commit'teki model dosyaları; hizalama modelleri | `scripts/kur.sh`, kurulum; deneysel bir dil hizalama modelini ilk kullanımda indirir |
| `download.pytorch.org` | torch ve torchaudio tekerleri (cu126); İngilizce torchaudio hizalama paketi | `scripts/kur.sh`, kurulum |
| `pypi.org` ve `files.pythonhosted.org` | `requirements.txt` Python paketleri | `scripts/kur.sh`, kurulum |

Sabitlenmiş sha256 olan her indirme ona karşı denetlenir, uyuşmazsa durur. Her indirmede olduğu gibi karşı taraf IP adresinizi ve olağan istek başlıklarını görür. Başka hiçbir şey göndermeyiz: hesap, kullanıcı adı, sistem bilgisi, kullanım verisi yok.

### Yapmadıkları
Telemetri/analitik yok, çökme raporu yok, güncelleme denetimi yok, hesap ya da çerez yok, ağ portu açmaz. Yazıya dökme tamamen makinenizde çalışır: sesiniz ve metin makineden çıkmaz.

### Bilgisayarınızda kalanlar
Seçtiğiniz kurulum kökü (`--kok`: modeller, önbellekler, indirmeler), depo klasöründeki `.venv/` ve `ayarlar.json` ile yazıya döküm çıktılarınızın olduğu `cikti/` klasörleri (birebir metin kişisel veridir: `ETHICS.md`). Günlüklerde klasör yolunuz olabilir: issue'ya günlük koymadan önce silin.

### Betiklerimizin dışında
- Burada paylaştığınız (issue, PR, yıldız) GitHub tarafından GitHub Gizlilik Bildirimi'ne göre işlenir ve herkese açıktır.
- Model ağırlıkları Nyra Health'in ticari olmayan lisansındadır, bu metnin kapsamı dışındadır (`NOTICE`).

### Kendiniz denetleyin (birkaç saniye, hiçbir şey indirilmez)
Koddaki bütün ağ çağrıları: `grep -rnE "https?://" transkript scripts ayarlar --exclude=repo_kapi.json --exclude=dil_eslik_denetimi.py`. Bugün beklenen: yalnız yukarıdaki adresler. Listede olmayan bir çağrı bulursanız `SECURITY.md`'deki gibi bildirin. Bir sürüm yeni adres eklerse bu dosya aynı değişiklikte güncellenir.
