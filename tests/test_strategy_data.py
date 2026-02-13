import json
from pathlib import Path


def test_preflop_scenarios_schema_contains_24_entries():
    data_path = Path(__file__).resolve().parents[1] / "src" / "shortdeck_cli" / "data" / "preflop_scenarios.json"
    with data_path.open("r", encoding="utf-8") as data_file:
        data = json.load(data_file)

    assert data["game"] == "short-deck"
    assert data["format"] == "5max-50a"
    assert len(data["scenarios"]) == 24


def test_preflop_scenarios_schema_keys_exist_for_main_categories():
    data_path = Path(__file__).resolve().parents[1] / "src" / "shortdeck_cli" / "data" / "preflop_scenarios.json"
    with data_path.open("r", encoding="utf-8") as data_file:
        data = json.load(data_file)

    keys = set(data["scenarios"].keys())
    assert "open:UTG_rfi" in keys
    assert "vs_limp:BTN_vs_CO_limp" in keys
    assert "vs_all_in:BTN_vs_CO_all_in" in keys
