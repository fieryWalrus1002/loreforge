from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import structlog
from ulid import ULID

from ingest.base import IngestResult
from models.canonical import Attack, Creature, DeadLetter
from validate.schema import coerce_int, default_hp

log = structlog.get_logger()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{ULID()}"


def _parse_attack(raw: dict[str, Any], creature_id: str) -> Attack:
    atk_bonus = raw.get("atk_bonus")
    atk = f"+{atk_bonus}" if atk_bonus is not None else ""

    short_r = raw.get("short_range")
    long_r = raw.get("long_range")
    range_str = f"{short_r}/{long_r}" if short_r is not None and long_r is not None else None

    tr_mult_raw = raw.get("trauma_mult")
    tr_mult = str(tr_mult_raw) if tr_mult_raw is not None else None

    shock_value = raw.get("shock_value")
    shock_threshold = raw.get("shock_threshold")

    return Attack(
        id=_new_id("atk"),
        creature_id=creature_id,
        name=raw.get("name", "attack"),
        atk=atk,
        num_attacks=raw.get("num_attacks", 1),
        dmg=raw.get("damage", ""),
        tr_die=raw.get("trauma_die") or None,
        tr_mult=tr_mult,
        shock_dmg=shock_value if shock_value else None,
        shock_ac=shock_threshold if shock_value else None,
        range_str=range_str,
        mag=raw.get("magazine"),
        attr=raw.get("attribute"),
        tl=raw.get("tech_level"),
        enc=raw.get("encumbrance"),
    )


class BestiaryIngestor:
    def can_handle(self, path: Path) -> bool:
        return path.name == "bestiary.json"

    def parse(self, path: Path, run_id: str) -> IngestResult:
        result = IngestResult()
        raw_entries: list[dict[str, Any]] = json.loads(path.read_text())
        result.records_read = len(raw_entries)

        for raw in raw_entries:
            name = raw.get("name", "<unnamed>")
            creature_id = _new_id("npc")
            stats = raw.get("stats", {})

            hd = coerce_int(stats.get("hd"), "hd", name)
            ac = coerce_int(stats.get("ac"), "ac", name)

            if hd is None or ac is None:
                log.error("missing_required_field", name=name, source=str(path))
                result.dead_letters.append(DeadLetter(
                    id=_new_id("dl"),
                    run_id=run_id,
                    source_file=str(path),
                    raw_content=json.dumps(raw),
                    reason="unparseable required field: hd or ac",
                ))
                result.errors += 1
                continue

            ml = coerce_int(stats.get("ml"), "ml", name)
            if ml is None:
                result.warnings += 1

            attacks = [_parse_attack(a, creature_id) for a in raw.get("attacks", [])]

            result.creatures.append(Creature(
                id=creature_id,
                name=name,
                hd=hd,
                hp=default_hp(hd),
                ac=ac,
                mv=str(stats["mv"]) if stats.get("mv") is not None else None,
                ml=ml,
                skill=str(stats["skill"]) if stats.get("skill") is not None else None,
                save=str(stats["save"]) if stats.get("save") is not None else None,
                attacks=attacks,
                source_file=str(path),
            ))

        result.records_written = len(result.creatures)
        return result
