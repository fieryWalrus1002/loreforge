from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from models.canonical import Character, Creature, DeadLetter


@dataclass
class IngestResult:
    creatures: list[Creature] = field(default_factory=list)
    characters: list[Character] = field(default_factory=list)
    dead_letters: list[DeadLetter] = field(default_factory=list)
    warnings: int = 0
    errors: int = 0
    records_read: int = 0
    records_written: int = 0


class Ingestor(Protocol):
    def can_handle(self, path: Path) -> bool: ...
    def parse(self, path: Path, run_id: str) -> IngestResult: ...
