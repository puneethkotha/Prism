import json
import time
import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.config import settings
from app.schemas import ExtractedTags

EXTRACTION_PROMPT = """Extract structured metadata from the following product description. Return only valid JSON with these exact fields:

{
  "category": "top-level product category (e.g. Electronics, Audio, Wearables)",
  "subcategory": "specific subcategory (e.g. Wireless Earbuds, Smart Watch)",
  "key_features": ["list", "of", "up to 5", "key product features"],
  "use_case": "primary use case in one sentence",
  "target_audience": "who this product is for (e.g. Fitness enthusiasts, Home office workers)",
  "complexity": "one of: Beginner, Intermediate, Advanced",
  "sentiment": "one of: Positive, Neutral, Negative"
}

Product text:
{text}

Return only the JSON object, no explanation."""


class LLMService:
    def __init__(self):
        self._client: anthropic.AsyncAnthropic | None = None

    @property
    def client(self) -> anthropic.AsyncAnthropic:
        if self._client is None:
            self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        return self._client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((anthropic.RateLimitError, anthropic.APIStatusError)),
    )
    async def extract_tags(self, text: str) -> tuple[ExtractedTags, float]:
        start = time.perf_counter()
        message = await self.client.messages.create(
            model=settings.llm_model,
            max_tokens=512,
            messages=[{"role": "user", "content": EXTRACTION_PROMPT.format(text=text[:3000])}],
        )
        latency_ms = (time.perf_counter() - start) * 1000
        raw = message.content[0].text.strip()
        data = json.loads(raw)
        tags = ExtractedTags(**data)
        return tags, latency_ms

    async def extract_tags_sync_client(self, text: str) -> tuple[ExtractedTags, float]:
        """Synchronous client variant used in batch scripts."""
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        start = time.perf_counter()
        message = client.messages.create(
            model=settings.llm_model,
            max_tokens=512,
            messages=[{"role": "user", "content": EXTRACTION_PROMPT.format(text=text[:3000])}],
        )
        latency_ms = (time.perf_counter() - start) * 1000
        raw = message.content[0].text.strip()
        data = json.loads(raw)
        tags = ExtractedTags(**data)
        return tags, latency_ms


llm_service = LLMService()
