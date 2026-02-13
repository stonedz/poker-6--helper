"""Short-deck postflop made-hand and outs analysis helpers."""

from itertools import combinations
from math import comb

RANK_ORDER = "6789TJQKA"
RANK_TO_INDEX = {rank: index for index, rank in enumerate(RANK_ORDER)}
SUITS = "shdc"

CATEGORY_NAME = {
    0: "High Card",
    1: "One Pair",
    2: "Two Pair",
    3: "Three of a Kind",
    4: "Straight",
    5: "Full House",
    6: "Flush",
    7: "Four of a Kind",
    8: "Straight Flush",
}


def full_shortdeck_deck() -> list[str]:
    return [f"{rank}{suit}" for rank in RANK_ORDER for suit in SUITS]


def _straight_high_index(cards: list[str]) -> int | None:
    indexes = {RANK_TO_INDEX[card[0]] for card in cards}
    if len(indexes) < 5:
        return None

    for start in range(0, len(RANK_ORDER) - 4):
        needed = {start, start + 1, start + 2, start + 3, start + 4}
        if needed.issubset(indexes):
            return start + 4

    wheel = {RANK_TO_INDEX["A"], RANK_TO_INDEX["6"], RANK_TO_INDEX["7"], RANK_TO_INDEX["8"], RANK_TO_INDEX["9"]}
    if wheel.issubset(indexes):
        return RANK_TO_INDEX["9"]

    return None


def _has_flush(cards: list[str]) -> bool:
    suit_counts: dict[str, int] = {}
    for card in cards:
        suit_counts[card[1]] = suit_counts.get(card[1], 0) + 1
    return any(count >= 5 for count in suit_counts.values())


def _has_four_to_flush(cards: list[str]) -> bool:
    if _has_flush(cards):
        return False
    suit_counts: dict[str, int] = {}
    for card in cards:
        suit_counts[card[1]] = suit_counts.get(card[1], 0) + 1
    return any(count == 4 for count in suit_counts.values())


def _has_straight(cards: list[str]) -> bool:
    return _straight_high_index(cards) is not None


def _has_four_to_straight(cards: list[str]) -> bool:
    if _has_straight(cards):
        return False

    indexes = {RANK_TO_INDEX[card[0]] for card in cards}
    for start in range(0, len(RANK_ORDER) - 4):
        needed = {start, start + 1, start + 2, start + 3, start + 4}
        if len(needed.intersection(indexes)) == 4:
            return True

    wheel = {RANK_TO_INDEX["A"], RANK_TO_INDEX["6"], RANK_TO_INDEX["7"], RANK_TO_INDEX["8"], RANK_TO_INDEX["9"]}
    if len(wheel.intersection(indexes)) == 4:
        return True

    return False


def _evaluate_five(cards: list[str]) -> tuple:
    rank_counts: dict[str, int] = {}
    for card in cards:
        rank_counts[card[0]] = rank_counts.get(card[0], 0) + 1

    sorted_groups = sorted(
        ((count, RANK_TO_INDEX[rank]) for rank, count in rank_counts.items()),
        key=lambda item: (item[0], item[1]),
        reverse=True,
    )

    is_flush = len({card[1] for card in cards}) == 1
    straight_high = _straight_high_index(cards)
    is_straight = straight_high is not None

    if is_straight and is_flush:
        return (8, straight_high)

    if sorted_groups[0][0] == 4:
        four_rank = sorted_groups[0][1]
        kicker = max(rank for count, rank in sorted_groups if count == 1)
        return (7, four_rank, kicker)

    if sorted_groups[0][0] == 3 and sorted_groups[1][0] == 2:
        return (5, sorted_groups[0][1], sorted_groups[1][1])

    if is_flush:
        ranks = sorted((RANK_TO_INDEX[card[0]] for card in cards), reverse=True)
        return (6, *ranks)

    if is_straight:
        return (4, straight_high)

    if sorted_groups[0][0] == 3:
        trip = sorted_groups[0][1]
        kickers = sorted((rank for count, rank in sorted_groups if count == 1), reverse=True)
        return (3, trip, *kickers)

    if sorted_groups[0][0] == 2 and sorted_groups[1][0] == 2:
        high_pair = max(sorted_groups[0][1], sorted_groups[1][1])
        low_pair = min(sorted_groups[0][1], sorted_groups[1][1])
        kicker = max(rank for count, rank in sorted_groups if count == 1)
        return (2, high_pair, low_pair, kicker)

    if sorted_groups[0][0] == 2:
        pair = sorted_groups[0][1]
        kickers = sorted((rank for count, rank in sorted_groups if count == 1), reverse=True)
        return (1, pair, *kickers)

    ranks = sorted((RANK_TO_INDEX[card[0]] for card in cards), reverse=True)
    return (0, *ranks)


