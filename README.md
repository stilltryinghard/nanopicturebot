# 🎨 NanoPicture Bot

Telegram-бот для генерации изображений с помощью AI-моделей. Поддерживает несколько моделей генерации, систему токенов, подписки, реферальную программу и оплату через ЮКассу.

## Стек

- **Python 3.11** / aiogram 3.7
- **PostgreSQL** + SQLAlchemy 2.0 (async) + Alembic
- **Redis** — кеш, очереди задач
- **Celery** — фоновые задачи (генерация, уведомления)
- **FastAPI** — webhook для ЮКассы
- **Docker** / Docker Compose

## AI-модели

| Модель | Провайдер | API |
|--------|-----------|-----|
| Nano Banana | Google (Gemini) | WaveSpeed AI |
| Seedream | ByteDance | WaveSpeed AI |
| Midjourney | Midjourney | midapi.ai |

## Структура проекта
```
├── bot/
│   ├── handlers/        # Обработчики команд (start, generate, balance, admin, referral)
│   ├── keyboards/       # Inline и Reply клавиатуры
│   └── middlewares/     # Auth, throttling
├── db/
│   ├── models/          # SQLAlchemy модели (User, Generation, Transaction, Subscription, Referral)
│   ├── repositories/    # Репозитории для работы с БД
│   └── session.py       # Async сессия
├── services/
│   ├── ai/              # AI сервисы (NanoBanana, Seedream, Midjourney)
│   ├── payment/         # ЮКасса
│   └── settings_service.py  # Динамические настройки через Redis
├── webhook/             # FastAPI webhook для ЮКассы
├── workers/             # Celery задачи и beat-расписание
├── migrations/          # Alembic миграции
└── core/                # Config, logger, i18n
```

## Быстрый старт

### 1. Клонировать репозиторий
```bash
git clone https://github.com/username/chatbot_tg.git
cd chatbot_tg
```

### 2. Создать `.env`
```env
BOT_TOKEN=your_bot_token
ADMIN_IDS=[123456789]

DB_HOST=db
DB_PORT=5432
DB_NAME=ai_bot_db
DB_USER=ai_bot_user
DB_PASSWORD=your_password

REDIS_URL=redis://redis:6379/0

WAVESPEED_API_KEY=your_wavespeed_key
MIDJOURNEY_API_KEY=your_midjourney_key

YUKASSA_SHOP_ID=your_shop_id
YUKASSA_SECRET_KEY=your_secret_key

TOKENS_2K=10
TOKENS_4K=20
REFERRAL_BONUS_TOKENS=50
```

### 3. Запустить
```bash
docker compose up --build -d
```

## Функционал

- Генерация изображений через 3 AI-модели
- Система токенов — тратятся на генерацию
- Подписки (basic, standard, pro)
- Реферальная программа — бонус за приглашённых
- Оплата через ЮКассу (webhook)
- Уведомление о низком балансе токенов
- Админ-панель: статистика, управление пользователями, тарифы, рассылка

## Деплой
```bash
# Первый деплой
docker compose up --build -d

# Применить миграции
docker compose run --rm migrate

# Обновление
rsync -avz --exclude='.git' --exclude='__pycache__' --exclude='venv' ./ user@server:~/chatbot_tg/
docker compose up --build -d
```
