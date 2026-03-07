from __future__ import annotations
import asyncio
import aiohttp
from services.ai.base import BaseAIService, GenerationRequest, GenerationResult
from core.config import settings
from core.logger import logger


class SeedreamService(BaseAIService):
    BASE_URL = "https://api.wavespeed.ai/api/v3/bytedance/seedream-v5.0-lite"

    def __init__(self):
        self.api_key = settings.WAVESPEED_API_KEY

    @property
    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def get_token_cost(self, quality: str, count: int) -> int:
        base = settings.TOKENS_2K if quality == "2K" else settings.TOKENS_4K
        return base * count

    async def _generate_one(
        self, session: aiohttp.ClientSession, prompt: str, size: str
    ) -> bytes:
        payload = {
            "prompt": prompt,
            "size": size,
            "enable_sync_mode": True,
        }
        async with session.post(
            self.BASE_URL, json=payload, headers=self._headers
        ) as response:
            response.raise_for_status()
            data = await response.json()

        if data.get("code") != 200:
            raise Exception(f"Seedream error: {data.get('message')}")

        url = data["data"]["outputs"][0]

        async with session.get(url) as img_response:
            return await img_response.read()

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        prompt = request.prompt
        if request.preference:
            prompt += f". Style: {request.preference}"

        size = "2048*2048" if request.quality == "2K" else "3840*2160"

        async with aiohttp.ClientSession() as session:
            tasks = [
                self._generate_one(session, prompt, size) for _ in range(request.count)
            ]
            images = await asyncio.gather(*tasks)

        logger.info(f"Seedream: сгенерировано {len(images)} изображений")
        return GenerationResult(images=list(images), model="seedream")
