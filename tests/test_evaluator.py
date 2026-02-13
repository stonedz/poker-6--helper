from shortdeck_cli.evaluator import build_scenario_key, recommend_action


def test_recommend_action_all_in_returns_fold():
    scenario_key, result = recommend_action("AKs", "CO", "BTN", "all-in")
    assert scenario_key == "vs_all_in:CO_vs_BTN_all_in"
    assert result == "Dummy recommendation: Fold"


def test_recommend_action_limp_with_premium_returns_raise():
    scenario_key, result = recommend_action("AA", "UTG", "HJ", "limp")
    assert scenario_key == "vs_limp:UTG_vs_HJ_limp"
    assert result == "Dummy recommendation: Raise"


def test_recommend_action_limp_with_non_premium_returns_check():
    scenario_key, result = recommend_action("T9s", "CO", "BTN", "limp")
    assert scenario_key == "vs_limp:CO_vs_BTN_limp"
    assert result == "Dummy recommendation: Check"


def test_recommend_action_fold_returns_open():
    scenario_key, result = recommend_action("QJo", "HJ", "CO", "fold")
    assert scenario_key == "open:HJ_rfi"
    assert result == "Data recommendation: 61.8% call, 38.2% all-in (confidence: medium)"


def test_scenario_key_maps_custom_mp_positions_to_mp_bucket():
    assert build_scenario_key("MP1", "UTG", "limp") == "vs_limp:MP_vs_UTG_limp"
    assert build_scenario_key("BTN", "MP2", "all-in") == "vs_all_in:BTN_vs_MP_all_in"


def test_recommend_action_uses_utg_data_for_all_in_hand():
    scenario_key, result = recommend_action("AKo", "UTG", "CO", "fold")
    assert scenario_key == "open:UTG_rfi"
    assert result == "Data recommendation: all-in (confidence: high)"


def test_recommend_action_uses_utg_data_for_call_hand():
    scenario_key, result = recommend_action("AA", "UTG", "HJ", "fold")
    assert scenario_key == "open:UTG_rfi"
    assert result == "Data recommendation: call (confidence: high)"


def test_recommend_action_mixed_strategy_percentages(monkeypatch):
    def fake_data():
        return {
            "scenarios": {
                "open:UTG_rfi": {
                    "label": "1 - UTG RFI",
                    "hand_actions": {
                        "AQo": {"all-in": 60, "call": 40}
                    },
                    "default_recommendation": "TBD",
                }
            }
        }

    monkeypatch.setattr("shortdeck_cli.evaluator.load_strategy_data", fake_data)
    scenario_key, result = recommend_action("AQo", "UTG", "CO", "fold")
    assert scenario_key == "open:UTG_rfi"
    assert result == "Data recommendation: 60% all-in, 40% call (confidence: medium)"


def test_recommend_action_mixed_strategy_decimal_weights(monkeypatch):
    def fake_data():
        return {
            "scenarios": {
                "open:UTG_rfi": {
                    "label": "1 - UTG RFI",
                    "hand_actions": {
                        "AQo": {"all-in": 0.6, "call": 0.4}
                    },
                    "default_recommendation": "TBD",
                }
            }
        }

    monkeypatch.setattr("shortdeck_cli.evaluator.load_strategy_data", fake_data)
    scenario_key, result = recommend_action("AQo", "UTG", "CO", "fold")
    assert scenario_key == "open:UTG_rfi"
    assert result == "Data recommendation: 60% all-in, 40% call (confidence: medium)"
