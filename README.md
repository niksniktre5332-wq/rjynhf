# Контра — отдельный сайт и онлайн-сервер

Сайт работает без Claude. В папке всё сразу:
- главная страница сайта: `public/index.html`;
- игра: `public/play.html`;
- свой онлайн-сервер для комнат: `server.js`.

## Запуск на своём компьютере
1. Установи Node.js 18 или новее: https://nodejs.org
2. В этой папке выполни:
   npm install
   npm start
3. Открой http://localhost:3000 — сайт; «Играть» открывает игру.
   Чтобы играть вдвоём на одном компьютере, открой игру во втором окне в режиме инкогнито.

## Выложить в интернет бесплатно (Render.com)
1. Загрузи эту папку в новый репозиторий на GitHub.
2. Зайди на https://render.com → New → Web Service → выбери репозиторий.
   Настройки подставятся из `render.yaml`: Build `npm install`, Start `npm start`.
3. Через пару минут сайт будет по адресу вида https://kontra-xxxx.onrender.com
   Эту ссылку можно давать друзьям.
На бесплатном тарифе сервер засыпает без игроков, первое открытие после паузы занимает до минуты.

Подойдёт любой хостинг с Node.js и WebSocket: Railway, Fly.io, свой VPS.

## Важно
Аккаунты, деньги, Gold и скины хранятся в браузере игрока (localStorage), а не на сервере.

## Вход через Google
1. Открой https://console.cloud.google.com → создай проект.
2. «APIs & Services» → «OAuth consent screen» → тип External → заполни название и почту → сохрани.
3. «Credentials» → «Create credentials» → «OAuth client ID» → тип «Web application».
   В «Authorized JavaScript origins» добавь адрес сайта, например https://rjynhf.onrender.com
4. Скопируй «Client ID».
5. В Render: сервис → Environment → Add variable: `GOOGLE_CLIENT_ID` = скопированный ID → Save.
После перезапуска на экране входа появится кнопка «Continue with Google».
