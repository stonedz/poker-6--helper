"""Interactive CLI flow for the Short Deck test app."""

from shortdeck_cli.evaluator import recommend_action
from shortdeck_cli.parser import parse_action, parse_flop_cards, parse_hand, parse_position, parse_turn_card
from shortdeck_cli.postflop import analyze_flop, analyze_turn
from shortdeck_cli.rules import ACTIONS, POSITIONS, previous_positions


ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_CYAN = "\033[36m"
ANSI_GREEN = "\033[32m"
ANSI_YELLOW = "\033[33m"
ANSI_RED = "\033[31m"

RANK_ORDER = "AKQJT9876"


def _color_for_recommendation(recommendation: str) -> str:
    lowered = recommendation.lower()
    if "confidence: high" in lowered:
        return ANSI_GREEN
    if "confidence: medium" in lowered:
        return ANSI_YELLOW
    if "confidence: low" in lowered:
        return ANSI_RED
    return ANSI_CYAN


def _read_input(prompt: str) -> str | None:
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt, StopIteration):
        return None


def _ask_until_valid(prompt: str, parser, allow_reset: bool = False):
    while True:
        raw_value = _read_input(prompt)
        if raw_value is None:
            return None
        if allow_reset and raw_value.strip() == "00":
            return "__RESET__"
        try:
            return parser(raw_value)
        except ValueError as error:
            print(f"Invalid input: {error}")


def _ask_hero_position() -> str | None:
    print("Hero position options:")
    for index, position in enumerate(POSITIONS, start=1):
        print(f"  {index}) {position}")

    def parse_hero_position(raw_value: str) -> str:
        value = raw_value.strip()
        if value.isdigit():
            index = int(value)
            if 1 <= index <= len(POSITIONS):
                return POSITIONS[index - 1]
        return parse_position(raw_value)

    return _ask_until_valid("Your position (# or name): ", parse_hero_position)


def _ask_villain_position(hero_position: str) -> str | None:
    valid_previous_positions = previous_positions(hero_position)
    option_map = {str(index): position for index, position in enumerate(valid_previous_positions, start=1)}
    print("Villain position options:")
    for index, position in option_map.items():
        print(f"  {index}) {position}")

    def parse_villain_position(raw_value: str) -> str:
        value = raw_value.strip()
        if value in option_map:
            return option_map[value]
        return parse_position(raw_value, allowed_positions=valid_previous_positions)

    return _ask_until_valid("Other player position (# or name): ", parse_villain_position)


def _ask_villain_action() -> str | None:
    action_map = {str(index): action for index, action in enumerate(ACTIONS, start=1)}
    print("Villain action options:")
    for index, action in action_map.items():
        print(f"  {index}) {action}")

    def parse_villain_action(raw_value: str) -> str:
        value = raw_value.strip()
        if value in action_map:
            return action_map[value]
        return parse_action(raw_value)

    return _ask_until_valid("Other player action (# or name): ", parse_villain_action)


def _format_pct(value: float) -> str:
    rounded = round(value, 1)
    if rounded.is_integer():
        return str(int(rounded))
    return f"{rounded:.1f}"


def _print_out_details(title: str, details: list[dict[str, str]], total_cards: int) -> None:
    if not details:
        print(f"{title}: none")
        return

    grouped: dict[str, list[str]] = {}
    for item in details:
        made_hand = item["made_hand"]
        grouped.setdefault(made_hand, []).append(item["card"])

    print(f"{title}:")
    for made_hand, cards in grouped.items():
        pct = (len(cards) * 100.0 / total_cards) if total_cards else 0.0
        print(f"  - {made_hand} ({len(cards)}, {_format_pct(pct)}%): {' '.join(cards)}")


def _print_draw_cards(title: str, cards: list[str], total_cards: int) -> None:
    if not cards:
        print(f"{title}: none")
        return
    pct = (len(cards) * 100.0 / total_cards) if total_cards else 0.0
    print(f"{title} ({len(cards)}, {_format_pct(pct)}%): {' '.join(cards)}")


def _ask_optional_flop(hole_cards: list[str]) -> list[str] | None:
    while True:
        raw_flop = _read_input("Flop 3 cards (e.g. KsQhTd or KpQcTf) [Enter to skip]: ")
        if raw_flop is None:
            return None
        if raw_flop.strip() == "":
            return []
        try:
            return parse_flop_cards(raw_flop, blocked_cards=hole_cards)
        except ValueError as error:
            print(f"Invalid input: {error}")


def _ask_optional_turn(hole_cards: list[str], flop_cards: list[str]) -> str | None:
    while True:
        raw_turn = _read_input("Turn card (e.g. 9c or 9q) [Enter to finish hand]: ")
        if raw_turn is None:
            return None
        if raw_turn.strip() == "":
            return ""
        try:
            return parse_turn_card(raw_turn, blocked_cards=hole_cards + flop_cards)
        except ValueError as error:
            print(f"Invalid input: {error}")


