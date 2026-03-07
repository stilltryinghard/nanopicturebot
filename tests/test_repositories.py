from __future__ import annotations
from datetime import datetime, timedelta
from db.repositories.user import UserRepository
from db.repositories.generation import GenerationRepository
from db.repositories.transaction import TransactionRepository
from db.repositories.subscription import SubscriptionRepository


# ─── UserRepository ───────────────────────────────────────────────────────────


class TestUserRepository:
    async def test_create_user(self, db_session):
        repo = UserRepository(db_session)
        user = await repo.create(user_id=1, username="alice", full_name="Alice")
        assert user.id == 1
        assert user.username == "alice"
        assert user.tokens == 0
        assert user.is_blocked is False

    async def test_get_by_id_found(self, db_session):
        repo = UserRepository(db_session)
        await repo.create(user_id=2, username="bob", full_name="Bob")
        user = await repo.get_by_id(2)
        assert user is not None
        assert user.username == "bob"

    async def test_get_by_id_not_found(self, db_session):
        repo = UserRepository(db_session)
        user = await repo.get_by_id(999)
        assert user is None

    async def test_get_or_create_new(self, db_session):
        repo = UserRepository(db_session)
        user, is_new = await repo.get_or_create(
            user_id=3, username="carol", full_name="Carol"
        )
        assert is_new is True
        assert user.id == 3

    async def test_get_or_create_existing(self, db_session):
        repo = UserRepository(db_session)
        await repo.create(user_id=4, username="dave", full_name="Dave")
        user, is_new = await repo.get_or_create(
            user_id=4, username="dave", full_name="Dave"
        )
        assert is_new is False

    async def test_update_tokens_add(self, db_session, user):
        repo = UserRepository(db_session)
        await repo.update_tokens(user.id, amount=100)
        updated = await repo.get_by_id(user.id)
        assert updated.tokens == 100

    async def test_update_tokens_subtract(self, db_session, user):
        repo = UserRepository(db_session)
        await repo.update_tokens(user.id, amount=50)
        await repo.update_tokens(user.id, amount=-20)
        updated = await repo.get_by_id(user.id)
        assert updated.tokens == 30

    async def test_block_user(self, db_session, user):
        repo = UserRepository(db_session)
        await repo.block(user.id, blocked=True)
        updated = await repo.get_by_id(user.id)
        assert updated.is_blocked is True

    async def test_unblock_user(self, db_session, user):
        repo = UserRepository(db_session)
        await repo.block(user.id, blocked=True)
        await repo.block(user.id, blocked=False)
        updated = await repo.get_by_id(user.id)
        assert updated.is_blocked is False

    async def test_get_all(self, db_session):
        repo = UserRepository(db_session)
        await repo.create(user_id=10, username="u1", full_name="U1")
        await repo.create(user_id=11, username="u2", full_name="U2")
        all_users = await repo.get_all()
        ids = [u.id for u in all_users]
        assert 10 in ids
        assert 11 in ids

    async def test_get_by_username(self, db_session):
        repo = UserRepository(db_session)
        await repo.create(user_id=20, username="findme", full_name="Find Me")
        user = await repo.get_by_username("findme")
        assert user is not None
        assert user.id == 20

    async def test_get_by_username_with_at(self, db_session):
        repo = UserRepository(db_session)
        await repo.create(user_id=21, username="findme2", full_name="Find Me 2")
        user = await repo.get_by_username("@findme2")
        assert user is not None

    async def test_get_by_username_not_found(self, db_session):
        repo = UserRepository(db_session)
        user = await repo.get_by_username("nobody")
        assert user is None

    async def test_referral_count(self, db_session, user):
        repo = UserRepository(db_session)
        await repo.update_referral_count(user.id)
        await repo.update_referral_count(user.id)
        updated = await repo.get_by_id(user.id)
        assert updated.referral_count == 2

    async def test_get_low_balance_users_filters_correctly(self, db_session):
        repo = UserRepository(db_session)
        rich = await repo.create(user_id=301, username="rich", full_name="Rich")
        poor = await repo.create(user_id=302, username="poor", full_name="Poor")
        blocked = await repo.create(
            user_id=303, username="blocked", full_name="Blocked"
        )

        await repo.update_tokens(rich.id, amount=500)
        await repo.update_tokens(poor.id, amount=10)
        await repo.update_tokens(blocked.id, amount=5)
        await repo.block(blocked.id, blocked=True)

        result = await repo.get_low_balance_users(threshold=20)
        ids = [u.id for u in result]
        assert poor.id in ids
        assert rich.id not in ids
        assert blocked.id not in ids  # заблокированные не включаются

    async def test_get_low_balance_users_pagination(self, db_session):
        repo = UserRepository(db_session)
        for i in range(5):
            u = await repo.create(
                user_id=400 + i, username=f"lb{i}", full_name=f"LB{i}"
            )
            await repo.update_tokens(u.id, amount=5)

        page1 = await repo.get_low_balance_users(threshold=20, limit=3, offset=0)
        page2 = await repo.get_low_balance_users(threshold=20, limit=3, offset=3)
        all_ids = [u.id for u in page1] + [u.id for u in page2]
        assert len(page1) == 3
        assert len(page2) == 2
        assert len(set(all_ids)) == 5  # нет дублей


