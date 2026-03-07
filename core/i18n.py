from __future__ import annotations

TEXTS: dict[str, dict[str, str]] = {
    # ── Onboarding ──────────────────────────────────────────────────────────
    "choose_language": {
        "default": "🌍 <b>Choose language / Выберите язык:</b>",
    },
    "terms_text": {
        "ru": (
            "📋 <b>Пользовательское соглашение и политика конфиденциальности</b>\n\n"
            "Для использования бота необходимо ознакомиться с документами "
            "и принять их условия."
        ),
        "en": (
            "📋 <b>Terms of Service and Privacy Policy</b>\n\n"
            "To use the bot you must read and accept the documents below.\n"
            "<i>(Documents are available in Russian only.)</i>"
        ),
    },
    "terms_accept_btn": {"ru": "✅ Принять", "en": "✅ Accept"},
    "terms_decline_btn": {"ru": "❌ Отклонить", "en": "❌ Decline"},
    "read_terms_btn": {
        "ru": "📄 Пользовательское соглашение",
        "en": "📄 Terms of Service",
    },
    "read_privacy_btn": {
        "ru": "📄 Политика конфиденциальности",
        "en": "📄 Privacy Policy",
    },
    "terms_declined": {
        "ru": (
            "😔 <b>Без принятия соглашения воспользоваться ботом невозможно.</b>\n\n"
            "Если передумаешь — нажми /start."
        ),
        "en": (
            "😔 <b>You cannot use the bot without accepting the terms.</b>\n\n"
            "If you change your mind — press /start."
        ),
    },
    "not_onboarded": {
        "ru": "👋 Нажми /start чтобы начать.",
        "en": "👋 Press /start to begin.",
    },
    # ── Main menu ────────────────────────────────────────────────────────────
    "welcome": {
        "ru": (
            "Привет! Ты в <b>Zuma AI Studio</b>\n\n"
            "Здесь твои идеи становятся изображениями. Просто опиши что хочешь — и ИИ создаст это за секунды.\n\n"
            "Выбирай стиль, задавай детали и получай результат.\n\n"
            "💰 <b>Ваш баланс:</b> {tokens} токенов\n\n"
            "Выбери раздел 👇"
        ),
        "en": (
            "Hi! You're in <b>Zuma AI Studio</b>\n\n"
            "Here your ideas become images. Just describe what you want — and AI will create it in seconds.\n\n"
            "Choose a style, set the details and get your result.\n\n"
            "💰 <b>Your balance:</b> {tokens} tokens\n\n"
            "Choose a section 👇"
        ),
    },
    "menu_generate": {"ru": "🎨 Генерация изображений", "en": "🎨 Generate images"},
    "menu_balance": {"ru": "💰 Баланс и пополнение", "en": "💰 Balance & top-up"},
    "menu_sub": {"ru": "👑 Подписка", "en": "👑 Subscription"},
    "menu_referral": {"ru": "🔗 Реферальная программа", "en": "🔗 Referral program"},
    "menu_help": {"ru": "ℹ️ Помощь", "en": "ℹ️ Help"},
    "menu_admin": {"ru": "⚙️ Админ-панель", "en": "⚙️ Admin panel"},
    "menu_language": {"ru": "🌍 Язык", "en": "🌍 Language"},
    "language_select_title": {
        "ru": "🌍 <b>Выбери язык:</b>",
        "en": "🌍 <b>Choose language:</b>",
    },
    "btn_back": {"ru": "🏠 Главное меню", "en": "🏠 Main menu"},
    "btn_nav_back": {"ru": "◀️ Назад", "en": "◀️ Back"},
    # ── Generate flow ────────────────────────────────────────────────────────
    "gen_choose_model": {
        "ru": "🎨 <b>Генерация изображений</b>\n\nВыбери нейросеть для генерации:",
        "en": "🎨 <b>Image Generation</b>\n\nChoose an AI model:",
    },
    "gen_model_selected": {
        "ru": "✅ Выбрана модель: <b>{model}</b>\n\n✏️ Введи промт — опиши что хочешь сгенерировать:\n\n<i>Пример: красивый закат над горами, фотореализм</i>",
        "en": "✅ Model selected: <b>{model}</b>\n\n✏️ Enter a prompt — describe what you want to generate:\n\n<i>Example: beautiful sunset over mountains, photorealism</i>",
    },
    "gen_prompt_error": {
        "ru": "❌ Введи текстовый промт.",
        "en": "❌ Please enter a text prompt.",
    },
    "gen_preference": {
        "ru": "🎛 <b>Преференс</b> (необязательно)\n\nВведи дополнительные параметры стиля:\n<i>Пример: cinematic, 4k, dramatic lighting</i>\n\nИли пропусти этот шаг:",
        "en": "🎛 <b>Preference</b> (optional)\n\nEnter additional style parameters:\n<i>Example: cinematic, 4k, dramatic lighting</i>\n\nOr skip this step:",
    },
    "gen_choose_quality": {
        "ru": "🖼 <b>Выбери качество изображения:</b>",
        "en": "🖼 <b>Choose image quality:</b>",
    },
    "gen_choose_count": {
        "ru": "🔢 <b>Сколько изображений сгенерировать?</b>",
        "en": "🔢 <b>How many images to generate?</b>",
    },
    "gen_insufficient_tokens": {
        "ru": "❌ <b>Недостаточно токенов</b>\n\nНужно: {cost} токенов\nУ вас: {balance} токенов\n\nПополни баланс и попробуй снова.",
        "en": "❌ <b>Not enough tokens</b>\n\nRequired: {cost} tokens\nYou have: {balance} tokens\n\nTop up your balance and try again.",
    },
    "gen_cost_free": {
        "ru": "💰 Стоимость: <b>бесплатно (админ)</b>",
        "en": "💰 Cost: <b>free (admin)</b>",
    },
    "gen_cost": {
        "ru": "💰 Стоимость: <b>{cost} токенов</b>\n💳 Ваш баланс: <b>{balance} токенов</b>",
        "en": "💰 Cost: <b>{cost} tokens</b>\n💳 Your balance: <b>{balance} tokens</b>",
    },
    "gen_preference_none": {"ru": "не указан", "en": "not specified"},
    "gen_confirm": {
        "ru": "📋 <b>Подтверди генерацию:</b>\n\n🤖 Модель: <b>{model}</b>\n✏️ Промт: <i>{prompt}</i>\n🎛 Преференс: <i>{preference}</i>\n🖼 Качество: <b>{quality}</b>\n🔢 Количество: <b>{count}</b>\n{cost_line}",
        "en": "📋 <b>Confirm generation:</b>\n\n🤖 Model: <b>{model}</b>\n✏️ Prompt: <i>{prompt}</i>\n🎛 Preference: <i>{preference}</i>\n🖼 Quality: <b>{quality}</b>\n🔢 Count: <b>{count}</b>\n{cost_line}",
    },
    "gen_started": {
        "ru": "⏳ <b>Генерация запущена!</b>\n\nИзображения придут сюда как только будут готовы.\nОбычно это занимает 30-60 секунд.",
        "en": "⏳ <b>Generation started!</b>\n\nImages will arrive here once ready.\nThis usually takes 30-60 seconds.",
    },
    "gen_kb_skip": {"ru": "⏭ Пропустить", "en": "⏭ Skip"},
    "gen_kb_cancel": {"ru": "❌ Отмена", "en": "❌ Cancel"},
    "gen_kb_confirm": {
        "ru": "✅ Подтвердить ({cost} токенов)",
        "en": "✅ Confirm ({cost} tokens)",
    },
    # ── Balance flow ─────────────────────────────────────────────────────────
    "bal_no_sub": {"ru": "❌ Нет подписки", "en": "❌ No subscription"},
    "bal_sub_active": {"ru": "✅ {plan} до {date}", "en": "✅ {plan} until {date}"},
    "bal_title": {
        "ru": "💰 <b>Баланс и оплата</b>\n\n💳 <b>Токены:</b> {tokens}\n👑 <b>Подписка:</b> {sub_text}\n\nВыбери действие:",
        "en": "💰 <b>Balance & Payment</b>\n\n💳 <b>Tokens:</b> {tokens}\n👑 <b>Subscription:</b> {sub_text}\n\nChoose an action:",
    },
    "bal_buy_tokens_title": {
        "ru": "💳 <b>Покупка токенов</b>\n\nВыбери пакет:",
        "en": "💳 <b>Buy Tokens</b>\n\nChoose a package:",
    },
    "bal_tokens_added": {
        "ru": "✅ <b>Токены зачислены!</b>\n\nНачислено: <b>{tokens} токенов</b>\nСумма: <b>{amount}₽</b>",
        "en": "✅ <b>Tokens added!</b>\n\nAdded: <b>{tokens} tokens</b>\nAmount: <b>{amount}₽</b>",
    },
    "bal_sub_title": {
        "ru": "👑 <b>Подписка</b>\n\n<b>Преимущества подписки:</b>\n• Приоритет в очереди генерации\n• Бонусные токены каждый месяц\n• Скидка на пакеты токенов\n\nВыбери тариф:",
        "en": "👑 <b>Subscription</b>\n\n<b>Subscription benefits:</b>\n• Priority in the generation queue\n• Bonus tokens every month\n• Discount on token packages\n\nChoose a plan:",
    },
    "bal_sub_activated": {
        "ru": "✅ <b>Подписка активирована!</b>\n\nТариф: <b>{plan}</b>\nДействует: <b>30 дней</b>\nСумма: <b>{amount}₽</b>",
        "en": "✅ <b>Subscription activated!</b>\n\nPlan: <b>{plan}</b>\nValid for: <b>30 days</b>\nAmount: <b>{amount}₽</b>",
    },
    "bal_kb_buy_tokens": {"ru": "💳 Купить токены", "en": "💳 Buy tokens"},
    "bal_kb_buy_sub": {"ru": "👑 Купить подписку", "en": "👑 Buy subscription"},
    "bal_kb_token_label": {
        "ru": "💎 {tokens} токенов — {amount}₽",
        "en": "💎 {tokens} tokens — {amount}₽",
    },
    "bal_kb_per_month": {"ru": "/мес", "en": "/mo"},
    "bal_kb_pay": {"ru": "💳 Оплатить", "en": "💳 Pay"},
}


def t(key: str, lang: str | None, **kwargs: str) -> str:
    """Return translated string for the given key and language code."""
    bucket = TEXTS.get(key, {})
    text = bucket.get(lang or "ru") or bucket.get("ru") or bucket.get("default") or key
    if kwargs:
        text = text.format(**kwargs)
    return text
