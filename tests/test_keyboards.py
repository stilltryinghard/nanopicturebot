from __future__ import annotations
from aiogram.types import InlineKeyboardMarkup


class TestBalanceKeyboards:
    def test_balance_menu_kb_structure(self):
        from bot.keyboards.balance_kb import balance_menu_kb

        kb = balance_menu_kb()
        assert isinstance(kb, InlineKeyboardMarkup)
        all_data = [btn.callback_data for row in kb.inline_keyboard for btn in row]
        assert "buy_tokens" in all_data
        assert "subscription" in all_data

    async def test_token_packages_kb(self):
        from unittest.mock import AsyncMock, patch
        from bot.keyboards.balance_kb import token_packages_kb

        mock_settings = AsyncMock()
        mock_settings.get_token_packages = AsyncMock(
            return_value=[
                {"tokens": 100, "amount": 99},
                {"tokens": 300, "amount": 249},
            ]
        )
        with patch("services.settings_service.bot_settings", mock_settings):
            kb = await token_packages_kb()

        all_data = [
            btn.callback_data
            for row in kb.inline_keyboard
            for btn in row
            if btn.callback_data
        ]
        package_data = [d for d in all_data if d.startswith("package:")]
        assert len(package_data) >= 1
        for d in package_data:
            parts = d.split(":")
            assert len(parts) == 3
            assert parts[1].isdigit()
            assert parts[2].isdigit()

    async def test_subscription_plans_kb(self):
        from unittest.mock import AsyncMock, patch
        from bot.keyboards.balance_kb import subscription_plans_kb

        mock_settings = AsyncMock()
        mock_settings.get_subscription_plans = AsyncMock(
            return_value=[
                {"plan": "basic", "amount": 299, "label": "🥉 Базовый"},
                {"plan": "pro", "amount": 999, "label": "🥇 Про"},
            ]
        )
        with patch("services.settings_service.bot_settings", mock_settings):
            kb = await subscription_plans_kb()

        all_data = [
            btn.callback_data
            for row in kb.inline_keyboard
            for btn in row
            if btn.callback_data
        ]
        sub_data = [d for d in all_data if d.startswith("sub:")]
        assert len(sub_data) >= 1
        for d in sub_data:
            parts = d.split(":")
            assert len(parts) == 3  # sub:plan:amount


class TestGenerateKeyboards:
    def test_select_model_kb(self):
        from bot.keyboards.generate_kb import select_model_kb

        kb = select_model_kb()
        all_data = [
            btn.callback_data
            for row in kb.inline_keyboard
            for btn in row
            if btn.callback_data
        ]
        model_data = [d for d in all_data if d.startswith("model:")]
        assert "model:nano_banana" in model_data
        assert "model:seedream" in model_data
        assert "model:midjourney" in model_data

    def test_select_quality_kb(self):
        from bot.keyboards.generate_kb import select_quality_kb

        kb = select_quality_kb()
        all_data = [
            btn.callback_data
            for row in kb.inline_keyboard
            for btn in row
            if btn.callback_data
        ]
        assert "quality:2K" in all_data
        assert "quality:4K" in all_data

    def test_select_count_kb(self):
        from bot.keyboards.generate_kb import select_count_kb

        kb = select_count_kb()
        all_data = [
            btn.callback_data
            for row in kb.inline_keyboard
            for btn in row
            if btn.callback_data
        ]
        count_data = [d for d in all_data if d.startswith("count:")]
        assert len(count_data) >= 1

    def test_confirm_generation_kb(self):
        from bot.keyboards.generate_kb import confirm_generation_kb

        kb = confirm_generation_kb(cost=50)
        all_data = [
            btn.callback_data
            for row in kb.inline_keyboard
            for btn in row
            if btn.callback_data
        ]
        assert "confirm_generate" in all_data

    def test_skip_preference_kb(self):
        from bot.keyboards.generate_kb import skip_preference_kb

        kb = skip_preference_kb()
        all_data = [
            btn.callback_data
            for row in kb.inline_keyboard
            for btn in row
            if btn.callback_data
        ]
        assert "skip_preference" in all_data


class TestMainKeyboard:
    def test_back_to_main_kb(self):
        from bot.keyboards.main_kb import back_to_main_kb

        kb = back_to_main_kb()
        assert isinstance(kb, InlineKeyboardMarkup)
        all_data = [
            btn.callback_data
            for row in kb.inline_keyboard
            for btn in row
            if btn.callback_data
        ]
        assert len(all_data) >= 1


class TestAdminKeyboards:
    def test_admin_menu_kb(self):
        from bot.keyboards.admin_kb import admin_menu_kb

        kb = admin_menu_kb()
        assert isinstance(kb, InlineKeyboardMarkup)
        all_data = [
            btn.callback_data
            for row in kb.inline_keyboard
            for btn in row
            if btn.callback_data
        ]
        assert any("admin:" in d for d in all_data)

    def test_admin_user_actions_kb_not_blocked(self):
        from bot.keyboards.admin_kb import admin_user_actions_kb

        kb = admin_user_actions_kb(user_id=123, is_blocked=False)
        all_data = [
            btn.callback_data
            for row in kb.inline_keyboard
            for btn in row
            if btn.callback_data
        ]
        assert any("block" in d for d in all_data)

    def test_admin_user_actions_kb_blocked(self):
        from bot.keyboards.admin_kb import admin_user_actions_kb

        kb = admin_user_actions_kb(user_id=123, is_blocked=True)
        all_data = [
            btn.callback_data
            for row in kb.inline_keyboard
            for btn in row
            if btn.callback_data
        ]
        assert any("unblock" in d for d in all_data)
