"""Parsing and validation helpers for CLI input."""

from shortdeck_cli.rules import ACTIONS, POSITIONS, RANKS


def _extract_cards(raw_value: str) -> list[str]:
    compact = raw_value.replace(" ", "").replace(",", "")
    if len(compact) % 2 != 0:
        raise ValueError("Card format must use rank+suit pairs (example: AsAd or KsQhTd).")
    cards = [compact[index:index + 2] for index in range(0, len(compact), 2)]

    raw_suits = [card[1].lower() for card in cards if len(card) == 2]
    italian_mode = any(suit in {"p", "q", "f"} for suit in raw_suits)

    def normalize_suit(suit: str) -> str:
        if suit == "p":
            return "s"
        if suit == "q":
            return "d"
        if suit == "f":
            return "c"
        if suit == "c":
            return "h" if italian_mode else "c"
        if suit in {"s", "h", "d"}:
            return suit
        raise ValueError("Card suits must be one of: s, h, d, c or italian p, c, q, f.")

    normalized: list[str] = []
    for card in cards:
        if len(card) != 2:
            raise ValueError("Card format must use rank+suit pairs (example: AsAd or KsQhTd).")
        rank, suit = card[0].upper(), card[1].lower()
        if rank not in RANKS:
            raise ValueError("Card ranks must be in A,K,Q,J,T,9,8,7,6.")
        normalized_suit = normalize_suit(suit)
        normalized.append(f"{rank}{normalized_suit}")
    if len(set(normalized)) != len(normalized):
        raise ValueError("Duplicate cards are not allowed.")
    return normalized


def parse_hand(raw_value: str) -> str:
    raw = raw_value.strip()
    value = raw.upper()

    if len(value) == 2:
        first, second = value[0], value[1]
        if first not in RANKS or second not in RANKS:
            raise ValueError("Hand ranks must be in A,K,Q,J,T,9,8,7,6.")
        if first != second:
            raise ValueError("Non-pair hands must include suitedness suffix: s or o (example: AKs, T9o).")
        return value

    if len(value) == 3:
        first, second, suitedness = value[0], value[1], value[2]
        if first not in RANKS or second not in RANKS:
            raise ValueError("Hand ranks must be in A,K,Q,J,T,9,8,7,6.")
        if first == second:
            raise ValueError("Pairs should be entered as two letters only (example: AA).")
        if suitedness not in ("S", "O"):
            raise ValueError("Non-pair hands must end with s or o (example: AKs, T9o).")
        return f"{first}{second}{suitedness.lower()}"

    try:
        cards = _extract_cards(raw)
        if len(cards) == 2:
            return "".join(cards)
    except ValueError:
        pass

    raise ValueError("Invalid hand format. Use AA, AKs, or T9o style formats.")


def parse_position(raw_value: str, allowed_positions: tuple[str, ...] | None = None) -> str:
    valid_positions = allowed_positions or POSITIONS
    value = raw_value.strip().upper()
    if value not in valid_positions:
        raise ValueError(f"Position must be one of: {', '.join(valid_positions)}")
    return value


def parse_action(raw_value: str) -> str:
    value = raw_value.strip().lower()
    if value not in ACTIONS:
        raise ValueError(f"Action must be one of: {', '.join(ACTIONS)}")
    return value


def parse_flop_cards(raw_value: str, blocked_cards: list[str]) -> list[str]:
    cards = _extract_cards(raw_value)
    if len(cards) != 3:
        raise ValueError("Flop must contain exactly 3 cards (example: KsQhTd).")
    blocked = set(blocked_cards)
    overlap = blocked.intersection(cards)
    if overlap:
        raise ValueError(f"Flop cards overlap with known cards: {', '.join(sorted(overlap))}")
    return cards


def parse_turn_card(raw_value: str, blocked_cards: list[str]) -> str:
    cards = _extract_cards(raw_value)
    if len(cards) != 1:
        raise ValueError("Turn must contain exactly 1 card (example: 9c).")
    card = cards[0]
    if card in set(blocked_cards):
        raise ValueError(f"Turn card overlaps with known cards: {card}")
    return card
