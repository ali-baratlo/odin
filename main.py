from fastapi import FastAPI
from api import endpoints , ui_routes
from api.events import register_events
import uvicorn


app = FastAPI(
    title="OKD Resource Search",
    description="Let's dive into resources on any clusters",
    version="pre-alpha-0.0.1"
)


app.include_router(endpoints.router)
app.include_router(ui_routes.router)


register_events(app)
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

