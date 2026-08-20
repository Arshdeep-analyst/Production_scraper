"""
Celery tasks -- thin wrappers around your EXISTING orchestrator
functions (run_myntra, run_meesho). No changes needed to those files;
Celery just calls them.

logger.info/.exception calls here go into BOTH the console (if
running with --loglevel=info) AND logs/celery_worker.log (because of
the --logfile flag on the worker command) -- so nothing needs to be
duplicated or printed separately for logging purposes.
"""

import logging

from pipeline.scheduler import celery_app
from orchestrators.myntra import run_myntra
from orchestrators.meesho import run_meesho

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    max_retries=2,
    default_retry_delay=10 * 60,  # wait 10 min before retrying a failed run
)
def scrape_myntra(self, query: str, pincode: str):
    try:
        logger.info(f"[myntra] task started | query={query}")
        run_myntra(query=query, pincode=pincode)
        logger.info("[myntra] task finished successfully")
    except Exception as exc:
        logger.exception(f"[myntra] task FAILED on attempt {self.request.retries + 1}")
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    max_retries=2,
    default_retry_delay=10 * 60,
)
def scrape_meesho(self, query: str):
    try:
        logger.info(f"[meesho] task started | query={query}")
        run_meesho(query=query)
        logger.info("[meesho] task finished successfully")
    except Exception as exc:
        logger.exception(f"[meesho] task FAILED on attempt {self.request.retries + 1}")
        raise self.retry(exc=exc)