from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import structlog
from ulid import ULID

from ingest.base import IngestResult
from models.canonical import Attack, Character, DeadLetter

log = structlog.get_logger()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{ULID()}"


def _parse_attack(raw: dict[str, Any], character_id: str) -> Attack:
    shock_raw = raw.get("shock", "-") or "-"
    shock_dmg = None
    if shock_raw != "-":
        try:
            shock_dmg = int(shock_raw.split("/")[0])
        except (ValueError, IndexError):
            pass

    return Attack(
        id=_new_id("atk"),
        character_id=character_id,
        name=raw.get("name", "attack"),
        atk=raw.get("atk", ""),
        dmg=raw.get("dmg", ""),
        tr_die=raw.get("tr_die") or None,
        tr_mult=raw.get("tr_mult") or None,
        shock_dmg=shock_dmg,
        range_str=raw.get("range"),
    )


class RosterIngestor:
    def can_handle(self, path: Path) -> bool:
        return path.name == "roster.json"

    def parse(self, path: Path, run_id: str) -> IngestResult:
        result = IngestResult()
        raw_entries: list[dict[str, Any]] = json.loads(path.read_text())
        result.records_read = len(raw_entries)

        for raw in raw_entries:
            source_id = raw.get("id", "")
            name = raw.get("name", "")

            missing = (
                not name
                or raw.get("hp") is None
                or raw.get("max_hp") is None
                or raw.get("ac") is None
            )
            if missing:
                log.error("missing_required_field", source_id=source_id, source=str(path))
                result.dead_letters.append(DeadLetter(
                    id=_new_id("dl"),
                    run_id=run_id,
                    source_file=str(path),
                    raw_content=json.dumps(raw),
                    reason="missing required field: name, hp, max_hp, or ac",
                ))
                result.errors += 1
                continue

            is_pc = bool(raw.get("is_pc", False))
            character_id = _new_id("pc" if is_pc else "npc")
            attacks = [_parse_attack(a, character_id) for a in raw.get("attacks", [])]

            result.characters.append(Character(
                id=character_id,
                source_id=source_id or None,
                name=name,
                is_pc=is_pc,
                hp=int(raw["hp"]),
                max_hp=int(raw["max_hp"]),
                system_strain=int(raw.get("system_strain", 0)),
                ac=int(raw["ac"]),
                attributes={k: int(v) for k, v in raw.get("attributes", {}).items()},
                skill=raw.get("skill"),
                initiative_mod=int(raw.get("initiative_mod", 0)),
                attacks=attacks,
                source_file=str(path),
            ))

        result.records_written = len(result.characters)
        return result
