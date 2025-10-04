from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from collectors.collect_configmaps import collect_configmaps
from collectors.metadata import metadata
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

def register_events(app):
    @app.on_event("startup")
    async def startup_event():
        logger.info("Starting scheduler...")

        collect_configmaps()
        metadata()

        scheduler.add_job(
            collect_configmaps,
            trigger=IntervalTrigger(hours=12),
            id="odin_collect_configmaps",
            replace_existing=True
        )

        scheduler.add_job(
            metadata,
            trigger=IntervalTrigger(hours=120),
            id="odin_metadata",
            replace_existing=True
        )

        scheduler.start()

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Shutting down scheduler...")
        scheduler.shutdown()
