# Контра для Android

`public/kontra.apk` — приложение-обёртка: открывает https://rjynhf.onrender.com/play на весь экран.

Собрано без Android Studio: `MainActivity.java` → javac (android.jar) → dx → `mkapk.py`
(двоичный AndroidManifest.xml и resources.arsc) → jarsigner.
Ключ подписи хранится у владельца отдельно (kontra.keystore) — он нужен для обновлений.
