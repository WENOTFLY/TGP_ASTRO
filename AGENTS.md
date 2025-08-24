) Стартовые инструкции для Codex

Инициализация проекта

Язык: Python 3.11+. Фрейм: FastAPI + aiogram 3.x. Очередь: Celery/RQ + Redis. БД: PostgreSQL + Alembic. Хранилище: S3-совместимое.

Линтеры: ruff/black; типизация: mypy(strict); тесты: pytest (coverage ≥ 90%).

Docker: app, db, redis, minio, worker.

Создать Makefile, .env.sample, docker-compose.yml, базовую структуру (см. §1.2).

Вебхук Telegram

Роут /tg/webhook (HTTPS), allowed_updates=["message","callback_query","my_chat_member","pre_checkout_query"].

Настроить команду регистрации вебхука и healthchecks.

Регистратор модулей-экспертов

Реализовать плагинную систему: каждый эксперт — изолированный модуль по интерфейсу (см. §3.1).

Поднять главное меню с инлайн-кнопками (см. §2.1).

Ингестер ассетов

Реализовать валидатор/индексатор assets: (см. §4).

Прогнать валидатор при старте; хранить индекс в БД (decks) + кэш.

Платежи и квоты

Настроить Stars (XTR): инвойсы, pre_checkout, successful_payment, entitlements.

Витрина тарифов + учёт лимитов (см. §5).

Телеметрия

События и дашборды (см. §7).

Генерация

Общая шина: Draw → Compose → Writer → Verifier → Deliver.

Подключить все эксперты с их спецификой (см. §3.3–§3.10).

1) Архитектура и структура репозитория
1.1 Компоненты

Bot: FSM/Handlers, payments, keyboards, i18n.

Core: плагины экспертов, Draw/Compose, валидаторы, лимиты, платежи.

NLP: Guide/Writer/Verifier/Localizer (строгие JSON-ответы).

Storage: S3 + PDF/PNG генерация.

Telemetry: события, метрики, админ-срезы.

1.2 Дерево проекта
/app
  /bot               # Telegram-обвязка (aiogram), FSM, UI
  /core
    /plugins         # реестр и плагины экспертов
    /assets          # ингестер, индексы, валидаторы
    /draw            # детерминированный выбор элементов
    /compose         # сборка изображений (коллажи, диаграммы, колёса)
    /limits          # квоты, fair-use, троттлинг
    /payments        # Stars, продукты, entitlements
    /telemetry       # track(), события, метрики
  /experts
    /tarot           # модуль эксперта Таро
    /lenormand
    /runes
    /numerology
    /astrology
    /dreams
    /copywriter
    /assistant
  /nlp
    /guide           # подсказки по шагам
    /writer          # генерация структурированного ответа (strict JSON)
    /verifier        # проверка фактов/чисел/карт
    /localizer
  /api               # FastAPI роуты: /tg/webhook, /exports/pdf, /admin/*
  /storage           # s3 utils, html->pdf
  /db                # модели + alembic
  /tests             # unit + e2e
/assets              # каталоги с изображениями/манифестами (см. §4)

2) UX: меню, шаги, CTA
2.1 Главное меню (инлайн)

🃏 Таролог | ♣ Ленорман | ᚱ Рунолог | ✨ Астролог | 🌙 Сны | ✍️ Копирайтер | 🤖 Ассистент | 🔢 Нумеролог | 💎 Премиум/Оплата | 👤 Профиль/История

2.2 Шаблон флоу эксперта (унифицированный)

Intro + «Как это работает?»

Сбор данных (микро-формы; Guide даёт короткий совет на каждом шаге)

Подтверждение → «Готовим»

Сообщение #1: картинка + TL;DR

Сообщение #2: текст (секциями), «3 шага действий», дисклеймеры

CTA: «Уточнить», «Дотянуть X», «Другой спред/режим», «PDF/Сохранить», «Поделиться»

Показываем остаток квоты и аккуратный апселл

3) Плагины экспертов (модульно)
3.1 Общий интерфейс плагина

Каждый модуль экспортирует:

plugin_id: str (e.g. "tarot", "numerology").

form_steps(locale) -> [Step] (описание шагов и валидаций).

