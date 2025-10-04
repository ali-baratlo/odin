from contextlib import asynccontextmanager
from fastapi import FastAPI
from api import endpoints, ui_routes
from scheduler.scheduler import start_scheduler
from collectors.resource_collector import collect_resources
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan manager for the FastAPI application.
    This handles startup and shutdown events.
    """
    print("Starting up...")

    # Perform an initial collection on startup
    print("Performing initial resource collection...")
    try:
        collect_resources()
        print("Initial resource collection complete.")
    except Exception as e:
        print(f"Error during initial resource collection: {e}")

    # Start the background scheduler for periodic collection
    start_scheduler()

    yield

    print("Shutting down...")

app = FastAPI(
    title="Odin - OKD Resource Collector and Inspector",
    description="A tool to collect, inspect, and compare Kubernetes resources from multiple clusters.",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(endpoints.router)
app.include_router(ui_routes.router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)