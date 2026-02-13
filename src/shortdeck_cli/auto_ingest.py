"""Auto-ingestion primitives for non-interactive recommendation flow."""

from __future__ import annotations

from dataclasses import dataclass
from json import JSONDecodeError, loads
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class Observation:
    hero_hand: str
    hero_position: str
    villain_position: str | None = None
    villain_action: str | None = None
    confidence: float | None = None
    source: str | None = None


class ObservationSource(Protocol):
    def next_observation(self) -> Observation | None:
        """Return a new observation when available, else None."""


class JsonlObservationSource:
    """Poll observations from a JSON Lines file.

    Each line must be a JSON object with at least:
    - hero_hand
    - hero_position
    Optional fields:
    - villain_position
    - villain_action
    - confidence
    - source
    """

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
        self._line_index = 0

    def next_observation(self) -> Observation | None:
        if not self.file_path.exists():
            return None

        lines = self.file_path.read_text(encoding="utf-8").splitlines()
        if self._line_index >= len(lines):
            return None

        while self._line_index < len(lines):
            line = lines[self._line_index].strip()
            self._line_index += 1
            if not line:
                continue
            try:
                payload = loads(line)
            except JSONDecodeError:
                continue

            if not isinstance(payload, dict):
                continue

            hero_hand = payload.get("hero_hand")
            hero_position = payload.get("hero_position")
            if not isinstance(hero_hand, str) or not isinstance(hero_position, str):
                continue

            villain_position = payload.get("villain_position")
            villain_action = payload.get("villain_action")
            confidence = payload.get("confidence")
            source = payload.get("source")

            if villain_position is not None and not isinstance(villain_position, str):
                villain_position = None
            if villain_action is not None and not isinstance(villain_action, str):
                villain_action = None
            if confidence is not None:
                try:
                    confidence = float(confidence)
                except (TypeError, ValueError):
                    confidence = None
            if source is not None and not isinstance(source, str):
                source = None

            return Observation(
                hero_hand=hero_hand,
                hero_position=hero_position,
                villain_position=villain_position,
                villain_action=villain_action,
                confidence=confidence,
                source=source,
            )

        return None
