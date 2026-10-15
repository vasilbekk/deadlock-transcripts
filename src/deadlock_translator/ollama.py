"""
Minimal Ollama client for Russian transcript translation
"""

import json
from urllib.error import URLError
from urllib.request import Request, urlopen


class OllamaTranslator:
    """
    Translate individual English voice lines with an Ollama chat model
    """

    def __init__(
        self,
        *,
        model: str,
        endpoint: str,
    ) -> None:
        """
        Initialize the Ollama model connection
        """
        self.model = model
        self.endpoint = endpoint

    def translate(
        self,
        *,
        text: str,
        language: str,
        record_id: str,
        glossary_prompt: str,
    ) -> str:
        """
        Return a translation in the requested language without commentary
        """
        payload = {
            "model": self.model,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Translate English video game dialogue into the language identified by "
                        f"the ISO language code '{language}'. "
                        "Preserve character names, ability names, and intentional tone. "
                        'Return JSON only in this exact shape: {"translation":"..."}.'
                    ),
                },
                {
                    "role": "user",
                    "content": f"Voice-line ID: {record_id}\n{glossary_prompt}English: {text}",
                },
            ],
        }
        request = Request(
            url=f"{self.endpoint.rstrip('/')}/api/chat",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=120) as response:
                result: object = json.load(response)
        except URLError as error:
            raise RuntimeError(f"Cannot reach Ollama at {self.endpoint}") from error
        if not isinstance(result, dict):
            raise RuntimeError("Ollama returned an invalid response")
        message = result.get("message")
        if not isinstance(message, dict) or not isinstance(message.get("content"), str):
            raise RuntimeError("Ollama returned no translated text")
        try:
            translated: object = json.loads(message["content"]).get("translation")
        except json.JSONDecodeError as error:
            raise RuntimeError("Ollama returned invalid translation JSON") from error
        if not isinstance(translated, str) or not translated.strip():
            raise RuntimeError("Ollama returned no translated text")
        return translated
