"""
Celery application + schedule, living in pipeline/ alongside
product_pipeline.py since this IS the pipeline orchestration layer --
it decides when and how often things run.

Three moving pieces, three separate processes:
1. Redis         -- message broker. Just a mailbox, holds no logic.
2. Celery WORKER -- picks up tasks and actually runs them (opens the
                     browser, scrapes, saves to DB).
3. Celery BEAT   -- the scheduler. Drops tasks into the queue on a
                     timer. Does no scraping itself, just triggers.

Run from your project root (see commands at the bottom of this file).
"""

import os

from celery import Celery
from celery.schedules import crontab

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "scraper_project",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_track_started=True,

    # Real browser-driven scrapes can genuinely take minutes.
    # soft_time_limit raises a catchable exception first;
    # time_limit is the hard kill if that doesn't work.
    task_soft_time_limit=25 * 60,
    task_time_limit=30 * 60,

    # Don't let a worker hoard multiple heavy scraping tasks in its
    # local queue before starting the first one.
    worker_prefetch_multiplier=1,

    timezone="UTC",
    enable_utc=True,

    # ---- SCHEDULE ----
    # Both fire at the same time now -- that's fine, the worker
    # runs with --pool=threads --concurrency=2, so they execute
    # genuinely concurrently instead of queueing behind each other.
    beat_schedule={
        "scrape-myntra-every-6-hours": {
            "task": "pipeline.task.scrape_myntra",
            "schedule": crontab(minute=0, hour="*/6"),
            "kwargs": {"query": "korean pants", "pincode": "144002"},
        },
        "scrape-meesho-every-6-hours": {
            "task": "pipeline.task.scrape_meesho",
            "schedule": crontab(minute=0, hour="*/6"),
            "kwargs": {"query": "korean pants"},
        },
    },
)

celery_app.autodiscover_tasks(["pipeline"])


"""
============================================================
SETUP -- run these once
============================================================

1. Redis (doesn't run natively on Windows -- Docker is easiest):

       docker run -d --name redis -p 6379:6379 redis

2. Python packages:

       uv add celery redis

3. Make a logs folder at your project root:

       mkdir logs

============================================================
RUNNING -- two terminals, both left open, from your PROJECT ROOT
============================================================

Terminal 1 -- the worker, with real concurrency + file logging:

    celery -A pipeline.scheduler worker --pool=threads --concurrency=2 --loglevel=info --logfile=logs/celery_worker.log

  --pool=threads --concurrency=2 lets Myntra and Meesho (or more
  sites later, up to 2 at once) run genuinely at the same time,
  same idea as your run_all.py ThreadPoolExecutor version.

  --logfile writes everything (task start/finish, retries, full
  tracebacks on failure) to logs/celery_worker.log instead of only
  the terminal. That file persists after you close the terminal --
  open it anytime to see exactly when a task failed and why.

Terminal 2 -- beat, the scheduler:

    celery -A pipeline.scheduler beat --loglevel=info --logfile=logs/celery_beat.log

  beat's log is mostly just "task X sent to queue at time Y" --
  useful for confirming the schedule is actually firing on time.

============================================================
TESTING WITHOUT WAITING FOR THE SCHEDULE
============================================================
With the worker running in Terminal 1, open a THIRD terminal:

    python -c "from pipeline.task import scrape_myntra, scrape_meesho; scrape_myntra.delay(query='korean pants', pincode='144002'); scrape_meesho.delay(query='korean pants')"

That queues BOTH immediately. Watch Terminal 1 -- with
--pool=threads --concurrency=2, you should see two browser windows
open close together instead of one waiting for the other to finish.

============================================================
CHECKING LOGS LATER
============================================================
logs/celery_worker.log grows over time (nothing rotates it
automatically). To find a specific failure:

    Windows PowerShell:
        Select-String -Path logs\\celery_worker.log -Pattern "ERROR"

    Or just open the file and Ctrl+F for "Traceback" or "ERROR" --
    each entry has a timestamp so you can line it up with when you
    noticed something was wrong.

If this log file grows large enough to be annoying (weeks of daily
runs), that's the point to add log rotation -- worth asking about
when you get there rather than setting it up preemptively now.
"""