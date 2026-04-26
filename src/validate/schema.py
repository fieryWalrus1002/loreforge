from __future__ import annotations

import math
import re
from typing import Any

import structlog

log = structlog.get_logger()


def coerce_int(value: object, field: str, record_id: str) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            result = int(value)
            log.warning("field_coerced", field=field, record_id=record_id, original=value)
            return result
        except ValueError:
            log.error("field_coerce_failed", field=field, record_id=record_id, value=value)
            return None
    return None


def default_hp(hd: int) -> int:
    return math.floor(4.5 * hd)


def remap_attack_fields(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize variant field names to canonical names, logging each remap."""
    remapped = dict(raw)
    if "t_die" in remapped and "tr_die" not in remapped:
        remapped["tr_die"] = remapped.pop("t_die")
        log.warning("field_remapped", from_field="t_die", to_field="tr_die")
    if "t_rate" in remapped and "tr_mult" not in remapped:
        remapped["tr_mult"] = remapped.pop("t_rate")
        log.warning("field_remapped", from_field="t_rate", to_field="tr_mult")
    return remapped


def normalize_tr(raw: str) -> str:
    """Normalize dN/xM → 1dN/xM (PDF sources sometimes drop the leading 1)."""
    if re.match(r'^d\d+/', raw):
        return "1" + raw
    return raw


def strip_annotation(raw: str, record_id: str) -> str:
    """Strip asterisk footnote markers from stat values, logging a warning."""
    if "*" in raw:
        cleaned = raw.replace("*", "")
        log.warning("annotation_stripped", record_id=record_id, original=raw, cleaned=cleaned)
        return cleaned
    return raw
