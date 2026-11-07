import json
import os
import re
import time
from dataclasses import dataclass, field
from random import Random
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .config import Settings


@dataclass(frozen=True)
class Completion:
    text: str
    metadata: dict = field(default_factory=dict)


class Provider(Protocol):
    def models(self) -> list[dict]: ...

    def complete(self, model: str, trial: dict, scenario: dict, config: dict) -> Completion: ...


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class OpenAICompatible:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.opener = build_opener(NoRedirect())

    def request(self, path: str, body: dict | None = None) -> dict:
        headers = {"Content-Type": "application/json"}
        key = os.environ.get("WORLD_CLOCKER_API_KEY")
        if key:
            headers["Authorization"] = f"Bearer {key}"
        data = None if body is None else json.dumps(body).encode()
        request = Request(self.settings.base_url.rstrip("/") + path, data, headers)
        for attempt in range(self.settings.retries + 1):
            try:
                with self.opener.open(request, timeout=self.settings.timeout) as response:
                    return json.load(response)
            except (HTTPError, URLError, TimeoutError) as exc:
                if isinstance(exc, HTTPError):
                    code = exc.code
                    exc.close()
                    retryable = code in (408, 429) or 500 <= code <= 599
                    reason = f"HTTP {code}"
                else:
                    retryable = True
                    reason = f"{type(exc).__name__}: {exc}"
                if not retryable or attempt == self.settings.retries:
                    raise RuntimeError(reason) from exc
                time.sleep(min(2**attempt, 8))
        raise AssertionError("Retry loop exited unexpectedly")

    def models(self) -> list[dict]:
        return sorted(self.request("/models")["data"], key=lambda model: model["id"])

    def complete(self, model: str, trial: dict, scenario: dict, config: dict) -> Completion:
        body = {
            "model": model,
            "messages": [{"role": "user", "content": trial["prompt"]}],
            "temperature": self.settings.temperature,
            "top_p": self.settings.top_p,
            "max_tokens": self.settings.max_tokens,
        }
        if self.settings.send_seed:
            body["seed"] = trial["seed"]
        payload = self.request("/chat/completions", body)
        choices = payload.get("choices") or []
        choice = choices[0] if choices else {}
        text = choice.get("message", {}).get("content")
        metadata = {name: payload.get(name) for name in ("model", "system_fingerprint", "usage")}
        metadata["finish_reason"] = choice.get("finish_reason")
        if not isinstance(text, str):
            metadata["response_without_text"] = payload
            text = ""
        return Completion(text, metadata)


class MockProvider:
    def models(self) -> list[dict]:
        return [{"id": name, "version": "1"} for name in ("structured", "constant", "random")]

    def complete(self, model: str, trial: dict, scenario: dict, config: dict) -> Completion:
        action = 0
        if model == "random":
            action = Random(trial["seed"]).randrange(2)
        elif (
            model == "structured" and config["factors"] and scenario["variant"] != "counterfactual"
        ):
            action = config["factors"][scenario["axis"]]
        label = "AB"[trial["mapping"].index(str(action))]
        return Completion(json.dumps({"choice": label}))


def provider_for(settings: Settings) -> Provider:
    return MockProvider() if settings.provider == "mock" else OpenAICompatible(settings)


def parse_choice(text: str, mapping: str) -> int:
    stripped = text.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", stripped, re.DOTALL | re.IGNORECASE)
    payload = json.loads(fenced[1] if fenced else stripped)
    if not isinstance(payload, dict) or payload.get("choice") not in ("A", "B"):
        raise ValueError("Expected a JSON object with choice A or B")
    return int(mapping["AB".index(payload["choice"])])
