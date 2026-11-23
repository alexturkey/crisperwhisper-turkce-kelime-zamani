# Sık hatalar / Common pitfalls

Her madde: kod, belirti, ne yapılır. Kodlar `docs/hata_imzalari.json` ile aynıdır (imza = log metninde aranan düz alt dize). Etiket [okudum] = kodda ya da belgede görüldü. /
Each item: code, symptom, what to do. Codes match `docs/hata_imzalari.json`. Label [read] = seen in code or docs.

Kuru çalışma / Dry run: `bash scripts/kur.sh --kok ~/stt --kuru` (writes nothing; prints the `[STT-...]` lines). Yerel rapor / local report: `bash scripts/tani.sh`.

1. <a id="stt-e-arac"></a>**`STT-E-ARAC`: Python, venv, curl ya da sha256sum eksik / Python, venv, curl or sha256sum missing** (hata; kur.sh --kuru) [okudum]
   - Ne yapılır: Adı geçen aracı kurun (Ubuntu: `sudo apt install python3-venv curl`, gerekebilecek tek sudo), sonra kuru çalışmayı yeniden koşun.
   - What to do: Install the named tool (Ubuntu: `sudo apt install python3-venv curl`, the only sudo you may need), then run the dry run again.
2. <a id="stt-e-gpu"></a>**`STT-E-GPU`: NVIDIA kart, sürücü >= 570 ya da 4 GB VRAM yok / NVIDIA GPU, driver >= 570 or 4 GB VRAM not found** (hata; kur.sh --kuru) [okudum]
   - Ne yapılır: Windows ya da Linux NVIDIA sürücüsünü güncelleyin; WSL2'de `wsl --update`; Ubuntu içinde `nvidia-smi` çalışmalı.
   - What to do: Update the Windows or Linux NVIDIA driver; on WSL2 run `wsl --update`; `nvidia-smi` must work inside Ubuntu.
3. <a id="stt-e-disk"></a>**`STT-E-DISK`: Kurulum kökünde 8 GiB'den az boş yer / Less than 8 GiB free at the install root** (hata; kur.sh --kuru) [okudum]
   - Ne yapılır: `--kok` ile en az 8 GiB boş yeri olan başka bir sürücüde kök seçin (yaklaşık 7 GB kullanılır).
   - What to do: Pick another root with `--kok` on a drive with at least 8 GiB free (about 7 GB is used).
4. <a id="stt-e-manifest"></a>**`STT-E-MANIFEST`: ayarlar/manifest.json yok ya da sabitleri eksik / ayarlar/manifest.json is missing or has no pins** (hata; kur.sh --kuru) [okudum]
   - Ne yapılır: Dosyayı git'ten geri alın (`git checkout -- ayarlar/manifest.json`). Bir denetimi geçmek için sabiti asla değiştirmeyin.
   - What to do: Restore the file from git (`git checkout -- ayarlar/manifest.json`). Never edit a pin to get past a check.
5. <a id="stt-w-ram"></a>**`STT-W-RAM`: 7 GiB'den az RAM görünüyor / Under 7 GiB of RAM visible** (uyarı; kur.sh --kuru) [okudum]
   - Ne yapılır: CT2 dönüşümü yaklaşık 4,5 GB boş RAM ister: diğer uygulamaları kapatın; WSL2'de `.wslconfig` bellek sınırını yükseltin.
   - What to do: The CT2 conversion needs about 4.5 GB free: close other apps; on WSL2 raise the memory limit in `.wslconfig`.
6. <a id="stt-w-kok"></a>**`STT-W-KOK`: Kök WSL2'ye bağlanmış bir Windows sürücüsünde / The root is on a Windows drive mounted into WSL2** (uyarı; kur.sh --kuru) [okudum]
   - Ne yapılır: Çalışır ama her dosyada yükleme dakikalar sürer; hız için Linux dosya sisteminde `--kok ~/stt` kullanın.
   - What to do: It works but loading takes minutes per file; use `--kok ~/stt` on the Linux filesystem for speed.
7. <a id="stt-w-disk"></a>**`STT-W-DISK`: Boş disk ölçülemedi / Free disk space could not be measured** (uyarı; kur.sh --kuru) [okudum]
   - Ne yapılır: Boş yeri `df -h <kök>` ile kendiniz bakın (8 GiB gerekir).
   - What to do: Check free space yourself with `df -h <root>` (8 GiB needed).
