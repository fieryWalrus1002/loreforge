from __future__ import annotations

import json

import psycopg
import structlog

from models.canonical import Character, Creature, DeadLetter, PipelineRun

log = structlog.get_logger()


class DbWriter:
    def __init__(self, conn_string: str) -> None:
        self.conn_string = conn_string

    def _connect(self) -> psycopg.Connection:
        return psycopg.connect(self.conn_string)

    def start_run(self, run: PipelineRun) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO pipeline_runs (id, started_at) VALUES (%s, %s)",
                (run.id, run.started_at),
            )

    def finish_run(self, run: PipelineRun) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE pipeline_runs
                SET finished_at=%s, records_read=%s, records_written=%s, warnings=%s, errors=%s
                WHERE id=%s
                """,
                (run.finished_at, run.records_read, run.records_written,
                 run.warnings, run.errors, run.id),
            )

    def write_creatures(self, creatures: list[Creature]) -> None:
        if not creatures:
            return
        with self._connect() as conn:
            for c in creatures:
                conn.execute(
                    """
                    INSERT INTO creatures
                        (id, source_id, name, hd, hp, ac, mv, ml, skill, save,
                         description, special_abilities, source_file)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (c.id, c.source_id, c.name, c.hd, c.hp, c.ac,
                     c.mv, c.ml, c.skill, c.save,
                     c.description, json.dumps(c.special_abilities), c.source_file),
                )
                for atk in c.attacks:
                    conn.execute(
                        """
                        INSERT INTO attacks
                            (id, creature_id, name, atk, num_attacks, dmg, dmg_type,
                             poison, tr_die, tr_mult, shock_dmg, shock_ac,
                             range_str, mag, attr, tl, enc)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (id) DO NOTHING
                        """,
                        (atk.id, atk.creature_id, atk.name, atk.atk, atk.num_attacks,
                         atk.dmg, atk.dmg_type, atk.poison, atk.tr_die, atk.tr_mult,
                         atk.shock_dmg, atk.shock_ac,
                         atk.range_str, atk.mag, atk.attr, atk.tl, atk.enc),
                    )
            log.info("creatures_written", count=len(creatures))

    def write_characters(self, characters: list[Character]) -> None:
        if not characters:
            return
        with self._connect() as conn:
            for c in characters:
                conn.execute(
                    """
                    INSERT INTO characters
                        (id, source_id, name, is_pc, hp, max_hp, system_strain,
                         ac, attributes, skill, initiative_mod, source_file)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (c.id, c.source_id, c.name, c.is_pc, c.hp, c.max_hp,
                     c.system_strain, c.ac, json.dumps(c.attributes),
                     c.skill, c.initiative_mod, c.source_file),
                )
                for atk in c.attacks:
                    conn.execute(
                        """
                        INSERT INTO attacks
                            (id, character_id, name, atk, num_attacks, dmg, dmg_type,
                             poison, tr_die, tr_mult, shock_dmg, shock_ac, range_str)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (id) DO NOTHING
                        """,
                        (atk.id, atk.character_id, atk.name, atk.atk, atk.num_attacks,
                         atk.dmg, atk.dmg_type, atk.poison, atk.tr_die, atk.tr_mult,
                         atk.shock_dmg, atk.shock_ac, atk.range_str),
                    )
            log.info("characters_written", count=len(characters))

    def write_dead_letters(self, dead_letters: list[DeadLetter]) -> None:
        if not dead_letters:
            return
        with self._connect() as conn:
            for dl in dead_letters:
                conn.execute(
                    """
                    INSERT INTO dead_letters (id, run_id, source_file, raw_content, reason)
                    VALUES (%s,%s,%s,%s,%s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (dl.id, dl.run_id, dl.source_file, dl.raw_content, dl.reason),
                )
        log.info("dead_letters_written", count=len(dead_letters))
