"""Windows PokerStars window capture + OCR observation source."""

from __future__ import annotations

import ctypes
import json
import platform
import re
from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path

from shortdeck_cli.auto_ingest import Observation, ObservationSource


VALID_POSITIONS = ("UTG", "MP1", "MP2", "HJ", "CO", "BTN")
VALID_ACTIONS = ("fold", "limp", "all-in")


@dataclass(frozen=True)
class RoiRect:
    left: float
    top: float
    right: float
    bottom: float
    normalized: bool


def _normalize_ocr_text(text: str) -> str:
    lowered = text.lower().replace("\n", " ")
    lowered = lowered.replace("all in", "all-in")
    lowered = re.sub(r"\s+", " ", lowered)
    return lowered.strip()


def _extract_hero_hand(text: str) -> str | None:
    direct_match = re.search(r"\b([akqjt9876][shdc])\s*([akqjt9876][shdc])\b", text, flags=re.IGNORECASE)
    if direct_match:
        first = direct_match.group(1)
        second = direct_match.group(2)
        return f"{first[0].upper()}{first[1].lower()}{second[0].upper()}{second[1].lower()}"

    shorthand_match = re.search(r"\b([akqjt9876]{2}(?:s|o)?)\b", text, flags=re.IGNORECASE)
    if shorthand_match:
        value = shorthand_match.group(1)
        return value[:2].upper() + value[2:].lower()

    return None


def _extract_villain_action(text: str, hero_position: str) -> tuple[str, str] | None:
    hero_index = VALID_POSITIONS.index(hero_position)
    valid_villains = set(VALID_POSITIONS[:hero_index])
    if not valid_villains:
        return None

    action_re = re.compile(r"\b(utg|mp1|mp2|hj|co|btn)\s+(fold|limp|all-in)\b", flags=re.IGNORECASE)
    matches = action_re.findall(text)
    for raw_position, raw_action in reversed(matches):
        position = raw_position.upper()
        action = raw_action.lower()
        if position in valid_villains and action in VALID_ACTIONS:
            return position, action
    return None


def extract_observation_from_ocr_parts(
    hand_text: str,
    action_text: str,
    hero_position: str,
    source_name: str = "pokerstars-ocr",
) -> Observation | None:
    hero_position = hero_position.upper().strip()
    if hero_position not in VALID_POSITIONS:
        raise ValueError("hero_position must be one of: UTG, MP1, MP2, HJ, CO, BTN")

    hero_hand = _extract_hero_hand(_normalize_ocr_text(hand_text))
    if hero_hand is None:
        return None

    if hero_position == "UTG":
        return Observation(
            hero_hand=hero_hand,
            hero_position=hero_position,
            villain_position="UTG",
            villain_action="fold",
            confidence=0.55,
            source=source_name,
        )

    villain = _extract_villain_action(_normalize_ocr_text(action_text), hero_position)
    if villain is None:
        return Observation(
            hero_hand=hero_hand,
            hero_position=hero_position,
            confidence=0.35,
            source=source_name,
        )

    villain_position, villain_action = villain
    return Observation(
        hero_hand=hero_hand,
        hero_position=hero_position,
        villain_position=villain_position,
        villain_action=villain_action,
        confidence=0.7,
        source=source_name,
    )


def extract_observation_from_ocr_text(text: str, hero_position: str, source_name: str = "pokerstars-ocr") -> Observation | None:
    return extract_observation_from_ocr_parts(
        hand_text=text,
        action_text=text,
        hero_position=hero_position,
        source_name=source_name,
    )