8. <a id="stt-e-wsl"></a>**`STT-E-WSL`: wsl.exe bulunamadı / wsl.exe not found** (hata; kur.ps1) [okudum]
   - Ne yapılır: WSL2'yi bir kez yönetici olarak kurun: `wsl --install -d Ubuntu`, yeniden başlatın, Ubuntu'yu bir kez açın, sonra kurulumu tekrar çalıştırın.
   - What to do: Install WSL2 once as administrator: `wsl --install -d Ubuntu`, reboot, open Ubuntu once, then run the installer again.
9. <a id="stt-e-pip"></a>**`STT-E-PIP`: pip ctranslate2-crisperwhisper tekerini bulamıyor / pip finds no ctranslate2-crisperwhisper wheel** (hata; kur.sh) [okudum]
   - Ne yapılır: CT2 çatalının yalnız Linux x86_64 tekeri var: yerel Windows ya da macOS Python'u değil, WSL2 ya da Linux kullanın.
   - What to do: The CT2 fork has Linux x86_64 wheels only: use WSL2 or Linux, not native Windows or macOS Python.
10. <a id="stt-e-sha"></a>**`STT-E-SHA`: İndirme sabit sha256 ile uyuşmuyor / A download does not match its pinned sha256** (hata; kur.sh, kur_hizalama) [okudum]
   - Ne yapılır: Kurulumu yeniden çalıştırın (yarım dosyalar silinir). Sürerse kaynak dosya değişmiştir: issue açın, manifest'i değiştirmeyin, denetimi gevşetmeyin.
   - What to do: Re-run the installer (partial files are removed). If it persists the upstream file changed: open an issue, do not edit the manifest or relax the check.
11. <a id="stt-e-kontrol"></a>**`STT-E-KONTROL`: CUDA int8 ya da gerçek bir torch CUDA çekirdeği çalışmıyor / CUDA int8 or a real torch CUDA kernel does not run** (hata; transkript --kontrol) [okudum]
   - Ne yapılır: Sürücüyü (>= 570) ve WSL içinde `nvidia-smi`'yi kontrol edin; `requirements.txt`'teki cu126 torch tekerini koruyun (cu128 Linux tekerleri GTX 10xx çekirdeklerini düşürür); torch'u yükseltmeyin.
   - What to do: Check the driver (>= 570) and `nvidia-smi` inside WSL; keep the pinned cu126 torch wheel from `requirements.txt` (cu128 Linux wheels drop GTX 10xx kernels); do not upgrade torch.
12. <a id="stt-e-ram"></a>**`STT-E-RAM`: Dönüşüm öldürüldü ya da MemoryError / Conversion killed or MemoryError** (hata; kur.sh model step) [okudum]
   - Ne yapılır: En az 4,5 GB RAM boşaltın (uygulamaları kapatın) ve yalnız o adımı yeniden koşun: `--adim model`.
   - What to do: Free at least 4.5 GB of RAM (close apps) and re-run only the step: `--adim model`.
13. <a id="stt-e-vram"></a>**`STT-E-VRAM`: 4 GB kartta hizalamada bellek bitti / Out of memory in alignment on a 4 GB card** (hata; transkript alignment) [okudum]
   - Ne yapılır: `--hizalama-cihazi cpu` (daha yavaş) ya da daha kısa ses kullanın; yine düşerse `kelimeler.json` ile bildirin.
   - What to do: Use `--hizalama-cihazi cpu` (slower) or a shorter audio file; report with the `kelimeler.json` if it still fails.
14. <a id="stt-e-ffmpeg"></a>**`STT-E-FFMPEG`: Ses çözülemedi (video ya da alışılmadık kap) / Audio could not be decoded (video or unusual container)** (hata; transkript ses) [okudum]
   - Ne yapılır: ffmpeg kurun (`sudo apt install ffmpeg`) ya da sesi önce wav/flac/mp3 olarak çıkarın.
   - What to do: Install ffmpeg (`sudo apt install ffmpeg`) or extract the audio to wav/flac/mp3 first.
15. <a id="stt-e-dil"></a>**`STT-E-DIL`: Dil için hizalama modeli yok / No alignment model for the language** (hata; transkript akis) [okudum]
   - Ne yapılır: `--hizalama-modeli <HF wav2vec2 CTC id>` ile birlikte `--hizalama-revizyon <commit>` verin (`docs/diller.md`).
   - What to do: Pass `--hizalama-modeli <HF wav2vec2 CTC id>` together with `--hizalama-revizyon <commit>` (see `docs/diller.md`).

Daha fazla belirti tablosu / more symptoms: `AGENTS.md` bölüm 4 (Troubleshooting). Aynı hata iki kez: dur, kodu ve log'un ilk 20 satırını issue'ya yaz (kişisel yol ve adı sil). / Same error twice: stop and post the code and the first 20 log lines (remove personal paths and names).
