from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from api import endpoints
from scheduler.scheduler import start_scheduler
from collectors.resource_collector import collect_resources
from utils.logger import logger
from utils.db import client as db_client # Import client to trigger connection check
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan manager for the FastAPI application.
    This handles startup and shutdown events.
    """
    logger.info("Application starting up...")

    # The database connection is implicitly checked by the import above.
    # If the connection fails, the app will not start.

    # Perform an initial collection on startup
    logger.info("Performing initial resource collection...")
    try:
        collect_resources()
        logger.info("Initial resource collection complete.")
    except Exception as e:
        logger.critical(f"Error during initial resource collection: {e}", exc_info=True)

    # Start the background scheduler for periodic collection
    start_scheduler()

    yield

    logger.info("Application shutting down...")

app = FastAPI(
    title="Odin - OKD Resource Collector and Inspector",
    description="A tool to collect, inspect, and compare Kubernetes resources from multiple clusters.",
    version="2.0.0",
    lifespan=lifespan
)

# API routes
app.include_router(endpoints.router)

# Serve the React frontend
app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)