def load_roi_config(file_path: str | Path) -> dict[str, RoiRect]:
    path = Path(file_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("ROI config must be a JSON object.")

    regions: dict[str, RoiRect] = {}
    for region_name in ("hero_hand", "action_log"):
        raw = payload.get(region_name)
        if raw is None:
            continue
        if not isinstance(raw, dict):
            raise ValueError(f"ROI region '{region_name}' must be an object.")

        try:
            left = float(raw["left"])
            top = float(raw["top"])
            right = float(raw["right"])
            bottom = float(raw["bottom"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"ROI region '{region_name}' must define numeric left/top/right/bottom.") from error

        normalized = all(0 <= value <= 1 for value in (left, top, right, bottom))
        if right <= left or bottom <= top:
            raise ValueError(f"ROI region '{region_name}' has invalid bounds.")

        regions[region_name] = RoiRect(
            left=left,
            top=top,
            right=right,
            bottom=bottom,
            normalized=normalized,
        )

    return regions


@dataclass(frozen=True)
class _WindowRect:
    left: int
    top: int
    right: int
    bottom: int


def _find_window_rect(title_contains: str) -> _WindowRect | None:
    if platform.system() != "Windows":
        return None

    user32 = ctypes.windll.user32
    wnd_enum_proc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    enum_windows = user32.EnumWindows
    enum_windows.argtypes = [wnd_enum_proc, wintypes.LPARAM]
    enum_windows.restype = wintypes.BOOL

    get_window_text_length = user32.GetWindowTextLengthW
    get_window_text = user32.GetWindowTextW
    is_window_visible = user32.IsWindowVisible
    get_window_rect = user32.GetWindowRect

    wanted = title_contains.lower().strip()
    found: list[_WindowRect] = []

    @wnd_enum_proc
    def _callback(hwnd, _lparam):
        if not is_window_visible(hwnd):
            return True
        length = get_window_text_length(hwnd)
        if length <= 0:
            return True
        buffer = ctypes.create_unicode_buffer(length + 1)
        get_window_text(hwnd, buffer, length + 1)
        title = buffer.value.strip()
        if not title:
            return True
        if wanted not in title.lower():
            return True

        rect = wintypes.RECT()
        if not get_window_rect(hwnd, ctypes.byref(rect)):
            return True
        found.append(_WindowRect(rect.left, rect.top, rect.right, rect.bottom))
        return False

    enum_windows(_callback, 0)
    if not found:
        return None
    return found[0]


class PokerStarsWindowOcrSource(ObservationSource):
    def __init__(
        self,
        hero_position: str,
        window_title_contains: str = "PokerStars",
        tesseract_cmd: str | None = None,
        debug_dir: str | None = None,
        roi_config_path: str | None = None,
    ):
        self.hero_position = hero_position.upper().strip()
        self.window_title_contains = window_title_contains
        self.debug_dir = Path(debug_dir) if debug_dir else None
        self._frame_index = 0
        self._roi_regions = load_roi_config(roi_config_path) if roi_config_path else {}

        if self.hero_position not in VALID_POSITIONS:
            raise ValueError("hero_position must be one of: UTG, MP1, MP2, HJ, CO, BTN")

        try:
            import pytesseract  # type: ignore

            self._pytesseract = pytesseract
        except ImportError as error:
            raise RuntimeError("pytesseract is required for --auto-source pokerstars") from error

        if tesseract_cmd:
            self._pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

        try:
            from PIL import ImageGrab  # type: ignore

            self._image_grab = ImageGrab
        except ImportError as error:
            raise RuntimeError("Pillow is required for --auto-source pokerstars") from error

    @staticmethod
    def _crop_region(image, roi: RoiRect):
        width, height = image.size
        if roi.normalized:
            left = int(roi.left * width)
            top = int(roi.top * height)
            right = int(roi.right * width)
            bottom = int(roi.bottom * height)
        else:
            left = int(roi.left)
            top = int(roi.top)
            right = int(roi.right)
            bottom = int(roi.bottom)

        left = max(0, min(left, width - 1))
        top = max(0, min(top, height - 1))
        right = max(left + 1, min(right, width))
        bottom = max(top + 1, min(bottom, height))
        return image.crop((left, top, right, bottom))

    def next_observation(self) -> Observation | None:
        rect = _find_window_rect(self.window_title_contains)
        if rect is None:
            return None

        image = self._image_grab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom), all_screens=True)
        hand_roi = self._roi_regions.get("hero_hand")
        action_roi = self._roi_regions.get("action_log")

        if hand_roi is not None:
            hand_text = self._pytesseract.image_to_string(self._crop_region(image, hand_roi), config="--psm 7")
        else:
            hand_text = self._pytesseract.image_to_string(image)

        if action_roi is not None:
            action_text = self._pytesseract.image_to_string(self._crop_region(image, action_roi), config="--psm 6")
        else:
            action_text = self._pytesseract.image_to_string(image)

        if self.debug_dir:
            self.debug_dir.mkdir(parents=True, exist_ok=True)
            frame_id = f"{self._frame_index:06d}"
            image.save(self.debug_dir / f"{frame_id}.png")
            (self.debug_dir / f"{frame_id}.hand.txt").write_text(hand_text, encoding="utf-8")
            (self.debug_dir / f"{frame_id}.action.txt").write_text(action_text, encoding="utf-8")

        self._frame_index += 1
        return extract_observation_from_ocr_parts(
            hand_text=hand_text,
            action_text=action_text,
            hero_position=self.hero_position,
        )
