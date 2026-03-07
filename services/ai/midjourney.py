from __future__ import annotations
import asyncio
import aiohttp
from services.ai.base import BaseAIService, GenerationRequest, GenerationResult
from core.config import settings
from core.logger import logger

POLL_INTERVAL = 5  # секунд между проверками
MAX_WAIT_TIME = 600  # максимум 10 минут


class MidjourneyService(BaseAIService):
    BASE_URL = "https://api.midapi.ai/api/v1/mj"

    def __init__(self):
        self.api_key = settings.MIDJOURNEY_API_KEY

    @property
    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def get_token_cost(self, quality: str, count: int) -> int:
        base = settings.TOKENS_2K if quality == "2K" else settings.TOKENS_4K
        return base * count

    async def _submit_task(self, session: aiohttp.ClientSession, prompt: str) -> str:
        payload = {
            "taskType": "mj_txt2img",
            "prompt": prompt,
            "speed": "fast",
            "aspectRatio": "1:1",
            "version": "6.1",
        }
        async with session.post(
            f"{self.BASE_URL}/generate",
            json=payload,
            headers=self._headers,
        ) as response:
            response.raise_for_status()
            data = await response.json()

        if data.get("code") != 200:
            raise Exception(f"Midjourney submit error: {data.get('msg', 'unknown')}")

        task_id = data["data"]["taskId"]
        logger.info(f"Midjourney: задача создана {task_id}")
        return task_id

    async def _poll_task(
        self, session: aiohttp.ClientSession, task_id: str
    ) -> list[str]:
        elapsed = 0
        while elapsed < MAX_WAIT_TIME:
            await asyncio.sleep(POLL_INTERVAL)
            elapsed += POLL_INTERVAL

            async with session.get(
                f"https://api.midapi.ai/api/v1/mj/record-info?taskId={task_id}",
                headers=self._headers,
            ) as response:
                response.raise_for_status()
                data = await response.json()

            task_data = data.get("data", {})
            success_flag = task_data.get("successFlag", 0)

            if success_flag == 1:
                result_info = task_data.get("resultInfoJson")
                if isinstance(result_info, str):
                    import json as _json

                    result_info = _json.loads(result_info)
                raw_urls = (result_info or {}).get("resultUrls", [])
                urls = [
                    item["resultUrl"] if isinstance(item, dict) else item
                    for item in raw_urls
                ]
                logger.info(f"Midjourney: задача {task_id} завершена, {len(urls)} URL")
                return urls
            elif success_flag in (2, 3):
                error_msg = task_data.get("errorMessage", "Generation failed")
                raise Exception(f"Midjourney task failed: {error_msg}")

            logger.info(f"Midjourney: ждём задачу {task_id}, прошло {elapsed}с")

        raise Exception(f"Midjourney: таймаут задачи {task_id}")

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        prompt = request.prompt
        if request.preference:
            prompt += f", {request.preference}"
        if request.quality == "4K":
            prompt += " --q 2"

        images: list[bytes] = []

        async with aiohttp.ClientSession() as session:
            task_id = await self._submit_task(session, prompt)
            image_urls = await self._poll_task(session, task_id)

            for url in image_urls[: request.count]:
                async with session.get(url) as img_response:
                    images.append(await img_response.read())

        logger.info(f"Midjourney: сгенерировано {len(images)} изображений")
        return GenerationResult(images=images, model="midjourney")
