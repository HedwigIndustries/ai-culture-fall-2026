"""LLM-слой: замечания по смыслу (логика, обработка ошибок, транзакции), которые правилами не описать.

* gigachat — GigaChat API. Нужны GIGACHAT_CREDENTIALS (Authorization key из личного кабинета), GIGACHAT_SCOPE
  (GIGACHAT_API_PERS / GIGACHAT_API_B2B / GIGACHAT_API_CORP) и сертификат НУЦ Минцифры в GIGACHAT_CA_BUNDLE.
* openai — OpenAI-совместимый endpoint (OPENAI_BASE_URL, OPENAI_API_KEY, OPENAI_MODEL), например внутренний шлюз.
* none — только правила.
"""
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass

import requests

SYSTEM_PROMPT = """Ты — senior Python-ревьюер в команде бэкенда банка. Ты проверяешь diff merge request'а.
Правила:
1. Комментируй только ДОБАВЛЕННЫЕ строки (начинаются с '+'). Указывай line — номер строки в новой версии файла.
2. Приоритет: корректность и надёжность (ошибки логики, гонки, обработка ошибок, транзакции, идемпотентность платежей,
   None, граничные случаи) > безопасность > производительность > тесты > читаемость/API > стиль.
3. Не повторяй замечания из списка ALREADY_FOUND — их уже нашли статические правила.
4. Не придумывай проблем. Если код нормальный — верни пустой список. Стиль кода не комментируй — его проверяют правила.
5. severity: blocker (сломает прод/безопасность), major (вероятный баг), minor (улучшение), nit (вкус), question (неясно, спроси автора).
6. Пиши по-русски, коротко и конкретно, как коллеге. В suggestion — что исправить, одним-двумя предложениями; код не переписывай.
Ответ — ТОЛЬКО JSON без markdown:
{"findings":[{"line":<int>,"severity":"...","category":"bug|security|performance|refactor|style|question|suggestion","message":"...","suggestion":"<что исправить или null>","confidence":<0..1>}]}"""


@dataclass
class LLMResult:
    content: str
    input_tokens: int
    output_tokens: int
    model: str
    latency_s: float


class GigaChatClient:
    AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    API_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

    def __init__(self, model: str | None = None):
        self.credentials = os.environ["GIGACHAT_CREDENTIALS"]
        self.scope = os.environ.get("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
        self.model = model or os.environ.get("GIGACHAT_MODEL", "GigaChat-2-Pro")
        self.verify = os.environ.get("GIGACHAT_CA_BUNDLE", True)
        self._token, self._exp = None, 0

    def _auth(self) -> str:
        if self._token and time.time() < self._exp - 60:
            return self._token
        r = requests.post(self.AUTH_URL, timeout=(5, 20), verify=self.verify,
                          headers={"Authorization": f"Basic {self.credentials}", "RqUID": str(uuid.uuid4()),
                                   "Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
                          data={"scope": self.scope})
        r.raise_for_status()
        j = r.json()
        # По спецификации expires_at в миллисекундах, но в примерах документации встречаются секунды.
        exp = j["expires_at"]
        self._token, self._exp = j["access_token"], exp / 1000 if exp > 10**11 else exp
        return self._token

    def chat(self, system: str, user: str) -> LLMResult:
        t0 = time.time()
        r = requests.post(self.API_URL, timeout=(5, 120), verify=self.verify,
                          headers={"Authorization": f"Bearer {self._auth()}"},
                          json={"model": self.model, "temperature": 0.1,
                                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]})
        r.raise_for_status()
        j = r.json()
        return LLMResult(j["choices"][0]["message"]["content"], j["usage"]["prompt_tokens"],
                         j["usage"]["completion_tokens"], self.model, time.time() - t0)


class OpenAICompatClient:
    def __init__(self, model: str | None = None):
        self.base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.key = os.environ["OPENAI_API_KEY"]
        self.model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        # OpenRouter: OPENAI_REASONING=off отключает «рассуждения» модели — в 3–5 раз меньше выходных токенов
        self.reasoning_off = os.environ.get("OPENAI_REASONING", "").lower() == "off"

    def chat(self, system: str, user: str) -> LLMResult:
        t0 = time.time()
        body = {"model": self.model, "temperature": 0.1,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        if self.reasoning_off:
            body["reasoning"] = {"enabled": False}
        r = requests.post(f"{self.base}/chat/completions", timeout=(5, 180),
                          headers={"Authorization": f"Bearer {self.key}"}, json=body)
        r.raise_for_status()
        j = r.json()
        return LLMResult(j["choices"][0]["message"]["content"], j["usage"]["prompt_tokens"],
                         j["usage"]["completion_tokens"], self.model, time.time() - t0)


def make_client(provider: str, model: str | None = None):
    if provider == "gigachat":
        return GigaChatClient(model)
    if provider == "openai":
        return OpenAICompatClient(model)
    return None


def parse_findings(content: str) -> list[dict]:
    """Достаёт {"findings": [...]} из ответа; модель иногда оборачивает JSON в ```json или пишет текст вокруг."""
    start = content.find("{")
    if start < 0:
        return []
    try:
        data, _ = json.JSONDecoder().raw_decode(content[start:])
    except json.JSONDecodeError:
        return []
    items = data.get("findings") if isinstance(data, dict) else None
    return [i for i in items if isinstance(i, dict)] if isinstance(items, list) else []