# ─── GenerationRepository ─────────────────────────────────────────────────────


class TestGenerationRepository:
    async def test_create_generation(self, db_session, user):
        repo = GenerationRepository(db_session)
        gen = await repo.create(
            user_id=user.id,
            model="nano_banana",
            prompt="a cat",
            quality="2K",
            count=1,
            tokens_spent=10,
        )
        assert gen.id is not None
        assert gen.status == "pending"
        assert gen.model == "nano_banana"

    async def test_update_status_done(self, db_session, user):
        repo = GenerationRepository(db_session)
        gen = await repo.create(
            user_id=user.id,
            model="seedream",
            prompt="p",
            quality="2K",
            count=1,
            tokens_spent=5,
        )
        await repo.update_status(gen.id, "done")
        updated = await repo.get_by_id(gen.id)
        assert updated.status == "done"

    async def test_update_status_failed(self, db_session, user):
        repo = GenerationRepository(db_session)
        gen = await repo.create(
            user_id=user.id,
            model="midjourney",
            prompt="p",
            quality="4K",
            count=2,
            tokens_spent=20,
        )
        await repo.update_status(gen.id, "failed")
        updated = await repo.get_by_id(gen.id)
        assert updated.status == "failed"

    async def test_get_by_id_not_found(self, db_session):
        repo = GenerationRepository(db_session)
        gen = await repo.get_by_id(99999)
        assert gen is None

    async def test_get_by_user(self, db_session, user):
        repo = GenerationRepository(db_session)
        await repo.create(
            user_id=user.id,
            model="nano_banana",
            prompt="p1",
            quality="2K",
            count=1,
            tokens_spent=10,
        )
        await repo.create(
            user_id=user.id,
            model="seedream",
            prompt="p2",
            quality="4K",
            count=2,
            tokens_spent=20,
        )
        gens = await repo.get_by_user(user.id)
        assert len(gens) == 2

    async def test_count_by_model(self, db_session, user):
        repo = GenerationRepository(db_session)
        await repo.create(
            user_id=user.id,
            model="nano_banana",
            prompt="p",
            quality="2K",
            count=1,
            tokens_spent=5,
        )
        await repo.create(
            user_id=user.id,
            model="nano_banana",
            prompt="p",
            quality="2K",
            count=1,
            tokens_spent=5,
        )
        await repo.create(
            user_id=user.id,
            model="seedream",
            prompt="p",
            quality="2K",
            count=1,
            tokens_spent=5,
        )
        counts = await repo.count_by_model()
        assert counts["nano_banana"] == 2
        assert counts["seedream"] == 1

    async def test_create_with_preference(self, db_session, user):
        repo = GenerationRepository(db_session)
        gen = await repo.create(
            user_id=user.id,
            model="midjourney",
            prompt="a dog",
            quality="4K",
            count=4,
            tokens_spent=40,
            preference="cinematic",
        )
        assert gen.preference == "cinematic"


# ─── TransactionRepository ────────────────────────────────────────────────────


