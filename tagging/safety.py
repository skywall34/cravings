"""Safety and dietary flag bitmask computation."""

SAFETY_FLAGS = {
    "raw_fish": 0,
    "raw_egg": 1,
    "raw_meat": 2,
    "unpasteurized_dairy": 3,
    "high_mercury_fish": 4,
}

DIETARY_FLAGS = {
    "vegetarian": 0,
    "vegan": 1,
    "gluten_free": 2,
    "dairy_free": 3,
    "halal": 4,
    "kosher": 5,
    "contains_nuts": 6,
    "contains_shellfish": 7,
    "contains_soy": 8,
    "contains_eggs": 9,
}


def compute_safety_bitmask(flags: list[str]) -> int:
    mask = 0
    for flag in flags:
        bit = SAFETY_FLAGS.get(flag)
        if bit is not None:
            mask |= (1 << bit)
    return mask


def compute_dietary_bitmask(flags: list[str]) -> int:
    mask = 0
    for flag in flags:
        bit = DIETARY_FLAGS.get(flag)
        if bit is not None:
            mask |= (1 << bit)
    return mask


def has_safety_flag(bitmask: int, flag: str) -> bool:
    bit = SAFETY_FLAGS.get(flag)
    if bit is None:
        return False
    return bool(bitmask & (1 << bit))


def has_dietary_flag(bitmask: int, flag: str) -> bool:
    bit = DIETARY_FLAGS.get(flag)
    if bit is None:
        return False
    return bool(bitmask & (1 << bit))


def dietary_list_from_bitmask(mask: int) -> list[str]:
    return [name for name, bit in DIETARY_FLAGS.items() if mask & (1 << bit)]


def safety_list_from_bitmask(mask: int) -> list[str]:
    return [name for name, bit in SAFETY_FLAGS.items() if mask & (1 << bit)]


_ALL_SAFETY_BITS = (1 << len(SAFETY_FLAGS)) - 1


def user_safety_mask(safety_overrides_bitmask: int) -> int:
    """Effective safety filter mask: all hard-safety flags minus user overrides."""
    return _ALL_SAFETY_BITS & ~safety_overrides_bitmask


def build_dietary_filter_clauses(dietary_restrictions: list[str]) -> tuple[list[str], list[int]]:
    """Return (WHERE clauses, bind args) for dietary restriction filtering.

    contains_* flags: item must NOT have the bit (allergen exclusion).
    All other flags: item MUST have the bit (positive certification).
    """
    clauses: list[str] = []
    args: list[int] = []
    for r in (dietary_restrictions or []):
        bit = DIETARY_FLAGS.get(r)
        if bit is None:
            continue
        mask = 1 << bit
        if r.startswith("contains_"):
            clauses.append("(dietary_flags_bitmask & ?) = 0")
        else:
            clauses.append("(dietary_flags_bitmask & ?) != 0")
        args.append(mask)
    return clauses, args


