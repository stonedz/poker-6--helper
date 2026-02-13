import pytest

from shortdeck_cli.parser import parse_action, parse_flop_cards, parse_hand, parse_position, parse_turn_card


@pytest.mark.parametrize(
    "raw_value,expected",
    [
        ("AA", "AA"),
        ("aks", "AKs"),
        ("t9o", "T9o"),
    ],
)
def test_parse_hand_valid(raw_value, expected):
    assert parse_hand(raw_value) == expected


@pytest.mark.parametrize("raw_value", ["A5s", "AK", "AAA", "KKo", "54s"])
def test_parse_hand_invalid(raw_value):
    with pytest.raises(ValueError):
        parse_hand(raw_value)


def test_parse_position_valid():
    assert parse_position("mp1") == "MP1"


def test_parse_position_invalid():
    with pytest.raises(ValueError):
        parse_position("SB")


def test_parse_action_valid():
    assert parse_action("ALL-IN") == "all-in"


def test_parse_action_invalid():
    with pytest.raises(ValueError):
        parse_action("raise")


def test_parse_hand_explicit_cards_valid():
    assert parse_hand("AsAd") == "AsAd"


def test_parse_hand_explicit_cards_valid_italian_suits():
    assert parse_hand("ApAc") == "AsAh"


def test_parse_flop_cards_valid_italian_suits():
    assert parse_flop_cards("KpQcTf", blocked_cards=["As", "Ad"]) == ["Ks", "Qh", "Tc"]


def test_parse_hand_explicit_cards_invalid_duplicate():
    with pytest.raises(ValueError):
        parse_hand("AsAs")


def test_parse_flop_cards_valid():
    assert parse_flop_cards("KsQhTd", blocked_cards=["As", "Ad"]) == ["Ks", "Qh", "Td"]


def test_parse_turn_card_blocked_invalid():
    with pytest.raises(ValueError):
        parse_turn_card("As", blocked_cards=["As", "Ad", "Ks", "Qh", "Td"])
