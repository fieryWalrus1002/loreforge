from __future__ import annotations

import math
import re
from pathlib import Path

import structlog
from ulid import ULID

from ingest.base import IngestResult
from models.canonical import Attack, Creature, DeadLetter
from validate.schema import normalize_tr, strip_annotation

log = structlog.get_logger()

_PLACEHOLDER_VALUES = {"by", "wpn", "weapon"}


def _new_id(prefix: str) -> str:
    return f"{prefix}_{ULID()}"


def _parse_atk(raw: str, name: str) -> tuple[str, int]:
    """'+6x2' → ('+6', 2), '+7*' → ('+7', 1) with warning."""
    raw = strip_annotation(raw, name)
    m = re.match(r'^([+-]\d+)(?:x(\d+))?$', raw)
    if not m:
        raise ValueError(f"Cannot parse atk: {raw!r}")
    return m.group(1), int(m.group(2)) if m.group(2) else 1


def _parse_dmg(dmg_raw: str, dmg_type_token: str | None, name: str) -> tuple[str, str | None, bool]:
    """Parse damage field. Returns (dmg, dmg_type, poison)."""
    dmg_raw = strip_annotation(dmg_raw, name)
    poison = False
    dmg = dmg_raw.rstrip("+").strip()
    if dmg.endswith("+poison"):
        dmg = dmg[:-7]
        poison = True
    dmg_type = dmg_type_token.strip() if dmg_type_token else None
    return dmg, dmg_type, poison


def _parse_tr(raw: str) -> tuple[str | None, str | None]:
    """'1d8/x2' or 'd8/x2' → ('1d8', 'x2'), '-' → (None, None)."""
    if raw == "-":
        return None, None
    raw = normalize_tr(raw)
    m = re.match(r'^(\d+d\d+)/(x\d+)$', raw)
    if not m:
        return None, None
    return m.group(1), m.group(2)


def _parse_shock(raw: str) -> tuple[int | None, int | None]:
    """'3/-' → (3, None), '-' → (None, None). Two-token 'N/AC M' handled by caller."""
    if raw == "-":
        return None, None
    m = re.match(r'^(\d+)/-$', raw)
    if m:
        return int(m.group(1)), None
    return None, None


def _is_placeholder(token: str) -> bool:
    return token.lower() in _PLACEHOLDER_VALUES


def _is_header_line(line: str) -> bool:
    return bool(re.search(r'\bHD\b.*\bAC\b.*\bAtk\b', line))


def _looks_like_data_row(line: str) -> bool:
    """Stat rows end with a save target like '14+'. Dice notation is not required
    because some rows use placeholder values (e.g. 'By wpn') instead of dice."""
    return bool(re.search(r'\d+\+$', line.strip()))


def _parse_stat_row(line: str, run_id: str, source_file: str) -> Creature | DeadLetter:
    tokens = line.split()
    original = line

    try:
        save = tokens.pop()    # "15+"
        skill = tokens.pop()   # "+2"
        ml_raw = tokens.pop()  # "7"
        mv = tokens.pop()      # "10m"

        # Shock: single token ("-", "3/-"), two-token "N/AC M", or "By wpn" placeholder
        if len(tokens) >= 2 and re.match(r'^\d+/AC$', tokens[-2]):
            shock_ac_val = int(tokens.pop())
            shock_prefix = tokens.pop()
            shock_dmg, shock_ac = int(shock_prefix.split("/")[0]), shock_ac_val
        else:
            shock_raw = tokens.pop()
            if _is_placeholder(shock_raw) and tokens and _is_placeholder(tokens[-1]):
                tokens.pop()  # consume companion "By" / "wpn"
                log.warning("placeholder_shock", source=source_file)
                shock_dmg, shock_ac = None, None
            else:
                shock_dmg, shock_ac = _parse_shock(shock_raw)

        # TR: single token or "By wpn" placeholder
        tr_raw = tokens.pop()
        if _is_placeholder(tr_raw) and tokens and _is_placeholder(tokens[-1]):
            tokens.pop()  # consume companion
            log.warning("placeholder_tr", source=source_file)
            tr_die, tr_mult = None, None
        else:
            tr_die, tr_mult = _parse_tr(tr_raw)

        # Detect "By wpn" placeholder pattern before attempting dmg parse
        if len(tokens) >= 2 and _is_placeholder(tokens[-1]) and _is_placeholder(tokens[-2]):
            tokens.pop()  # "wpn"
            tokens.pop()  # "By"
            dmg_raw = "By wpn"
            dmg_type_token = None
            log.warning("placeholder_dmg", record=line.strip(), source=source_file)
        elif tokens and re.match(r'^[a-zA-Z][a-zA-Z/]*$', tokens[-1]) and not _is_placeholder(
            tokens[-1]
        ):
            dmg_type_token = tokens.pop()
            dmg_raw = tokens.pop()
        else:
            dmg_type_token = None
            dmg_raw = tokens.pop()

        atk_raw = tokens.pop()
        ac_raw = tokens.pop()

        # HD: "1 HP" (fixed HP) or plain integer
        if tokens and tokens[-1] == "HP":
            tokens.pop()  # remove "HP"
            tokens.pop()  # remove the preceding number (always 1 by convention)
            hd = 1
            hp = 1
        else:
            hd = int(tokens.pop())
            hp = math.floor(4.5 * hd)

        name = " ".join(tokens)
        if not name:
            raise ValueError("Empty creature name after parsing")

        atk_str, num_attacks = _parse_atk(atk_raw, name)
        dmg, dmg_type, poison = _parse_dmg(dmg_raw, dmg_type_token, name)

        creature_id = _new_id("npc")
        attack = Attack(
            id=_new_id("atk"),
            creature_id=creature_id,
            name="attack",
            atk=atk_str,
            num_attacks=num_attacks,
            dmg=dmg,
            dmg_type=dmg_type,
            poison=poison,
            tr_die=tr_die,
            tr_mult=tr_mult,
            shock_dmg=shock_dmg,
            shock_ac=shock_ac,
        )

        return Creature(
            id=creature_id,
            name=name,
            hd=hd,
            hp=hp,
            ac=int(ac_raw),
            mv=mv,
            ml=int(ml_raw),
            skill=skill,
            save=save,
            attacks=[attack],
            source_file=source_file,
        )

    except (IndexError, ValueError) as exc:
        return DeadLetter(
            id=_new_id("dl"),
            run_id=run_id,
            source_file=source_file,
            raw_content=original,
            reason=str(exc),
        )


