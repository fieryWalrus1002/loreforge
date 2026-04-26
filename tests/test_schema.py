from validate.schema import (
    coerce_int,
    default_hp,
    normalize_tr,
    remap_attack_fields,
    strip_annotation,
)


def test_coerce_int_passes_through_native_int():
    assert coerce_int(6, "hd", "Beast") == 6


def test_coerce_int_converts_string_digit():
    assert coerce_int("6", "hd", "Beast") == 6


def test_coerce_int_returns_none_for_non_numeric_string():
    assert coerce_int("bad", "hd", "Beast") is None


def test_default_hp_floors_result():
    assert default_hp(1) == 4   # floor(4.5) = 4
    assert default_hp(3) == 13  # floor(13.5) = 13
    assert default_hp(4) == 18  # floor(18.0) = 18


def test_normalize_tr_prepends_1_to_bare_die():
    assert normalize_tr("d8/x2") == "1d8/x2"
    assert normalize_tr("d10/x3") == "1d10/x3"


def test_normalize_tr_leaves_correct_format_unchanged():
    assert normalize_tr("1d8/x2") == "1d8/x2"


def test_strip_annotation_removes_asterisk():
    assert strip_annotation("+7*", "Beast") == "+7"
    assert strip_annotation("2d6*", "Beast") == "2d6"


def test_strip_annotation_leaves_clean_values_unchanged():
    assert strip_annotation("+6", "Beast") == "+6"


def test_remap_attack_fields_renames_t_die():
    raw = {"t_die": "1d6", "dmg": "1d6"}
    result = remap_attack_fields(raw)
    assert "tr_die" in result
    assert "t_die" not in result


def test_remap_attack_fields_renames_t_rate():
    raw = {"t_rate": "x2", "dmg": "1d6"}
    result = remap_attack_fields(raw)
    assert "tr_mult" in result
    assert "t_rate" not in result


def test_remap_attack_fields_does_not_overwrite_existing_canonical_field():
    raw = {"t_die": "1d4", "tr_die": "1d6"}
    result = remap_attack_fields(raw)
    assert result["tr_die"] == "1d6"  # existing canonical value preserved
