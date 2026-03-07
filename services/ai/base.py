from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class GenerationRequest:
    """Параметры запроса на генерацию"""

    prompt: str
    quality: str  # 2K или 4K
    count: int  # 1-4 изображения
    preference: str | None = None  # доп. настройки стиля


@dataclass
class GenerationResult:
    """Результат генерации"""

    images: list[bytes]  # список изображений в байтах
    model: str  # какая модель генерировала


class BaseAIService(ABC):
    """
    Абстрактный класс — как розетка с определённым стандартом.
    Любой AI-сервис обязан реализовать метод generate,
    иначе Python выбросит ошибку при создании объекта.
    """

    @abstractmethod
    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """Отправить запрос в AI и получить изображения"""
        pass

    @abstractmethod
    def get_token_cost(self, quality: str, count: int) -> int:
        """Сколько токенов стоит генерация"""
        pass