def _join_prose_lines(lines: list[str]) -> str:
    """Join lines and repair PDF hyphenation artifacts (e.g. 'op-\\nposed')."""
    parts: list[str] = []
    for line in lines:
        if parts and parts[-1].endswith("-"):
            parts[-1] = parts[-1][:-1] + line  # stitch across hyphen break
        else:
            parts.append(line)
    return " ".join(parts)


def _extract_prose(lines: list[str], creature_names: set[str]) -> dict[str, str]:
    """Map creature name (lowercase) → joined prose block."""
    sections: dict[str, list[str]] = {}
    current: str | None = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.lower() in creature_names:
            current = stripped.lower()
            sections[current] = []
        elif current is not None:
            sections[current].append(stripped)

    return {k: _join_prose_lines(v) for k, v in sections.items() if v}


def _extract_special_abilities(prose: str) -> tuple[str, list[dict[str, str]]]:
    """Split prose into (description, special_abilities).

    Ability blocks match the pattern 'Title Case Name: description text'.
    """
    pattern = re.compile(r'([A-Z][a-zA-Z][a-zA-Z\s]*?):\s')
    parts = pattern.split(prose)

    description = parts[0].strip() if parts else ""
    abilities: list[dict[str, str]] = []

    for i in range(1, len(parts) - 1, 2):
        abilities.append({
            "name": parts[i].strip(),
            "description": parts[i + 1].strip() if i + 1 < len(parts) else "",
        })

    return description, abilities


class TextTableIngestor:
    def can_handle(self, path: Path) -> bool:
        return path.suffix == ".txt"

    def parse(self, path: Path, run_id: str) -> IngestResult:
        result = IngestResult()
        source_file = str(path)
        raw_text = path.read_text()

        # Strip comment lines and bare page numbers
        lines = [
            ln for ln in raw_text.splitlines()
            if not ln.startswith("#") and not re.match(r"^\s*\d+\s*$", ln)
        ]

        header_idx = next((i for i, ln in enumerate(lines) if _is_header_line(ln)), None)
        if header_idx is None:
            log.warning("no_table_found", source=source_file)
            result.dead_letters.append(DeadLetter(
                id=_new_id("dl"),
                run_id=run_id,
                source_file=source_file,
                raw_content=raw_text[:200],
                reason="No stat table header found in file",
            ))
            result.errors += 1
            return result

        # Collect data rows immediately after the header
        data_start = header_idx + 1
        data_end = data_start
        while data_end < len(lines) and _looks_like_data_row(lines[data_end]):
            data_end += 1

        data_lines = lines[data_start:data_end]
        result.records_read = len(data_lines)
        creatures: list[Creature] = []

        for row in data_lines:
            parsed = _parse_stat_row(row, run_id, source_file)
            if isinstance(parsed, Creature):
                creatures.append(parsed)
            else:
                result.dead_letters.append(parsed)
                result.errors += 1
                log.error(
                    "dead_letter", source=source_file, reason=parsed.reason, raw=parsed.raw_content
                )

        # Match prose sections to parsed creatures
        prose_lines = lines[:header_idx] + lines[data_end:]
        name_map = {c.name.lower(): c for c in creatures}
        prose_sections = _extract_prose(prose_lines, set(name_map))

        for name_lower, creature in name_map.items():
            if name_lower in prose_sections:
                description, abilities = _extract_special_abilities(prose_sections[name_lower])
                creature.description = description or None
                creature.special_abilities = abilities

        result.creatures = creatures
        result.records_written = len(creatures)
        return result
