from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from webhook.app import app

# ---------- хелперы ----------


def _event(payment_id: str = "pay_001", metadata: dict | None = None) -> dict:
    """Тело вебхука. metadata можно подделать — вебхук не должен ей верить."""
    return {
        "event": "payment.succeeded",
        "object": {"id": payment_id, "metadata": metadata or {}},
    }


def _payment(status: str = "succeeded", paid: bool = True, value: str = "99.00") -> dict:
    """Ответ API ЮКассы на GET /payments/{id}."""
    return {
        "status": status,
        "paid": paid,
        "amount": {"value": value, "currency": "RUB"},
    }


def _tx(
    type_: str = "purchase",
    tokens: int = 100,
    amount: float = 99.0,
    status: str = "pending",
    user_id: int = 111,
) -> SimpleNamespace:
    """Транзакция из нашей базы — единственный источник правды о начислении."""
    return SimpleNamespace(
        type=type_, tokens=tokens, amount=amount, status=status, user_id=user_id
    )


# ---------- фикстуры ----------


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.fixture
def repos():
    """Подменяем сессию, репозитории и уведомление там, где их использует вебхук."""
    session = AsyncMock()
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=session)
    ctx.__aexit__ = AsyncMock(return_value=False)

    trans_repo = AsyncMock()
    user_repo = AsyncMock()
    sub_repo = AsyncMock()

    with (
        patch("webhook.app.async_session_maker", return_value=ctx),
        patch("webhook.app.TransactionRepository", return_value=trans_repo),
        patch("webhook.app.UserRepository", return_value=user_repo),
        patch("webhook.app.SubscriptionRepository", return_value=sub_repo),
        patch("webhook.app.notify_user", new=AsyncMock()) as notify,
    ):
        yield SimpleNamespace(trans=trans_repo, user=user_repo, sub=sub_repo, notify=notify)


def _fetch_returns(value):
    return patch("webhook.app.fetch_payment", new=AsyncMock(return_value=value))


# ---------- тесты ----------


async def test_non_payment_event_ignored(client):
    resp = await client.post(
        "/webhook/yukassa", json={"event": "payment.canceled", "object": {}}
    )
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_token_purchase_credits_from_transaction_not_metadata(client, repos):
    # В metadata — попытка накрутить миллион токенов
    tx = _tx(tokens=100, amount=99.0)
    repos.trans.get_by_payment_id.return_value = tx
    repos.trans.mark_success_if_pending.return_value = tx

    with _fetch_returns(_payment(value="99.00")):
        resp = await client.post(
            "/webhook/yukassa",
            json=_event("pay_tok", metadata={"user_id": "666", "tokens": "1000000"}),
        )

    assert resp.status_code == 200
    # Начислено по транзакции: юзер 111, 100 токенов
    repos.user.update_tokens.assert_called_once_with(111, amount=100)
    repos.trans.mark_success_if_pending.assert_called_once_with("pay_tok")
    repos.notify.assert_called_once_with(111, None, 100)


async def test_subscription_activates_plan_from_transaction_type(client, repos):
    tx = _tx(type_="subscription_pro", tokens=0, amount=999.0, user_id=222)
    repos.trans.get_by_payment_id.return_value = tx
    repos.trans.mark_success_if_pending.return_value = tx

    with _fetch_returns(_payment(value="999.00")):
        resp = await client.post("/webhook/yukassa", json=_event("pay_sub"))

    assert resp.status_code == 200
    repos.sub.upsert.assert_called_once()
    kwargs = repos.sub.upsert.call_args.kwargs
    assert kwargs["plan"] == "pro"
    assert kwargs["user_id"] == 222
    repos.user.update_tokens.assert_not_called()
    repos.trans.mark_success_if_pending.assert_called_once_with("pay_sub")


async def test_fake_payment_not_found_in_yukassa(client, repos):
    with _fetch_returns(None):
        resp = await client.post("/webhook/yukassa", json=_event("pay_fake"))

    assert resp.status_code == 200
    repos.user.update_tokens.assert_not_called()
    repos.sub.upsert.assert_not_called()


async def test_payment_not_succeeded_in_yukassa(client, repos):
    # Тело говорит succeeded, а API — pending: верим API
    with _fetch_returns(_payment(status="pending", paid=False)):
        resp = await client.post("/webhook/yukassa", json=_event("pay_pending"))

    assert resp.status_code == 200
    repos.user.update_tokens.assert_not_called()


async def test_unknown_transaction_ignored(client, repos):
    repos.trans.get_by_payment_id.return_value = None

    with _fetch_returns(_payment()):
        resp = await client.post("/webhook/yukassa", json=_event("pay_unknown"))

    assert resp.status_code == 200
    repos.user.update_tokens.assert_not_called()


async def test_duplicate_payment_ignored(client, repos):
    repos.trans.get_by_payment_id.return_value = _tx(status="success")

    with _fetch_returns(_payment()):
        resp = await client.post("/webhook/yukassa", json=_event("pay_dup"))

    assert resp.status_code == 200
    repos.user.update_tokens.assert_not_called()
    repos.trans.mark_success_if_pending.assert_not_called()


async def test_amount_mismatch_ignored(client, repos):
    # Выставили 99, а оплачено 1 — не начисляем
    repos.trans.get_by_payment_id.return_value = _tx(amount=99.0)

    with _fetch_returns(_payment(value="1.00")):
        resp = await client.post("/webhook/yukassa", json=_event("pay_cheap"))

    assert resp.status_code == 200
    repos.user.update_tokens.assert_not_called()
    repos.trans.mark_success_if_pending.assert_not_called()


async def test_yukassa_unavailable_returns_503(client, repos):
    # 5xx — сигнал ЮКассе повторить уведомление позже
    failing = AsyncMock(side_effect=httpx.ConnectError("boom"))
    with patch("webhook.app.fetch_payment", new=failing):
        resp = await client.post("/webhook/yukassa", json=_event("pay_down"))

    assert resp.status_code == 503
    repos.user.update_tokens.assert_not_called()


async def test_notify_failure_does_not_break_webhook(client, repos):
    tx = _tx()
    repos.trans.get_by_payment_id.return_value = tx
    repos.trans.mark_success_if_pending.return_value = tx
    repos.notify.side_effect = RuntimeError("telegram is down")

    with _fetch_returns(_payment()):
        resp = await client.post("/webhook/yukassa", json=_event("pay_notify"))

    # Деньги зачислены, падение уведомления не роняет ответ
    assert resp.status_code == 200
    repos.user.update_tokens.assert_called_once()


async def test_parallel_duplicate_loses_race(client, repos):
    # Оба запроса прочитали pending, но UPDATE выиграл другой: этот не начисляет
    repos.trans.get_by_payment_id.return_value = _tx(status="pending")
    repos.trans.mark_success_if_pending.return_value = None

    with _fetch_returns(_payment()):
        resp = await client.post("/webhook/yukassa", json=_event("pay_race"))

    assert resp.status_code == 200
    repos.user.update_tokens.assert_not_called()
    repos.sub.upsert.assert_not_called()
    repos.notify.assert_not_called()