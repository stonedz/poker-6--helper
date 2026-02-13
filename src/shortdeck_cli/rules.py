"""Shared constants and rules for the Short Deck CLI MVP."""

POSITIONS = ("UTG", "MP1", "MP2", "HJ", "CO", "BTN")
ACTIONS = ("fold", "limp", "all-in")
RANKS = "AKQJT9876"


def previous_positions(position: str) -> tuple[str, ...]:
	index = POSITIONS.index(position)
	return POSITIONS[:index]
