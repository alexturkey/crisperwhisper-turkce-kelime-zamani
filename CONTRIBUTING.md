# Contributing / Katkı

## English (authoritative)

Thank you for helping. You do not need to be an expert, and most useful changes need **no GPU (docs, translations and tests run without one)**.

**What helps most:** runs on other GPUs and in other languages (use the Hardware test form: card, driver, command, the TRANSKRIPT_OK line, a few wrong word or time examples), word-time checks against hand labels, clearer install steps, typo and translation fixes.

### Your first pull request in 5 steps
1. **Fork** the repository (Fork button on GitHub), then clone your fork.
2. **Branch and change one thing**: `git switch -c fix/short-name`.
3. **Run the checks** (a few seconds, needs Python 3): `python -I -X utf8 scripts/denetim.py --hizli` (it prints PASSED or RED).
4. **Commit and push** to your fork. Use your GitHub no-reply e-mail (see "Your commit e-mail" below).
5. **Open the pull request** and fill in the short template. Not sure it is ready? Open it as a **draft**; we will say what to fix. Our goal is a first reply within 7 days: a goal of a small volunteer project, not a promise.

### What we accept and what we decline
| Accepted | Declined (with a kind reason) |
|---|---|
| A run report from another GPU or language, with the output line | Lowering the fixed quality settings (pinned model commits and sha256, CT2 int8 compute, the cu126 torch wheel, the two-process ASR then alignment design) to go faster |
| Docs, typo and translation fixes | Model weights, videos, large binaries |
| A script fix that shows the problem and the fix | Claims nobody ran ("should work") |
| A change that keeps the default behaviour identical, or is marked experimental and off by default | Personal paths, names, e-mails, tokens |
| A speed or memory saving with a measurement and the same output | Invisible or bidirectional Unicode, obfuscated code, downloads from hosts not listed in `PRIVACY.md`, telemetry |

A decline is about the rule, never about you.

### Evidence labels (use them in the pull request and in docs)
- **[measured]** you ran it and kept the log or numbers.
- **[read]** you read it in a file or document (give the path).
- **[computed]** derived from measured numbers.
- **[user-reported]** someone else reported it; not reproduced.
- **[guess]** not checked.

Do not write "works" about something you did not run. A labelled guess is welcome; an unlabelled one is not.

### No GPU? You can still help
Read the install steps and tell us where you got stuck, fix a sentence in a translation, add a missing "what you see / what to do" row to `docs/SIK_HATALAR.md`, improve an error message, or run the tests. These are real contributions.

### One language is enough
Write your pull request in English or Turkish (any language is fine if that is what you have; we will cope). You do not have to write both: if your change touches a section, a maintainer writes the other language. For README content changes edit `README.md` (the English source); translations are updated together by the maintainers. For the license and security text, English is authoritative in every language.

### Your commit e-mail
Commits keep their e-mail in history for good. To keep your address private use the GitHub no-reply address: **GitHub > Settings > Emails > "Keep my email addresses private"**, then `git config user.email "<ID>+<username>@users.noreply.github.com"` (the ID is shown on that page). Commits with another address are accepted; our checks only warn.

### Also
- Security problems: do not open a public issue; see `SECURITY.md`.
- Working with an AI coding agent: read `AGENTS.md` (the agent must never commit, upload or serve the non-commercial model weights).
- Contributions are accepted under the repository's license (Apache-2.0). The model weights stay under the Nyra Health non-commercial research license (`NOTICE`).
- Be kind: `CODE_OF_CONDUCT.md`.

## Türkçe