class TestTransactionRepository:
    async def test_create_transaction(self, db_session, user):
        repo = TransactionRepository(db_session)
        tx = await repo.create(
            user_id=user.id,
            type="purchase",
            amount=99.0,
            tokens=100,
            payment_id="pay_123",
        )
        assert tx.id is not None
        assert tx.status == "pending"
        assert tx.tokens == 100

    async def test_update_status(self, db_session, user):
        repo = TransactionRepository(db_session)
        await repo.create(
            user_id=user.id,
            type="purchase",
            amount=99.0,
            tokens=100,
            payment_id="pay_456",
        )
        await repo.update_status("pay_456", "success")
        updated = await repo.get_by_payment_id("pay_456")
        assert updated.status == "success"

    async def test_get_by_payment_id_found(self, db_session, user):
        repo = TransactionRepository(db_session)
        await repo.create(
            user_id=user.id,
            type="purchase",
            amount=249.0,
            tokens=300,
            payment_id="pay_789",
        )
        tx = await repo.get_by_payment_id("pay_789")
        assert tx is not None
        assert tx.amount == 249.0

    async def test_get_by_payment_id_not_found(self, db_session):
        repo = TransactionRepository(db_session)
        tx = await repo.get_by_payment_id("nonexistent")
        assert tx is None

    async def test_get_by_user(self, db_session, user):
        repo = TransactionRepository(db_session)
        await repo.create(user_id=user.id, type="purchase", amount=99.0, tokens=100)
        await repo.create(user_id=user.id, type="purchase", amount=249.0, tokens=300)
        txs = await repo.get_by_user(user.id)
        assert len(txs) == 2

    async def test_get_total_revenue(self, db_session, user):
        repo = TransactionRepository(db_session)
        await repo.create(
            user_id=user.id, type="purchase", amount=99.0, tokens=100, payment_id="r1"
        )
        await repo.create(
            user_id=user.id, type="purchase", amount=249.0, tokens=300, payment_id="r2"
        )
        await repo.update_status("r1", "success")
        await repo.update_status("r2", "success")
        # pending не считается
        await repo.create(user_id=user.id, type="purchase", amount=500.0, tokens=1000)
        total = await repo.get_total_revenue()
        assert total == 348.0

    async def test_get_revenue_by_period(self, db_session, user):
        repo = TransactionRepository(db_session)
        await repo.create(
            user_id=user.id, type="purchase", amount=99.0, tokens=100, payment_id="p1"
        )
        await repo.update_status("p1", "success")
        revenue = await repo.get_revenue_by_period(days=30)
        assert revenue == 99.0


# ─── SubscriptionRepository ───────────────────────────────────────────────────


class TestSubscriptionRepository:
    async def test_create_subscription(self, db_session, user):
        repo = SubscriptionRepository(db_session)
        expires = datetime.now() + timedelta(days=30)
        sub = await repo.create(user_id=user.id, plan="basic", expires_at=expires)
        assert sub.plan == "basic"
        assert sub.is_active is True

    async def test_get_by_user_id(self, db_session, user):
        repo = SubscriptionRepository(db_session)
        expires = datetime.now() + timedelta(days=30)
        await repo.create(user_id=user.id, plan="pro", expires_at=expires)
        sub = await repo.get_by_user_id(user.id)
        assert sub is not None
        assert sub.plan == "pro"

    async def test_get_by_user_id_not_found(self, db_session):
        repo = SubscriptionRepository(db_session)
        sub = await repo.get_by_user_id(99999)
        assert sub is None

    async def test_is_active_true(self, db_session, user):
        repo = SubscriptionRepository(db_session)
        expires = datetime.now() + timedelta(days=30)
        await repo.create(user_id=user.id, plan="standard", expires_at=expires)
        assert await repo.is_active(user.id) is True

    async def test_is_active_expired(self, db_session, user):
        repo = SubscriptionRepository(db_session)
        expires = datetime.now() - timedelta(days=1)  # уже истекла
        await repo.create(user_id=user.id, plan="basic", expires_at=expires)
        assert await repo.is_active(user.id) is False

    async def test_is_active_no_subscription(self, db_session):
        repo = SubscriptionRepository(db_session)
        assert await repo.is_active(99999) is False

    async def test_deactivate(self, db_session, user):
        repo = SubscriptionRepository(db_session)
        expires = datetime.now() + timedelta(days=30)
        await repo.create(user_id=user.id, plan="pro", expires_at=expires)
        await repo.deactivate(user.id)
        sub = await repo.get_by_user_id(user.id)
        assert sub.is_active is False

    async def test_get_active_count(self, db_session):
        from db.repositories.user import UserRepository

        user_repo = UserRepository(db_session)
        sub_repo = SubscriptionRepository(db_session)

        u1 = await user_repo.create(user_id=201, username="s1", full_name="S1")
        u2 = await user_repo.create(user_id=202, username="s2", full_name="S2")
        u3 = await user_repo.create(user_id=203, username="s3", full_name="S3")

        future = datetime.now() + timedelta(days=30)
        past = datetime.now() - timedelta(days=1)

        await sub_repo.create(user_id=u1.id, plan="basic", expires_at=future)
        await sub_repo.create(user_id=u2.id, plan="pro", expires_at=future)
        await sub_repo.create(user_id=u3.id, plan="basic", expires_at=past)

        count = await sub_repo.get_active_count()
        assert count == 2