def _strategy_hand_from_explicit(hero_hand: str) -> str:
    first = hero_hand[:2]
    second = hero_hand[2:]
    rank_one, suit_one = first[0], first[1]
    rank_two, suit_two = second[0], second[1]

    if rank_one == rank_two:
        return f"{rank_one}{rank_two}"

    ordered = sorted([rank_one, rank_two], key=lambda rank: RANK_ORDER.index(rank))
    suitedness = "s" if suit_one == suit_two else "o"
    return f"{ordered[0]}{ordered[1]}{suitedness}"


def main() -> None:
    print("=== Short Deck (6+) Test CLI ===")
    print("Play runs continuously hand by hand.")
    print("Hero position is entered every hand.")
    print("Use 00 when entering hand to reset and start a fresh hand.")
    print()

    while True:
        print("\n=== New Hand ===")
        hero_hand = _ask_until_valid("Your starting hand (AA, AKs, T9o, AsAd) or 00 to reset: ", parse_hand, allow_reset=True)

        if hero_hand is None:
            print("\nSession ended.")
            return

        if hero_hand == "__RESET__":
            print("\nReset requested.")
            continue

        hero_position = _ask_hero_position()
        if hero_position is None:
            print("\nSession ended.")
            return

        if hero_position == "UTG":
            villain_position = "UTG"
            villain_action = "fold"
            print("UTG turn: no prior player action. Using automatic UTG RFI scenario.")
        else:
            print("Now enter the other player's info.")
            villain_position = _ask_villain_position(hero_position)
            if villain_position is None:
                print("\nSession ended.")
                return
            villain_action = _ask_villain_action()
            if villain_action is None:
                print("\nSession ended.")
                return

        strategy_hand = hero_hand
        explicit_hole = len(hero_hand) == 4 and hero_hand[1].islower() and hero_hand[3].islower()
        if explicit_hole:
            strategy_hand = _strategy_hand_from_explicit(hero_hand)

        scenario_key, recommendation = recommend_action(
            hero_hand=strategy_hand,
            hero_position=hero_position,
            villain_position=villain_position,
            villain_action=villain_action,
        )

        print("\n--- Scenario ---")
        print(f"Hero: {hero_hand} @ {hero_position}")
        if hero_position == "UTG":
            print("Villain: N/A (UTG open spot)")
        else:
            print(f"Villain: {villain_position} did {villain_action}")
        print(f"Scenario key: {scenario_key}")
        print("\n>>> RECOMMENDATION <<<")
        rec_color = _color_for_recommendation(recommendation)
        print(f"{ANSI_BOLD}{rec_color}{recommendation}{ANSI_RESET}")
        print(">>>>>>>>>>>>>>>>>>>>>>")
        print("(When data is set from TBD to real actions, this becomes data-driven.)")

        if explicit_hole:
            hole_cards = [hero_hand[:2], hero_hand[2:]]
            flop_cards = _ask_optional_flop(hole_cards)
            if flop_cards is None:
                print("\nSession ended.")
                return

            if flop_cards:
                flop_analysis = analyze_flop(hole_cards, flop_cards)
                print("\n--- Postflop (Flop) ---")
                print(f"Board: {' '.join(flop_cards)}")
                print(f"Made hand: {flop_analysis['made_hand']}")
                print(
                    f"Turn outs: {flop_analysis['turn_outs']}/{flop_analysis['turn_total']} "
                    f"({_format_pct(flop_analysis['turn_outs_pct'])}%)"
                )
                _print_out_details("Turn out cards", flop_analysis["turn_out_details"], flop_analysis["turn_total"])
                print("Draw cards (excluded from Turn outs %):")
                _print_draw_cards("  4/5 Straight", flop_analysis["four_to_straight_cards"], flop_analysis["turn_total"])
                _print_draw_cards("  4/5 Flush", flop_analysis["four_to_flush_cards"], flop_analysis["turn_total"])
                print(f"Improve by river (2 cards): {_format_pct(flop_analysis['improve_by_river_pct'])}%")

                turn_card = _ask_optional_turn(hole_cards, flop_cards)
                if turn_card is None:
                    print("\nSession ended.")
                    return

                if turn_card:
                    turn_analysis = analyze_turn(hole_cards, flop_cards, turn_card)
                    print("\n--- Postflop (Turn) ---")
                    print(f"Board: {' '.join(flop_cards + [turn_card])}")
                    print(f"Made hand: {turn_analysis['made_hand']}")
                    print(
                        f"River outs: {turn_analysis['river_outs']}/{turn_analysis['river_total']} "
                        f"({_format_pct(turn_analysis['river_outs_pct'])}%)"
                    )
                    _print_out_details("River out cards", turn_analysis["river_out_details"], turn_analysis["river_total"])


if __name__ == "__main__":
    main()
