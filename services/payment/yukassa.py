from __future__ import annotations
import uuid
from yookassa import Configuration, Payment
from core.config import settings
from core.logger import logger


class YukassaService:
    """
    Сервис оплаты через ЮКассу.
    Создаём платёж → отдаём юзеру ссылку → ждём webhook.
    """

    def __init__(self):
        Configuration.account_id = settings.YUKASSA_SHOP_ID
        Configuration.secret_key = settings.YUKASSA_SECRET_KEY

    def create_payment(
        self,
        amount: float,
        description: str,
        user_id: int,
        tokens: int,
        plan: str | None = None,
    ) -> tuple[str, str]:
        """
        Создаёт платёж.
        Возвращает (payment_id, confirmation_url).
        """
        idempotence_key = str(uuid.uuid4())

        metadata: dict = {"user_id": user_id, "tokens": tokens}
        if plan:
            metadata["plan"] = plan

        payment = Payment.create(
            {
                "amount": {
                    "value": f"{amount:.2f}",
                    "currency": "RUB",
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": f"https://t.me/{settings.BOT_USERNAME}",
                },
                "capture": True,
                "description": description,
                "metadata": metadata,
            },
            idempotence_key,
        )

        payment_id = payment.id or ""
        confirmation_url = (
            payment.confirmation.confirmation_url if payment.confirmation else ""
        )

        logger.info(f"Создан платёж {payment_id} для юзера {user_id}")
        return payment_id, confirmation_url

    def check_payment(self, payment_id: str) -> str:
        """
        Проверяет статус платежа.
        Возвращает: pending, succeeded, canceled.
        """
        payment = Payment.find_one(payment_id)
        return payment.status or ""

    def parse_webhook(self, data: dict) -> tuple[str, int, int] | None:
        """
        Парсит входящий webhook от ЮКассы.
        Возвращает (payment_id, user_id, tokens) или None.
        """
        try:
            if data.get("event") != "payment.succeeded":
                return None

            payment_obj = data["object"]
            payment_id = payment_obj["id"]
            metadata = payment_obj.get("metadata", {})
            user_id = int(metadata["user_id"])
            tokens = int(metadata["tokens"])

            return payment_id, user_id, tokens
        except (KeyError, ValueError) as e:
            logger.error(f"Ошибка парсинга webhook: {e}")
            return None
