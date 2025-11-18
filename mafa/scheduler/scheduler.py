"""APScheduler‑based scheduler for MAFA."""

from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.job import Job

from mafa.config.settings import Settings
from mafa.orchestrator import run as orchestrator_run


class SchedulerService:
    """Wrapper around APScheduler that runs the orchestrator on a schedule."""

    def __init__(self, settings: Settings):
        self.settings = settings
        jobstores = {"default": MemoryJobStore()}
        executors = {"default": AsyncIOExecutor()}
        job_defaults = {"coalesce": False, "max_instances": 1}
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores, executors=executors, job_defaults=job_defaults
        )

    def start(self) -> None:
        """Start the scheduler with configured jobs."""
        # Default periodic job (every 30 minutes) – configurable later.
        interval_minutes = 30
        self.scheduler.add_job(
            func=self._run_scraper_job,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id="periodic_scraper",
            replace_existing=True,
        )

        # Example of a daily job (run at 09:00) – not added by default.
        # self.scheduler.add_job(
        #     func=self._run_scraper_job,
        #     trigger=CronTrigger(hour=9, minute=0),
        #     id="daily_morning_scraper",
        #     replace_existing=True,
        # )

        self.scheduler.start()

    def stop(self) -> None:
        """Shutdown the scheduler."""
        self.scheduler.shutdown(wait=False)

    def _run_scraper_job(self) -> None:
        """Wrapper that calls the orchestrator run function."""
        try:
            orchestrator_run(config_path=self.settings.config_path)
        except Exception as e:
            print(f"Scheduled orchestrator run failed: {e}")

    def add_manual_job(self, job_id: str, run_at: str | None = None) -> Job:
        """
        Add a manual one‑off job to run the scraper immediately or at a given time.

        Parameters
        ----------
        job_id: str
            Unique identifier for the job.
        run_at: str | None
            ISO 8601 timestamp for when to run the job. If None, run immediately.

        Returns
        -------
        Job
            The APScheduler Job instance.
        """
        if run_at:
            return self.scheduler.add_job(
                func=self._run_scraper_job,
                trigger="date",
                run_date=run_at,
                id=job_id,
                replace_existing=True,
            )
        else:
            return self.scheduler.add_job(
                func=self._run_scraper_job,
                trigger="date",
                id=job_id,
                replace_existing=True,
            )