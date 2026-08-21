"""
Small helper so orchestrators don't need to know SQLAlchemy details --
just call start_run() at the beginning and finish_run()/fail_run() at
the end.

Usage inside an orchestrator:

    session = SessionLocal()
    run = start_run(session, site="myntra", query=query)
    try:
        ... do the scrape, get saved_count ...
        finish_run(session, run, product_count=saved_count)
    except Exception as exc:
        fail_run(session, run, error=str(exc))
        raise
    finally:
        session.close()
"""

from datetime import datetime, UTC

from sqlalchemy.orm import Session

from db.models import ScrapeRun


def start_run(session: Session, site: str, query: str) -> ScrapeRun:
    run = ScrapeRun(
        site=site,
        query=query,
        status="running",
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def finish_run(session: Session, run: ScrapeRun, product_count: int) -> None:
    run.status = "success"
    run.product_count = product_count
    run.finished_at = datetime.now(UTC)
    session.commit()


def fail_run(session: Session, run: ScrapeRun, error: str) -> None:
    run.status = "failed"
    run.error_message = error[:2000]  # keep it reasonable, full tracebacks belong in your log file
    run.finished_at = datetime.now(UTC)
    session.commit()