Teşekkürler. Uzman olmanız gerekmez; işe yarayan değişikliklerin çoğu **GPU istemez (belge, çeviri ve testler GPU'suz çalışır)**.

**En değerli katkı:** başka kartlarda ve başka dillerde denemeler (Donanım testi formu: kart, sürücü, komut, TRANSKRIPT_OK satırı, birkaç yanlış kelime ya da zaman örneği), elle etiketlenmiş kelime zamanıyla karşılaştırma, daha net kurulum adımları, yazım ve çeviri düzeltmeleri.

### İlk PR'ınız 5 adımda
1. Repoyu **fork'layın** (GitHub'da Fork düğmesi), fork'unuzu klonlayın.
2. **Dal açın, tek şeyi değiştirin**: `git switch -c fix/kisa-ad`.
3. **Kontrolleri çalıştırın** (birkaç saniye, Python 3 gerekir): `python -I -X utf8 scripts/denetim.py --hizli` (GEÇTİ ya da KIRMIZI yazar).
4. Fork'unuza **commit ve push**. GitHub no-reply e-postanızı kullanın (aşağıda).
5. **PR açın**, kısa şablonu doldurun. Hazır mı emin değilseniz **taslak (draft)** açın; neyi düzelteceğinizi söyleriz. Hedefimiz ilk yanıtı 7 gün içinde vermek: küçük bir gönüllü projenin hedefi, taahhüdü değil.

### Neyi alırız, neyi geri çeviririz
| Alırız | Gerekçesini nazikçe söyleyerek geri çeviririz |
|---|---|
| Başka kartta ya da dilde deneme raporu (çıktı satırıyla) | Hız için sabit kalite ayarlarını (pinned model commits and sha256, CT2 int8 compute, the cu126 torch wheel, the two-process ASR then alignment design) düşürmek |
| Belge, yazım, çeviri düzeltmesi | Model ağırlığı, video, büyük ikili dosya |
| Sorunu ve çözümü gösteren betik düzeltmesi | Kimsenin çalıştırmadığı iddia ("çalışmalı") |
| Varsayılan davranışı değiştirmeyen ya da deneysel ve varsayılan kapalı işaretli değişiklik | Kişisel yol, ad, e-posta, token |
| Ölçümlü, aynı çıktıyı veren hız ya da bellek kazancı | Görünmez/çift yönlü Unicode, gizlenmiş kod, `PRIVACY.md`'de olmayan adresten indirme, telemetri |

Ret kurala dairdir, size değil.

### Kanıt etiketleri (PR'da ve belgelerde kullanın)
**[ölçtüm]** çalıştırdınız, günlük/sayı elinizde; **[okudum]** dosya ya da belgede okudunuz (yolunu yazın); **[hesap]** ölçülen sayılardan türetildi; **[kullanıcı bildirdi]** başkası bildirdi, tekrarlanmadı; **[tahmin]** denenmedi. Çalıştırmadığınız şey için "çalışır" yazmayın; etiketli tahmin makbuldür.

### GPU'nuz yok mu? Yine de yardım edebilirsiniz
Kurulum adımlarını okuyup nerede takıldığınızı söylemek, bir çeviride cümle düzeltmek, `docs/SIK_HATALAR.md`'na eksik bir "ne görürsünüz / ne yapılır" satırı eklemek, bir hata mesajını netleştirmek ya da testleri çalıştırmak gerçek katkıdır.

### Tek dil yeter
PR'ınızı İngilizce ya da Türkçe yazın (elinizdeki dil neyse o da olur). İkisini birden yazmanız gerekmez: değişiklik bir bölüme dokunuyorsa diğer dili bakımcı yazar. README içerik değişikliği için `README.md`'yi (İngilizce kaynak) düzenleyin; çeviriler bakımcılar tarafından birlikte güncellenir. Lisans ve güvenlik metninde her dilde İngilizce esastır.

### Commit e-postanız
Commit'teki e-posta geçmişte kalıcıdır. Gizli kalması için GitHub no-reply adresini kullanın: **GitHub > Settings > Emails > "Keep my email addresses private"**, sonra `git config user.email "<ID>+<kullanici>@users.noreply.github.com"` (ID aynı sayfada yazar). Başka adresli commit de kabul edilir; kontrollerimiz yalnız uyarır.

### Ayrıca
Güvenlik sorunu: herkese açık issue açmayın, `SECURITY.md`. Yapay zeka ajanıyla çalışıyorsanız `AGENTS.md` (ajan ticari olmayan model ağırlıklarını asla commit'lemez, yüklemez, sunmaz). Katkılar deponun lisansı (Apache-2.0) altında kabul edilir. Model ağırlıkları Nyra Health'in ticari olmayan araştırma lisansında kalır (`NOTICE`). Nazik olun: `CODE_OF_CONDUCT.md`.
