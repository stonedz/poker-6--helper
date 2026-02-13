import json

from shortdeck_cli.pokerstars_capture import extract_observation_from_ocr_parts, extract_observation_from_ocr_text, load_roi_config


def test_extract_observation_for_utg_uses_auto_villain_defaults():
    observation = extract_observation_from_ocr_text("Hole cards: As Ad", hero_position="UTG")

    assert observation is not None
    assert observation.hero_hand == "AsAd"
    assert observation.hero_position == "UTG"
    assert observation.villain_position == "UTG"
    assert observation.villain_action == "fold"


def test_extract_observation_for_non_utg_reads_villain_action():
    text = "Table log ... UTG limp ... your cards Kc Qc"
    observation = extract_observation_from_ocr_text(text, hero_position="CO")

    assert observation is not None
    assert observation.hero_hand == "KcQc"
    assert observation.hero_position == "CO"
    assert observation.villain_position == "UTG"
    assert observation.villain_action == "limp"


def test_extract_observation_without_action_returns_partial_low_confidence():
    observation = extract_observation_from_ocr_text("Hero cards: KsQh", hero_position="BTN")

    assert observation is not None
    assert observation.hero_hand == "KsQh"
    assert observation.hero_position == "BTN"
    assert observation.villain_position is None
    assert observation.villain_action is None
    assert observation.confidence is not None and observation.confidence < 0.5


def test_extract_observation_returns_none_when_no_hand_found():
    observation = extract_observation_from_ocr_text("no useful ocr text", hero_position="CO")
    assert observation is None


def test_extract_observation_from_parts_uses_action_channel():
    observation = extract_observation_from_ocr_parts(
        hand_text="cards: As Ks",
        action_text="UTG all-in",
        hero_position="BTN",
    )

    assert observation is not None
    assert observation.hero_hand == "AsKs"
    assert observation.villain_position == "UTG"
    assert observation.villain_action == "all-in"


def test_load_roi_config_reads_normalized_regions(tmp_path):
    config_path = tmp_path / "roi.json"
    config_path.write_text(
        json.dumps(
            {
                "hero_hand": {"left": 0.4, "top": 0.7, "right": 0.6, "bottom": 0.85},
                "action_log": {"left": 0.05, "top": 0.2, "right": 0.4, "bottom": 0.8},
            }
        ),
        encoding="utf-8",
    )

    regions = load_roi_config(config_path)
    assert set(regions.keys()) == {"hero_hand", "action_log"}
    assert regions["hero_hand"].normalized is True
