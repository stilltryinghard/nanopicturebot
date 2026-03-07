from __future__ import annotations
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from webhook.app import app


def _payment_event(
    user_id: int, tokens: int, plan: str | None = None, payment_id: str = "pay_001"
):
    metadata = {"user_id": str(user_id), "tokens": str(tokens)}
    if plan:
        metadata["plan"] = plan
    return {
        "event": "payment.succeeded",
        "object": {
            "id": payment_id,
            "metadata": metadata,
        },
    }


@pytest.fixture
def mock_session_ctx():
    session = AsyncMock()
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=session)
    ctx.__aexit__ = AsyncMock(return_value=False)
    return ctx, session


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def test_non_payment_event_ignored(client):
    resp = await client.post(
        "/webhook/yukassa", json={"event": "payment.canceled", "object": {}}
    )
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_missing_user_id_ignored(client, mock_session_ctx):
    ctx, session = mock_session_ctx
    trans_repo = AsyncMock()
    trans_repo.get_by_payment_id = AsyncMock(return_value=None)

    # Вебхук делает lazy import внутри функции, патчим источники
    with (
        patch("db.session.async_session_maker", return_value=ctx),
        patch(
            "db.repositories.transaction.TransactionRepository", return_value=trans_repo
        ),
    ):
        resp = await client.post(
            "/webhook/yukassa",
            json={
                "event": "payment.succeeded",
                "object": {"id": "pay_x", "metadata": {"tokens": "100"}},
            },
        )

    assert resp.status_code == 200


async def test_token_purchase_credits_tokens(client, mock_session_ctx):
    ctx, _ = mock_session_ctx

    trans_repo = AsyncMock()
    trans_repo.get_by_payment_id = AsyncMock(return_value=None)
    trans_repo.update_status = AsyncMock()

    user_repo = AsyncMock()
    user_repo.update_tokens = AsyncMock()

    mock_bot = AsyncMock()
    mock_bot.send_message = AsyncMock()

    with (
        patch("db.session.async_session_maker", return_value=ctx),
        patch(
            "db.repositories.transaction.TransactionRepository", return_value=trans_repo
        ),
        patch("db.repositories.user.UserRepository", return_value=user_repo),
        patch(
            "db.repositories.subscription.SubscriptionRepository",
            return_value=AsyncMock(),
        ),
        patch("aiogram.Bot") as MockBot,
    ):
        MockBot.return_value.__aenter__ = AsyncMock(return_value=mock_bot)
        MockBot.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await client.post(
            "/webhook/yukassa",
            json=_payment_event(user_id=111, tokens=100, payment_id="pay_tok"),
        )

    assert resp.status_code == 200
    user_repo.update_tokens.assert_called_once_with(111, amount=100)
    trans_repo.update_status.assert_called_once_with("pay_tok", "success")


async def test_subscription_activates_plan(client, mock_session_ctx):
    ctx, _ = mock_session_ctx

    trans_repo = AsyncMock()
    trans_repo.get_by_payment_id = AsyncMock(return_value=None)
    trans_repo.update_status = AsyncMock()

    user_repo = AsyncMock()
    sub_repo = AsyncMock()
    sub_repo.create = AsyncMock()

    mock_bot = AsyncMock()
    mock_bot.send_message = AsyncMock()

    with (
        patch("db.session.async_session_maker", return_value=ctx),
        patch(
            "db.repositories.transaction.TransactionRepository", return_value=trans_repo
        ),
        patch("db.repositories.user.UserRepository", return_value=user_repo),
        patch(
            "db.repositories.subscription.SubscriptionRepository", return_value=sub_repo
        ),
        patch("aiogram.Bot") as MockBot,
    ):
        MockBot.return_value.__aenter__ = AsyncMock(return_value=mock_bot)
        MockBot.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await client.post(
            "/webhook/yukassa",
            json=_payment_event(
                user_id=222, tokens=0, plan="pro", payment_id="pay_sub"
            ),
        )

    assert resp.status_code == 200
    sub_repo.create.assert_called_once()
    call_kwargs = sub_repo.create.call_args.kwargs
    assert call_kwargs["plan"] == "pro"
    assert call_kwargs["user_id"] == 222
    user_repo.update_tokens.assert_not_called()


async def test_duplicate_payment_ignored(client, mock_session_ctx):
    ctx, _ = mock_session_ctx

    existing_tx = MagicMock()
    existing_tx.status = "success"

    trans_repo = AsyncMock()
    trans_repo.get_by_payment_id = AsyncMock(return_value=existing_tx)

    user_repo = AsyncMock()

    with (
        patch("db.session.async_session_maker", return_value=ctx),
        patch(
            "db.repositories.transaction.TransactionRepository", return_value=trans_repo
        ),
        patch("db.repositories.user.UserRepository", return_value=user_repo),
    ):
        resp = await client.post(
            "/webhook/yukassa",
            json=_payment_event(user_id=333, tokens=100, payment_id="pay_dup"),
        )

    assert resp.status_code == 200
    user_repo.update_tokens.assert_not_called()
