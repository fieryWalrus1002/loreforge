from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import structlog
from ulid import ULID

from ingest.base import IngestResult
from models.canonical import Attack, Creature, DeadLetter
from validate.schema import coerce_int, default_hp, remap_attack_fields

log = structlog.get_logger()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{ULID()}"


def _parse_attack(raw: dict[str, Any], creature_id: str) -> Attack:
    raw = remap_attack_fields(raw)

    shock_raw = raw.get("shock", "-") or "-"
    shock_dmg, shock_ac = None, None
    if shock_raw != "-":
        parts = shock_raw.split("/")
        try:
            shock_dmg = int(parts[0])
        except (ValueError, IndexError):
            pass

    return Attack(
        id=_new_id("atk"),
        creature_id=creature_id,
        name=raw.get("name", "attack"),
        atk=raw.get("atk", ""),
        dmg=raw.get("dmg", ""),
        tr_die=raw.get("tr_die") or None,
        tr_mult=raw.get("tr_mult") or None,
        shock_dmg=shock_dmg,
        shock_ac=shock_ac,
        range_str=raw.get("range"),
        mag=int(raw["mag"]) if raw.get("mag") is not None else None,
        attr=raw.get("attr"),
        tl=int(raw["tl"]) if raw.get("tl") is not None else None,
        enc=int(raw["enc"]) if raw.get("enc") is not None else None,
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

            hd = coerce_int(raw.get("hd"), "hd", name)
            ac = coerce_int(raw.get("ac"), "ac", name)

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

            ml = coerce_int(raw.get("ml"), "ml", name)
            if ml is None:
                result.warnings += 1

            attacks = [_parse_attack(a, creature_id) for a in raw.get("attacks", [])]

            result.creatures.append(Creature(
                id=creature_id,
                name=name,
                hd=hd,
                hp=default_hp(hd),
                ac=ac,
                mv=raw.get("mv"),
                ml=ml,
                skill=raw.get("skill"),
                save=raw.get("save"),
                attacks=attacks,
                source_file=str(path),
            ))

        result.records_written = len(result.creatures)
        return result
