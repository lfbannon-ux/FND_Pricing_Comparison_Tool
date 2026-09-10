"""Like-for-like pricing comparison across Floor & Decor and its competitive set."""

__version__ = "1.2.0"

BASE_RETAILER = "floor_and_decor"

RETAILERS = (
    "floor_and_decor",
    "home_depot",
    "lowes",
    "menards",
    "tile_shop",
)

RETAILER_LABELS = {
    "floor_and_decor": "Floor & Decor",
    "home_depot": "Home Depot",
    "lowes": "Lowe's",
    "menards": "Menards",
    "tile_shop": "The Tile Shop",
}

# Short codes: column prefixes in the collection worksheet, keys in the report's
# JSON payload, and abbreviations in narrow console tables.
RETAILER_CODES = {
    "floor_and_decor": "fnd",
    "home_depot": "hd",
    "lowes": "lw",
    "menards": "mnd",
    "tile_shop": "tsh",
}

# Compact labels for column headers where the full name will not fit.
RETAILER_SHORT = {
    "floor_and_decor": "F&D",
    "home_depot": "Home Depot",
    "lowes": "Lowe's",
    "menards": "Menards",
    "tile_shop": "Tile Shop",
}

COMPETITORS = tuple(r for r in RETAILERS if r != BASE_RETAILER)

# --- the active competitive set -------------------------------------------
# RETAILERS is the registry of banners the tool knows about. The *active* set
# is which of them a given run compares, so a question like "where do we stand
# without The Tile Shop" is a flag rather than a second dataset. Narrowing it
# changes what the market low is measured against, so it is a methodology
# change, not a filter - every report states the set it ran on.

_ACTIVE = list(RETAILERS)


def active_retailers():
    return tuple(_ACTIVE)


def competitors():
    return tuple(r for r in _ACTIVE if r != BASE_RETAILER)


def set_active_retailers(names) -> None:
    """Narrow the run to `names`. Floor & Decor is always included."""
    wanted = [n.strip() for n in names if n and n.strip()]
    unknown = [n for n in wanted if n not in RETAILERS]
    if unknown:
        raise ValueError(
            f"unknown retailer(s): {', '.join(unknown)}. "
            f"Known: {', '.join(RETAILERS)}"
        )
    ordered = [r for r in RETAILERS if r in set(wanted) | {BASE_RETAILER}]
    if len(ordered) < 2:
        raise ValueError("at least one competitor must remain in the active set")
    _ACTIVE[:] = ordered


def reset_retailers() -> None:
    _ACTIVE[:] = list(RETAILERS)


def label(retailer: str) -> str:
    return RETAILER_LABELS.get(retailer, retailer)


def code(retailer: str) -> str:
    return RETAILER_CODES.get(retailer, retailer)
