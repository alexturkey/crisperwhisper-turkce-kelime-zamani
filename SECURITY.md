# Güvenlik / Security

**TR**

Bir güvenlik açığı bulduysanız lütfen herkese açık bir issue açmayın. GitHub'ın özel bildirim yolunu kullanın: repo
sayfasında **Security → Report a vulnerability**. Bildirim yalnız bakımcıya gider. Yazarken: sürüm (`git log -1` ya da
Release etiketi), nasıl tetiklendiği, etkisi. Hedef: 7 gün içinde ilk cevap; düzeltme yayınlanana kadar ayrıntıyı
paylaşmamanızı rica ederiz.

Kapsam: bu depodaki Python kodu ve `scripts/` altındaki kurulum betikleri. Kapsam dışı: CrisperWhisper paketi ve
modeli, CTranslate2, torch/torchaudio, hizalama modelleri (kendi projelerine bildirin).

Bilinen tasarım sınırları (açık değil, bilerek böyle):
- Ağ erişimi yalnız kurulumda (Hugging Face, PyPI, download.pytorch.org); her indirme sabit commit + sha256 ile
  doğrulanır, tutmazsa durur. Çalışma anında ağ yok; `HF_HUB_OFFLINE=1` ile tamamen kapatılabilir (deneysel dillerin
  ilk indirmesi hariç).
- Sunucu, port, arayüz yok; yalnız komut satırı. Çıktılar yerel klasöre yazılır.
- Hugging Face modelleri `pytorch_model.bin` (pickle) biçimindedir; `transformers` bunları `weights_only` güvenli
  yükleyiciyle açar ve dosyalar sabit commit + sha256 ile doğrulanır. Kendi verdiğiniz `--hizalama-modeli` için bu
  doğrulama yoktur: yalnız güvendiğiniz depoları verin.
- `-ExecutionPolicy Bypass` (Windows sarmalayıcı) yalnız o PowerShell sürecine etki eder; `kur.sh` sudo istemez,
  PATH ya da sistem ayarı değiştirmez.

**EN**

If you find a security vulnerability, please do not open a public issue. Use GitHub's private reporting:
**Security → Report a vulnerability** on the repository page. Include the version (`git log -1` or the Release tag),
how to trigger it and the impact. Target: first reply within 7 days; please hold details until a fix is out.

Scope: the Python code in this repository and the install scripts under `scripts/`. Out of scope: the CrisperWhisper
package and model, CTranslate2, torch/torchaudio and the alignment checkpoints (report upstream).

Known design limits (intentional):
- Network access only at install time (Hugging Face, PyPI, download.pytorch.org); every download is pinned to a commit
  and verified with sha256, a mismatch stops the installer. No network at run time; `HF_HUB_OFFLINE=1` turns it off
  completely (except the first download of an experimental language).
- No server, port or UI; command line only, outputs go to a local folder.
- Hugging Face alignment checkpoints are `pytorch_model.bin` (pickle); `transformers` loads them with the
  `weights_only` safe loader and the files are pinned by commit + sha256. A model you pass yourself with
  `--hizalama-modeli` is not verified: use only repositories you trust.
- `-ExecutionPolicy Bypass` (Windows wrapper) affects only that PowerShell process; `kur.sh` needs no sudo and changes
  no PATH or system setting.
