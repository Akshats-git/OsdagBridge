"""theme.py is the single source of styling; check it is self-consistent."""
import re

from osdagbridge.core.reports import theme as T


def test_palette_values_are_six_digit_hex():
    for name, hexv in T.LATEX_COLORS.items():
        assert re.fullmatch(r"[0-9A-Fa-f]{6}", hexv), name


def test_ur_rule_is_inclusive_at_limit():
    assert T.ur_passes(T.UR_LIMIT)
    assert T.ur_passes(0.0)
    assert not T.ur_passes(T.UR_LIMIT + 1e-9)


def test_fmt_never_turns_missing_into_zero():
    assert T.fmt(None) == T.MISSING
    assert T.fmt("") == T.MISSING
    assert T.fmt("abc") == T.MISSING
    assert T.fmt(0) == "0.00"
    assert T.fmt(1.2345, 3) == "1.234" or T.fmt(1.2345, 3) == "1.235"


def test_unicode_map_has_unique_codepoints():
    cps = [cp for cp, _ in T.UNICODE_MAP]
    assert len(cps) == len(set(cps))


def test_mpl_rc_is_a_plain_dict_and_does_not_pick_a_backend():
    rc = T.mpl_rc()
    assert isinstance(rc, dict) and "backend" not in rc
