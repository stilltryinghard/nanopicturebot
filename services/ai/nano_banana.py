from __future__ import annotations
import aiohttp
from services.ai.base import BaseAIService, GenerationRequest, GenerationResult
from core.config import settings
from core.logger import logger


class NanoBananaService(BaseAIService):
    BASE_URL = "https://api.wavespeed.ai/api/v3/google/nano-banana/text-to-image"

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
        self, session: aiohttp.ClientSession, prompt: str, quality: str
    ) -> bytes:
        resolution = "2k" if quality == "2K" else "4k"
        payload = {
            "prompt": prompt,
            "resolution": resolution,
            "enable_sync_mode": True,
            "output_format": "png",
        }
        async with session.post(
            self.BASE_URL, json=payload, headers=self._headers
        ) as response:
            response.raise_for_status()
            data = await response.json()

        if data.get("code") != 200:
            raise Exception(f"NanoBanana error: {data.get('message')}")

        url = data["data"]["outputs"][0]

        async with session.get(url) as img_response:
            return await img_response.read()

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        prompt = request.prompt
        if request.preference:
            prompt += f". Style: {request.preference}"

        images: list[bytes] = []

        async with aiohttp.ClientSession() as session:
            import asyncio

            tasks = [
                self._generate_one(session, prompt, request.quality)
                for _ in range(request.count)
            ]
            images = await asyncio.gather(*tasks)

        logger.info(f"NanoBanana: сгенерировано {len(images)} изображений")
        return GenerationResult(images=list(images), model="nano_banana")
