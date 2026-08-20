"""
Runs multiple site orchestrators CONCURRENTLY using threads.

Why threads, not asyncio:
- Your clients/orchestrators use Playwright's SYNC api (sync_playwright,
  page.goto(), etc). Converting all of that to async_playwright would
  mean rewriting MyntraClient, MeeshoClient, and every call site --
  a large refactor for a benefit you don't need yet at 2-3 sites.
- Playwright's sync API officially supports running multiple
  independent sync_playwright() instances in SEPARATE THREADS. Each
  thread gets its own browser, own event loop internally -- they
  don't interfere with each other. That's exactly what we're doing
  here: run_myntra() and run_meesho() each open their OWN browser
  inside their own thread.
- SQLAlchemy sessions aren't shared across threads either -- each
  orchestrator already creates its own SessionLocal() session, so
  there's no extra work needed there.

Why NOT asyncio (for now):
- asyncio gives you concurrency within ONE thread/process using
  cooperative multitasking -- more efficient at scale (hundreds of
  concurrent tasks), but requires every I/O call in the chain
  (browser calls, DB calls) to be awaitable. At 2-5 sites, threads
  are simpler, require zero changes to your existing client code,
  and the overhead difference doesn't matter yet. Revisit asyncio if
  you ever need to run 20+ scrapers concurrently.

Concurrency limit:
- Each site orchestrator launches its own full Chromium instance.
  Running too many at once will eat RAM/CPU fast. max_workers below
  caps how many run AT THE SAME TIME -- extra jobs queue and start
  as earlier ones finish, rather than all launching simultaneously.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed

from orchestrators.myntra import run_myntra
from orchestrators.meesho import run_meesho


def _run_and_capture(name: str, func, kwargs: dict) -> dict:
    """
    Wraps an orchestrator call so one site's exception doesn't kill
    the whole batch -- same isolation principle as the scheduler job
    handling from earlier: one broken site should never take down
    the others.
    """
    try:
        func(**kwargs)
        return {"site": name, "status": "success", "error": None}
    except Exception as exc:
        print(f"❌ {name} orchestrator failed: {exc}")
        return {"site": name, "status": "failed", "error": str(exc)}


def run_all(query: str, pincode: str, max_workers: int = 2) -> list[dict]:
    jobs = {
        "myntra": (run_myntra, {"query": query, "pincode": pincode}),
        "meesho": (run_meesho, {"query": query}),
    }

    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_run_and_capture, name, func, kwargs): name
            for name, (func, kwargs) in jobs.items()
        }

        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(f"— {result['site']} finished with status: {result['status']}")

    print("\n" + "=" * 50)
    print("✅ All orchestrators finished")
    for r in results:
        print(f"  {r['site']:<10}: {r['status']}")
    print("=" * 50)

    return results


if __name__ == "__main__":
    run_all(
        query="korean pants",
        pincode="144002",
        max_workers=2,
    )