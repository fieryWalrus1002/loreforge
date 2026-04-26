from __future__ import annotations

import os
import sys
from datetime import UTC, datetime
from pathlib import Path

import structlog
from ulid import ULID

from ingest.base import Ingestor, IngestResult
from ingest.bestiary import BestiaryIngestor
from ingest.roster import RosterIngestor
from ingest.text_table import TextTableIngestor
from models.canonical import PipelineRun
from output.db_writer import DbWriter

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)

log = structlog.get_logger()

LANDING_ZONE = Path(__file__).parent.parent / "data" / "raw"
INGESTORS: list[Ingestor] = [BestiaryIngestor(), RosterIngestor(), TextTableIngestor()]


def main() -> None:
    conn_string = os.environ.get("DATABASE_URL")
    if not conn_string:
        log.error("DATABASE_URL environment variable not set")
        sys.exit(1)

    run_id = f"run_{ULID()}"
    run = PipelineRun(id=run_id, started_at=datetime.now(UTC))
    writer = DbWriter(conn_string)
    writer.start_run(run)

    log.info("pipeline_started", run_id=run_id, landing_zone=str(LANDING_ZONE))

    total = IngestResult()

    for path in sorted(LANDING_ZONE.glob("*")):
        if not path.is_file():
            continue

        ingestor: Ingestor | None = next((i for i in INGESTORS if i.can_handle(path)), None)
        if ingestor is None:
            log.warning("no_ingestor_for_file", path=str(path))
            continue

        log.info("processing_file", path=str(path), ingestor=type(ingestor).__name__)
        result = ingestor.parse(path, run_id)

        total.creatures.extend(result.creatures)
        total.characters.extend(result.characters)
        total.dead_letters.extend(result.dead_letters)
        total.warnings += result.warnings
        total.errors += result.errors
        total.records_read += result.records_read
        total.records_written += result.records_written

    writer.write_creatures(total.creatures)
    writer.write_characters(total.characters)
    writer.write_dead_letters(total.dead_letters)

    run.finished_at = datetime.now(UTC)
    run.records_read = total.records_read
    run.records_written = total.records_written
    run.warnings = total.warnings
    run.errors = total.errors
    writer.finish_run(run)

    log.info(
        "pipeline_complete",
        run_id=run_id,
        records_read=run.records_read,
        records_written=run.records_written,
        warnings=run.warnings,
        errors=run.errors,
    )


if __name__ == "__main__":
    main()