def best_hand_strength(cards: list[str]) -> tuple:
    return max(_evaluate_five(list(combo)) for combo in combinations(cards, 5))


def hand_name_from_strength(strength: tuple) -> str:
    return CATEGORY_NAME[strength[0]]


def analyze_flop(hole_cards: list[str], flop_cards: list[str]) -> dict:
    known_cards = hole_cards + flop_cards
    current_strength = best_hand_strength(known_cards)
    deck = [card for card in full_shortdeck_deck() if card not in set(known_cards)]

    turn_outs = 0
    turn_out_details: list[dict[str, str]] = []
    four_to_straight_cards: list[str] = []
    four_to_flush_cards: list[str] = []
    for turn_card in deck:
        cards_after_turn = known_cards + [turn_card]
        strength_after_turn = best_hand_strength(cards_after_turn)
        if strength_after_turn > current_strength:
            turn_outs += 1
            turn_out_details.append(
                {
                    "card": turn_card,
                    "made_hand": hand_name_from_strength(strength_after_turn),
                }
            )
        else:
            if _has_four_to_straight(cards_after_turn):
                four_to_straight_cards.append(turn_card)
            if _has_four_to_flush(cards_after_turn):
                four_to_flush_cards.append(turn_card)

    total_turn_cards = len(deck)
    turn_outs_pct = (turn_outs * 100.0 / total_turn_cards) if total_turn_cards else 0.0

    success_by_river = 0
    total_by_river = comb(len(deck), 2)
    for turn_card, river_card in combinations(deck, 2):
        final_strength = best_hand_strength(known_cards + [turn_card, river_card])
        if final_strength > current_strength:
            success_by_river += 1

    improve_by_river_pct = (success_by_river * 100.0 / total_by_river) if total_by_river else 0.0

    return {
        "made_hand": hand_name_from_strength(current_strength),
        "turn_outs": turn_outs,
        "turn_total": total_turn_cards,
        "turn_outs_pct": turn_outs_pct,
        "improve_by_river_pct": improve_by_river_pct,
        "turn_out_details": turn_out_details,
        "four_to_straight_cards": four_to_straight_cards,
        "four_to_flush_cards": four_to_flush_cards,
    }


def analyze_turn(hole_cards: list[str], flop_cards: list[str], turn_card: str) -> dict:
    known_cards = hole_cards + flop_cards + [turn_card]
    current_strength = best_hand_strength(known_cards)
    deck = [card for card in full_shortdeck_deck() if card not in set(known_cards)]

    river_outs = 0
    river_out_details: list[dict[str, str]] = []
    for river_card in deck:
        final_strength = best_hand_strength(known_cards + [river_card])
        if final_strength > current_strength:
            river_outs += 1
            river_out_details.append(
                {
                    "card": river_card,
                    "made_hand": hand_name_from_strength(final_strength),
                }
            )

    total_river_cards = len(deck)
    river_outs_pct = (river_outs * 100.0 / total_river_cards) if total_river_cards else 0.0

    return {
        "made_hand": hand_name_from_strength(current_strength),
        "river_outs": river_outs,
        "river_total": total_river_cards,
        "river_outs_pct": river_outs_pct,
        "river_out_details": river_out_details,
    }
