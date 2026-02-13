from shortdeck_cli.postflop import analyze_flop, analyze_turn


def test_analyze_flop_returns_expected_fields():
    result = analyze_flop(["As", "Ad"], ["Ks", "Qh", "Td"])
    assert "made_hand" in result
    assert "turn_outs" in result
    assert "turn_total" in result
    assert "turn_outs_pct" in result
    assert "improve_by_river_pct" in result
    assert "turn_out_details" in result
    assert "four_to_straight_cards" in result
    assert "four_to_flush_cards" in result
    assert isinstance(result["turn_out_details"], list)
    assert isinstance(result["four_to_straight_cards"], list)
    assert isinstance(result["four_to_flush_cards"], list)
    if result["turn_out_details"]:
        assert {"card", "made_hand"}.issubset(result["turn_out_details"][0].keys())
    assert result["turn_total"] > 0


def test_analyze_turn_returns_expected_fields():
    result = analyze_turn(["As", "Ad"], ["Ks", "Qh", "Td"], "9c")
    assert "made_hand" in result
    assert "river_outs" in result
    assert "river_total" in result
    assert "river_outs_pct" in result
    assert "river_out_details" in result
    assert isinstance(result["river_out_details"], list)
    if result["river_out_details"]:
        assert {"card", "made_hand"}.issubset(result["river_out_details"][0].keys())
    assert result["river_total"] > 0
