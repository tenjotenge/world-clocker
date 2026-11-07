from dataclasses import dataclass, field
from datetime import date
from math import isfinite
from pathlib import Path
from urllib.parse import urlsplit

import yaml

from .calibration import Calibration, QuadraticCalibration, load_calibration
from .pilot import probe_bank


@dataclass(frozen=True)
class Settings:
    schema_version: int = 1
    provider: str = "mock"
    model: str | None = None
    base_url: str = "http://localhost:1234/v1"
    seed: int = 42
    repeats: int = 6
    temperature: float = 0.7
    top_p: float = 1.0
    max_tokens: int = 128
    timeout: float = 60
    retries: int = 2
    send_seed: bool = False
    distance: float = 0.25
    stability: float = 0.8
    bootstrap: int = 200
    configuration_ids: tuple[str, ...] | None = None
    benchmark: str = "0.1.0"
    calibration: Calibration | QuadraticCalibration = Calibration()
    model_annotations: dict[str, str | int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ValueError("Unsupported configuration schema")
        if self.benchmark not in ("0.1.0", "0.2.0"):
            raise ValueError("Unsupported benchmark version")
        if isinstance(self.calibration, dict):
            object.__setattr__(self, "calibration", load_calibration(self.calibration))
        if not isinstance(self.calibration, (Calibration, QuadraticCalibration)):
            raise ValueError("calibration must be a mapping")
        if not isinstance(self.model_annotations, dict):
            raise ValueError("model_annotations must be a mapping")
        annotations = dict(self.model_annotations)
        for key, value in annotations.items():
            if key == "parameter_count":
                if type(value) is not int or value < 1:
                    raise ValueError("parameter_count must be a positive integer")
            elif key == "release_date":
                if type(value) is date:
                    annotations[key] = value.isoformat()
                elif isinstance(value, str) and date.fromisoformat(value).isoformat() == value:
                    continue
                else:
                    raise ValueError("release_date must use YYYY-MM-DD")
            elif (
                key
                not in (
                    "family",
                    "architecture",
                    "quantization",
                    "training_specialization",
                    "inference_backend",
                )
                or not isinstance(value, str)
                or not value.strip()
            ):
                raise ValueError(f"Invalid model annotation: {key}")
        object.__setattr__(self, "model_annotations", annotations)
        if self.provider not in ("mock", "openai"):
            raise ValueError("provider must be mock or openai")
        if self.model is not None and (not isinstance(self.model, str) or not self.model.strip()):
            raise ValueError("model must be a nonempty string")
        if not isinstance(self.base_url, str):
            raise ValueError("base_url must be a string")
        url = urlsplit(self.base_url)
        _ = url.port
        if (
            url.scheme not in ("http", "https")
            or not url.hostname
            or url.username is not None
            or url.query
            or url.fragment
        ):
            raise ValueError("base_url must be an HTTP(S) endpoint without credentials or query")
        if url.scheme == "http" and url.hostname not in ("localhost", "127.0.0.1", "::1"):
            raise ValueError("HTTP is supported only on loopback")
        for name, low, high in (
            ("repeats", 2, 1000),
            ("seed", 0, 2**32 - 1),
            ("max_tokens", 1, 65536),
            ("retries", 0, 8),
            ("bootstrap", 1, 10000),
        ):
            value = getattr(self, name)
            if type(value) is not int or not low <= value <= high:
                raise ValueError(f"{name} must be an integer in [{low}, {high}]")
        for name, low, high in (
            ("temperature", 0, 2),
            ("top_p", 0, 1),
            ("timeout", 0, 3600),
            ("distance", 0, 1),
            ("stability", 0.5, 1),
        ):
            value = getattr(self, name)
            if type(value) not in (float, int) or not isfinite(value) or not low <= value <= high:
                raise ValueError(f"{name} must be finite and in [{low}, {high}]")
            if name in ("top_p", "timeout", "distance") and value == 0:
                raise ValueError(f"{name} must be positive")
        if self.configuration_ids is not None:
            ids = self.configuration_ids
            known = {config.id for config in probe_bank(self.benchmark)[0]}
            if (
                not isinstance(ids, (list, tuple))
                or not ids
                or any(not isinstance(item, str) or item not in known for item in ids)
                or len(set(ids)) != len(ids)
            ):
                raise ValueError("configuration_ids must contain unique, known configuration IDs")
            object.__setattr__(self, "configuration_ids", tuple(ids))
        if type(self.send_seed) is not bool:
            raise ValueError("send_seed must be a boolean")


def load_settings(path: Path) -> Settings:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("Expected a mapping with schema_version 1")
    try:
        return Settings(**data)
    except TypeError as exc:
        raise ValueError(f"Invalid configuration fields: {exc}") from exc