prepare(input) -> Facts (детерминированные факты/элементы).

compose(facts) -> ImageBundle (единая картинка/набор).

write(facts, locale, tone) -> StructuredText (Writer, strict JSON).

verify(facts, text) -> {ok, diffs} (Verifier).

cost() -> int or "unlimited" (стоимость запроса в квоте).

cta(facts) -> [SuggestedActions] (нативные предложения).

products_supported (если модулю нужны доп. платежи — опц.).

3.2 Общая компоновка изображений

Канвас по умолчанию: 1080×1080, фон из /assets/backgrounds.

Отступы: gutter ≥ 24px; подписи ≥ 28px, шрифт Inter.

Вес файла ≤ 3 МБ (WebP 80 / JPEG 85).

Водяной знак (тонкий), опционально.

3.3 ТАРО (🃏 Tarot)
3.3.1 Колода/ассеты

Директория: /assets/tarot/<deck_id>/

Обязательные файлы: deck.json, /cards/*.png (78 шт), back.png, опц. frame.png.

deck.json:

deck_id, name{ru,en}, type:"tarot", image:{aspect_ratio:"3:5",allow_reversed:true,frame?,default_back}

cards[]:
key (уникальный id, напр. major_00_fool, cups_ace),
display{ru,en}, file, arcana (major/minor), suit (wands/cups/swords/pentacles), rank (ace..king)/number,
upright[], reversed[] — списки ключевых слов.

3.3.2 Спрэды (реализовать сразу все)

tarot_one_daily — Одна карта (день)

cards_required=1, positions:[{1,"День"}], allow_reversed=true, unique_cards=true.

tarot_three_ppf — Прошлое–Настоящее–Будущее

cards_required=3, positions:[Past,Present,Future].

tarot_three_decision — Выбор А/Б + совет

cards_required=3, positions:[Вариант A, Вариант B, Совет].

tarot_five_solution — Решение проблемы (5)

Позиции: Ситуация, Корень, Что помогает, Что мешает, Исход.

tarot_celtic_cross_10 — Кельтский крест (10)

Позиции (классика): Сигнификатор, Перекрест, Основа, Прошлое, Цели, Будущее, Вы, Окружение, Надежды/Страхи, Итог.

tarot_relationship_7 — Отношения (7)

Вы, Партнёр, Связь, Сильное, Слабое, Урок, Перспектива.

tarot_career_7 — Карьера (7)

Ситуация, Сильные стороны, Слабые, Шанс, Риски, Рекомендация, Перспектива.

tarot_yes_no_3 — Да/Нет (3)

Позитив, Негатив, Баланс; Writer обязан давать взвешенный ответ (не бинарный оракул).

3.3.3 Правила выбора

Детерминизм: seed = SHA256(user_id || spread_id || yyyy-mm-dd || nonce).

Без повторов в пределах спрэда, allow_reversed — по спрэду/колоде, p_reversed=0.45 (конфиг).

nonce меняется при «Перетянуть».

3.3.4 Compose (объединённое изображение)

Сетка: 1, 3 (ряд), 5 (2+3), 7 (3+4), 10 (по КК макету), подписи: позиция + карта; реверс — поворот 180°.

Фреймы/тени — из frame.png при наличии.

3.3.5 Writer/Verifier (строгие)

Вход Writer: question, spread(positions), cards[{card_key, orientation, display, hints}].

Выход Writer:
tldr (≤280),
per_position[{idx,card_key,role,meaning}],
synthesis,
actions[3],
disclaimers.

Verifier: сверяет card_key/orientation/позиции; при несоответствии — регенерация.

3.4 ЛЕНОРМАН (♣ Lenormand)
3.4.1 Колода/ассеты

/assets/lenormand/<deck_id>/ + deck.json (36 карт, номера 1..36).

allow_reversed=false по умолчанию.

3.4.2 Спрэды

leno_three_line — 3 карты (линейный).

leno_five_line — 5 карт (ситуация-совет).

leno_nine_square — 3×3 квадрат (центр — ядро).

leno_grand_tableau_36 — Большой расклад (вся колода, 4×8 + 4 внизу) — требует отдельной разметки Compose и краткой сводки Writer.

3.4.3 Compose

Линейные — ряд/две строки; 3×3 — сетка; GT — предустановленная схема с номерами.

Подписи карт — короткие; общий TL;DR обязателен.

3.5 РУНЫ (ᚱ Runes)
3.5.1 Набор/ассеты

/assets/runes/<set_id>/ + set.json

runes[] {key, display, file, upright[], reversed[]?, can_reverse}

3.5.2 Спрэды

runes_one — 1 руна (день/ответ).

runes_three_ppf — прошлое/настоящее/будущее.

runes_five_cross — крест (центр — тема; стороны — факторы/совет).

3.5.3 Правила

Детерминизм по seed, уникальность в спрэде.

can_reverse — если true, использовать p_reversed=0.33.

3.6 НУМЕРОЛОГИЯ (🔢 Numerology)
3.6.1 Вход/валидаторы

Имя (одно/несколько), дата рождения (YYYY-MM-DD), опц. время/место (для суточных расчётов), язык/алфавит.

Параметр system: "pythagor" или "chaldean".

3.6.2 Ассеты

/assets/numerology/alphabets/*.json (RU/EN и пр.) — таблицы буква→число по системам.

/assets/numerology/rules.json — редукция (keep_master 11/22/33), стратегии личных циклов (personal_year/month/day), правила Pinnacles/Challenges.

3.6.3 Расчёты (детерминированно)

Life Path: редукция суммы yyyy+mm+dd c учётом master.

Birthday: редукция dd.

Expression (Destiny): сумма всех букв ФИО.

Soul Urge (Heart’s Desire): сумма гласных.

Personality: сумма согласных.

Maturity: редукция (Life Path + Expression).

Personal Year/Month/Day: по выбранной стратегии (описать в rules.json).

Pinnacles/Challenges: стандартные формулы (1-й пинокл: редукция (month + day), и т.д.; Challenges — абсолютные разницы).

Transit Letters/Essence — опционально, но контракт подготовить.

3.6.4 Compose (визуал)

Матрица Пифагора: сетка 3×3 с количеством повторов цифр, легенда.

Диаграммы периодов: шкала Personal Year/Month, пинки/вызовы (простая полосная).

3.6.5 Writer/Verifier

Writer строит отчёт из готовых чисел (никаких вычислений).

Verifier сравнивает все числа в тексте с facts_json.

3.7 АСТРОЛОГИЯ (✨ Astrology)
3.7.1 Вход

Дата, опц. время, место (геокод → TZ). При отсутствии времени — солар (без домов) с дисклеймером.

3.7.2 Данные/ассеты

Эфемериды (подключить шину; допускается lightweight режим с публичными приближениями).

/assets/astrology/glyphs/*.png (планеты/знаки/аспекты), astro.json (цвета/толщины/орбисы).

3.7.3 Факты

Положения планет по знакам (+ градусы), при времени — дома; аспекты (сходящиеся/расходящиеся с орбисами).

3.7.4 Compose

Колесо с домами/знаками, легенда таблицей (позиции планет). Вес ≤ 3 МБ.

3.7.5 Writer/Verifier

Writer даёт интерпретации с привязкой только к facts.

Verifier отключает любые «выдуманные» аспекты/позиции.

3.8 СНЫ (🌙 Dreams)
3.8.1 Вход

Текст сна, теги эмоций, контекст «перед сном/после сна».

3.8.2 Ассеты

/assets/dreams/lexicon.json — словарь символов с синонимами и смыслами.

/assets/dreams/symbols/*.png — изображения символов (опц.).

3.8.3 Подготовка фактов

Extractor извлекает символы/темы из текста по лексикону, формирует facts.

3.8.4 Compose

Коллаж 2–4 символов (или подбор релевантных фото из локальной библиотеки).

TL;DR + действия (мягко). Дисклеймер — не мед.помощь.

3.9 КОПИРАЙТЕР (✍️) и 3.10 АССИСТЕНТ (🤖)

Ввод темы/брифа.

Writer в строгом JSON: tldr, sections, actions.

Опц. баннер/постер по теме (генератор арта или подбор из фонов).

4) Ассеты: файловые требования (обязательно)
4.1 Каталоги
/assets
  /tarot/<deck_id>/cards/*.png, back.png, frame.png, deck.json
  /lenormand/<deck_id>/...
  /runes/<set_id>/...
  /astrology/{glyphs/*.png, astro.json}
  /dreams/{symbols/*.png, lexicon.json}
  /numerology/{alphabets/*.json, rules.json}
  /backgrounds/*.jpg|png
  /fonts/*.ttf

4.2 Ингестер

Валидация имен файлов, размеров (соотношение сторон), обязательных ключей в JSON.

Индексация в БД (decks) + кэш в памяти.

Генерация миниатюр (для Истории/админ).

5) Продукты, платежи, квоты
5.1 Продукты

pack_3 (3 запроса), pack_10 (10), unlimited_30d (безлимит 30 дней с Fair-Use).

(Опц.) sub_30d — рекуррентная Stars-подписка.

5.2 Stars/XTR

sendInvoice(currency="XTR", provider_token="")

Обязательно: pre_checkout_query → answerPreCheckoutQuery(ok=True) → successful_payment.

По successful_payment — создать/продлить entitlement.

5.3 Квоты

Пакет: списывать после успешной отправки ответа.

Безлимит: fair_daily_cap (конфиг), ограничение параллелизма (≤ 2).

Анти-флуд: минимальный интервал (напр., 5 сек).

6) Доставка и история

Сообщение #1: изображение + TL;DR.

Сообщение #2: подробный текст + actions.

Кнопки: «Дотянуть», «Другой спред/режим», «PDF», «Сохранить», «Поделиться».

История: draws (миниатюры, повтор, углубление), readings (pdf_url, text_md).

7) Телеметрия и удержание
7.1 События

start, form_step, form_completed, draw_started/finished, image_rendered, writer_ok, verifier_ok/failed, answer_sent, quota_spent, successful_payment, cta_clicked, error.

7.2 Удержание/апселлы

«Дневная карта» бесплатно N/день.

«Дотянуть 1 карту» (−1 запрос) → быстрый follow-up.

Предложения пресетов (Карьера/Отношения/Деньги).

Коллекции/ачивки (7 разных спредов → +1 запрос).

Реферал через шаринг картинки (тонкий watermark + UTM).

8) База данных (DDL — создать таблицы)

Создать таблицы (минимум):

users(id BIGSERIAL PK, tg_id BIGINT UNIQUE, username TEXT, locale TEXT, created_at TIMESTAMPTZ, last_seen TIMESTAMPTZ)

profiles(user_id FK, name_raw TEXT, name_norm TEXT, dob_date DATE, birth_time TIME NULL, birth_place TEXT, tz TEXT, consent_at TIMESTAMPTZ)

orders(id BIGSERIAL PK, user_id FK, product TEXT, amount_xtr INT, currency TEXT, status TEXT, external_id TEXT, created_at TIMESTAMPTZ)

entitlements(id BIGSERIAL PK, user_id FK, product TEXT, status TEXT, expires_at TIMESTAMPTZ NULL, quota_total INT, quota_left INT, fair_daily_cap INT, created_at TIMESTAMPTZ)

usages(id BIGSERIAL PK, user_id FK, expert TEXT, cost INT, created_at TIMESTAMPTZ)

decks(id BIGSERIAL PK, type TEXT, name_json JSONB, config_json JSONB, created_at TIMESTAMPTZ)

draws(id BIGSERIAL PK, user_id FK, expert TEXT, deck_id TEXT, spread_id TEXT, seed TEXT, facts_json JSONB, image_url TEXT, created_at TIMESTAMPTZ)

readings(id BIGSERIAL PK, user_id FK, expert TEXT, input_json JSONB, facts_json JSONB, text_md TEXT, pdf_url TEXT, images_json JSONB, created_at TIMESTAMPTZ)

events(id BIGSERIAL PK, user_id FK, event TEXT, props_json JSONB, ts TIMESTAMPTZ)

Индексы: users(tg_id), entitlements(user_id,status), draws(user_id,created_at DESC), events(ts,event).

9) NLP-контракты (строго JSON)
9.1 Guide

Input: {expert, step, locale} → Output: {tip} (≤ 200 симв.)

9.2 Writer

Input: {facts, locale, tone, user_goal}
Output (strict):

{
  "tldr": "string <= 280",
  "sections": [ {"title": "string", "body_md":"string"} ],
  "actions": ["Шаг 1 ...", "Шаг 2 ...", "Шаг 3 ..."],
  "disclaimers": ["string", "..."]
}

9.3 Verifier

Input: {facts, markdown} → Output: {ok: boolean, diffs: [{path, expected, found}]}
Несоответствие → автоперегенерация; 2 неудачи → fallback-ответ (без списания).

10) PDF/экспорт

HTML (Jinja2) → PDF (WeasyPrint/Chromium).

Ограничение: ≤ 10 МБ.

Сохранение в S3, presigned URLs.

11) Админ

/admin/metrics (read-only JSON): MAU/DAU, конверсии по экспертам/продуктам, баланс Stars, активные безлимиты, среднее время генерации, процент Verifier-fail.

/admin/decks — список колод (проверка валидности ассетов).

/admin/broadcast — (опц.) рассылка по сегментам.

12) Нефункциональные требования

p95 генерации: ≤ 8 сек (без тяжелых чартов), ≤ 15 сек (чарты/астро).

Ошибкоустойчивость: ретраи LLM, DLQ для задач, идемпотентность отправок в Telegram.

Безопасность: PII-шифрование, маскирование в логах, секреты только из ENV.

13) Тесты и приёмка (DoD)

Unit/Component

Ингестер ассетов: строгая валидация манифестов/файлов.

Draw: воспроизводимость по seed; уникальность/реверсы; все спрэды.

Compose: корректные сетки (1/3/5/7/10/3×3/GT/крест), подписи, вес файла.

Numerology: golden-наборы чисел (Life Path, Expression, Soul Urge, Personality, Birthday, Maturity, PY/PM/PD, Pinnacles/Challenges).

Astrology: корректные позиции/аспекты для тестовых дат.

Dreams: извлечение символов из лексикона.

Writer/Verifier: strict JSON, 0 «выдуманных» фактов.

E2E

Полный флоу каждого эксперта (форма → картинка → текст).

Stars: invoice → pre_checkout → successful_payment → entitlement → списание.

Лимиты: пакет/безлимит; fair-use; анти-флуд; параллелизм ≤ 2.

История: отображение, повтор, «дотянуть».

Телеметрия: фаннел /start → form_completed → paid → answer_sent заполнен.

Документация

README (деплой), .env.sample, FAQ по ассетам (как положить колоду/руны/лексикон/алфавиты), runbook инцидентов.

14) Требования к Codex (жёстко)

Сделать все модули экспертов, перечисленные спрэды и визуалы целиком.

Никаких «примеров», «TODO» или «заглушек». Все кнопки и экраны — рабочие.

Строгие JSON-контракты в NLP, Verifier — обязателен; ошибки — авторегенерация.

Полная витрина тарифов и реальная обработка Stars (XTR) с учётом квот.

Asset pipeline: валиден для ручного наполнения (ты кладёшь картинки и deck.json — всё работает).

RU/EN локализация из коробки.

Метрики и админ-срезы присутствуют.

Код — промышленного уровня качества (типизация, тесты, покрытие, миграции, логирование).

Приложение A: Готовые идентификаторы спрэдов (для registry)

Tarot:

tarot_one_daily, tarot_three_ppf, tarot_three_decision, tarot_five_solution,
tarot_celtic_cross_10, tarot_relationship_7, tarot_career_7, tarot_yes_no_3.

Lenormand:

leno_three_line, leno_five_line, leno_nine_square, leno_grand_tableau_36.

Runes:

runes_one, runes_three_ppf, runes_five_cross.

Приложение B: Правила seed/nonce
seed = SHA256( str(user_id) + "|" + expert + "|" + spread_id + "|" + YYYYMMDD + "|" + nonce )
nonce = 0 для первого вытяга; +1 при «Перетянуть»/«Дотянуть»

Приложение C: Словарь CTA (минимум)

«Дотянуть 1 карту» (–1 запрос)

«Сделать другой спред»

«Уточнить вопрос»

«PDF» | «Сохранить» | «Поделиться»

«Перейти к [другому эксперту]» (крест-промо)

«Пополнить квоту» (витрина тарифов)
