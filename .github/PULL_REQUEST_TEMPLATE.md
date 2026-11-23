<!-- One language is enough (English or Turkish); a maintainer adds the other. Tek dil yeter. Draft is fine. Taslak PR olur. -->

## What changes / Ne değişiyor
<!-- 1-3 sentences / 1-3 cümle -->

## Kind / Tür
- [ ] Docs or script / Belge ya da betik
- [ ] Behaviour change / Davranış değişikliği
- [ ] Test report from another machine / Başka makinede test raporu

## Evidence / Kanıt
Label each claim: [measured] [read] [computed] [user-reported] [guess] ([ölçtüm] [okudum] [hesap] [kullanıcı bildirdi] [tahmin]).
<!-- paste the log or numbers, or write "none" / günlük ya da sayıyı yapıştırın, yoksa "yok" -->

## Checks / Kontroller
- [ ] `python -I -X utf8 scripts/denetim.py --hizli` result / sonuç: <!-- GECTI -->
- [ ] No personal paths, names, e-mails (use the GitHub no-reply address), tokens, model weights or videos / Kişisel yol, ad, e-posta, token, model, video yok
- [ ] Quality settings and the default command line unchanged (pinned model commits and sha256, CT2 int8 compute, the cu126 torch wheel, the two-process ASR then alignment design) / Kalite ayarları ve varsayılan komut satırı değişmedi
