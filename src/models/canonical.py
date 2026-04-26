from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class Attack(BaseModel):
    id: str
    creature_id: str | None = None
    character_id: str | None = None
    name: str
    atk: str
    num_attacks: int = 1
    dmg: str
    dmg_type: str | None = None
    poison: bool = False
    tr_die: str | None = None
    tr_mult: str | None = None
    shock_dmg: int | None = None
    shock_ac: int | None = None
    range_str: str | None = None
    mag: int | None = None
    attr: str | None = None
    tl: int | None = None
    enc: int | None = None


class Creature(BaseModel):
    id: str
    source_id: str | None = None
    name: str
    hd: int
    hp: int
    ac: int
    mv: str | None = None
    ml: int | None = None
    skill: str | None = None
    save: str | None = None
    description: str | None = None
    special_abilities: list[dict[str, Any]] = []
    attacks: list[Attack] = []
    source_file: str


class Character(BaseModel):
    id: str
    source_id: str | None = None
    name: str
    is_pc: bool
    hp: int
    max_hp: int
    system_strain: int = 0
    ac: int
    attributes: dict[str, int]
    skill: str | None = None
    initiative_mod: int = 0
    attacks: list[Attack] = []
    source_file: str


class DeadLetter(BaseModel):
    id: str
    run_id: str
    source_file: str
    raw_content: str
    reason: str


class PipelineRun(BaseModel):
    id: str
    started_at: datetime
    finished_at: datetime | None = None
    records_read: int = 0
    records_written: int = 0
    warnings: int = 0
    errors: int = 0
