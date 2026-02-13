"""Scenario mapping and recommendation lookup for the MVP."""

from functools import lru_cache
from json import load
from pathlib import Path


POSITION_ALIAS = {
    "UTG": "UTG",
    "MP1": "MP",
    "MP2": "MP",
    "HJ": "HJ",
    "CO": "CO",
    "BTN": "BTN",
}

DISPLAY_MIN_PERCENT = 1.0


@lru_cache(maxsize=1)
def load_strategy_data() -> dict:
    file_path = Path(__file__).resolve().parent / "data" / "preflop_scenarios.json"
    with file_path.open("r", encoding="utf-8") as data_file:
        return load(data_file)


def build_scenario_key(hero_position: str, villain_position: str, villain_action: str) -> str:
    hero = POSITION_ALIAS[hero_position]
    villain = POSITION_ALIAS[villain_position]

    if villain_action == "fold":
        return f"open:{hero}_rfi"
    if villain_action == "limp":
        return f"vs_limp:{hero}_vs_{villain}_limp"
    return f"vs_all_in:{hero}_vs_{villain}_all_in"


def _fallback_recommendation(hero_hand: str, villain_action: str) -> str:
    if villain_action == "all-in":
        return "Dummy recommendation: Fold"
    if villain_action == "limp":
        if hero_hand in {"AA", "KK", "QQ", "AKs"}:
            return "Dummy recommendation: Raise"
        return "Dummy recommendation: Check"
    return "Dummy recommendation: Open"


def _format_percent(value: float) -> str:
    rounded = round(value, 1)
    if rounded.is_integer():
        return str(int(rounded))
    return f"{rounded:.1f}"


def _format_data_recommendation(action_data: str | dict[str, float | int]) -> str:
    if isinstance(action_data, str):
        return f"Data recommendation: {action_data} (confidence: high)"

    allowed_actions = {"all-in", "call", "fold", "raise", "check", "open", "limp", "ante"}
    raw_entries: list[tuple[str, float]] = []
    for action, raw_value in action_data.items():
        if action not in allowed_actions:
            continue
        value = float(raw_value)
        if value <= 0:
            continue
        raw_entries.append((action, value))

    use_fraction_scale = bool(raw_entries) and all(0 < value <= 1 for _, value in raw_entries)
    normalized: list[tuple[str, float]] = []
    for action, value in raw_entries:
        if use_fraction_scale:
            value *= 100
        normalized.append((action, value))

    if not normalized:
        return "Data recommendation: TBD"

    total = sum(value for _, value in normalized)
    if total <= 0:
        return "Data recommendation: TBD"

    scaled = [(action, (value / total) * 100) for action, value in normalized]
    scaled.sort(key=lambda item: item[1], reverse=True)

    filtered = [(action, value) for action, value in scaled if value >= DISPLAY_MIN_PERCENT]
    if not filtered:
        filtered = [scaled[0]]

    filtered_total = sum(value for _, value in filtered)
    display_scaled = [(action, (value / filtered_total) * 100) for action, value in filtered]

    top_weight = display_scaled[0][1]
    if top_weight >= 90:
        confidence = "high"
    elif top_weight >= 60:
        confidence = "medium"
    else:
        confidence = "low"

    if len(display_scaled) == 1:
        return f"Data recommendation: {display_scaled[0][0]} (confidence: {confidence})"

    parts = [f"{_format_percent(value)}% {action}" for action, value in display_scaled]
    return f"Data recommendation: {', '.join(parts)} (confidence: {confidence})"


def recommend_action(hero_hand: str, hero_position: str, villain_position: str, villain_action: str) -> tuple[str, str]:
    scenario_key = build_scenario_key(
        hero_position=hero_position,
        villain_position=villain_position,
        villain_action=villain_action,
    )
    scenarios = load_strategy_data().get("scenarios", {})
    scenario = scenarios.get(scenario_key)

    if scenario and hero_hand in scenario.get("hand_actions", {}):
        action = scenario["hand_actions"][hero_hand]
        recommendation = _format_data_recommendation(action)
    elif scenario and scenario.get("default_recommendation") != "TBD":
        recommendation = _format_data_recommendation(scenario["default_recommendation"])
    else:
        recommendation = _fallback_recommendation(hero_hand=hero_hand, villain_action=villain_action)

    return scenario_key, recommendation
