# main.py
from fastapi import FastAPI
from backend.routes.day_plan_routes import router as day_plan_router
from backend.routes.task_routes import router as task_router
from backend.routes.notes_routes import router as notes_router
from backend.routes.page_cordination import router as page_cordination_router
from backend.routes.time_routes import router as time_router
from backend.routes.journal_routes import router as journal_router

app = FastAPI()

# Include routers with the "/api" prefix
app.include_router(day_plan_router, prefix="/api")
app.include_router(task_router, prefix="/api")
app.include_router(notes_router, prefix="/api")
app.include_router(page_cordination_router, prefix="/api")
app.include_router(time_router, prefix="/api")
app.include_router(journal_router, prefix="/api")
