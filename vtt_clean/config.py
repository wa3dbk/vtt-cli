from __future__ import annotations

from dataclasses import dataclass, field
from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml


class TaxonomyError(ValueError):
    pass


class PipelineError(ValueError):
    pass


@dataclass
class Taxonomy:
    events: dict[str, list[str]]
    delimiters: dict[str, str]
    rules: dict[str, Any]
    normalization: dict[str, Any]
    output_tokens: dict[str, str]
    default_lang: str
    _surface_to_event: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for ev, surfaces in self.events.items():
            for s in surfaces:
                if s in self._surface_to_event:
                    raise TaxonomyError(
                        f"duplicate surface {s!r} mapped to {self._surface_to_event[s]!r} and {ev!r}"
                    )
                self._surface_to_event[s] = ev
        for ev in self.events:
            if ev not in self.output_tokens:
                raise TaxonomyError(f"event {ev!r} has no output_tokens entry")

    def lookup(self, surface: str) -> str | None:
        return self._surface_to_event.get(surface.strip())

    def render_token(self, event_type: str) -> str:
        return self.output_tokens.get(event_type, "<unk>")


@dataclass
class PipelineSpec:
    steps: list[str]


def _load_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


_REQUIRED_SECTIONS = ("events", "delimiters", "rules", "normalization", "output_tokens")


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise TaxonomyError(msg)


def _validate_taxonomy_data(data: Any) -> None:
    _require(isinstance(data, dict), f"taxonomy must be a mapping, got {type(data).__name__}")
    for key in _REQUIRED_SECTIONS:
        _require(key in data, f"missing required taxonomy key: {key!r}")
    events = data["events"]
    _require(isinstance(events, dict), f"events: expected mapping, got {type(events).__name__}")
    for ev, surfaces in events.items():
        _require(
            isinstance(ev, str) and ev, f"events: event name must be non-empty string, got {ev!r}"
        )
        _require(
            isinstance(surfaces, list),
            f"events.{ev}: expected list, got {type(surfaces).__name__}",
        )
        for i, s in enumerate(surfaces):
            _require(
                isinstance(s, str) and s,
                f"events.{ev}[{i}]: surface must be non-empty string, got {s!r}",
            )
    tokens = data["output_tokens"]
    _require(
        isinstance(tokens, dict), f"output_tokens: expected mapping, got {type(tokens).__name__}"
    )
    for ev, tok in tokens.items():
        _require(
            isinstance(tok, str),
            f"output_tokens.{ev}: token must be string, got {type(tok).__name__}",
        )
    extra_tokens = set(tokens) - set(events)
    _require(
        not extra_tokens,
        f"output_tokens has entries for undeclared events: {sorted(extra_tokens)}",
    )
    for section in ("delimiters", "rules", "normalization"):
        _require(
            isinstance(data[section], dict),
            f"{section}: expected mapping, got {type(data[section]).__name__}",
        )


def load_taxonomy(path: Path | None) -> Taxonomy:
    if path is None:
        data = yaml.safe_load(
            files("vtt_clean").joinpath("default_taxonomy.yaml").read_text(encoding="utf-8")
        )
    else:
        data = _load_yaml(path)
    _validate_taxonomy_data(data)
    return Taxonomy(
        events=data["events"],
        delimiters=data["delimiters"],
        rules=data["rules"],
        normalization=data["normalization"],
        output_tokens=data["output_tokens"],
        default_lang=data.get("default_lang", "ar"),
    )


def load_pipeline(path: Path | None) -> PipelineSpec:
    if path is None:
        data = yaml.safe_load(
            files("vtt_clean").joinpath("default_pipeline.yaml").read_text(encoding="utf-8")
        )
    else:
        data = _load_yaml(path)
    steps = data.get("steps")
    if not steps or not isinstance(steps, list):
        raise PipelineError("pipeline YAML must have a non-empty 'steps' list")
    return PipelineSpec(steps=steps)
