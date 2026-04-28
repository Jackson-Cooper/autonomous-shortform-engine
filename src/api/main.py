from fastapi import FastAPI, Depends, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.db.session import get_db
from src.models.models import Workflow, Task, Analytics
from src.orchestrator.planner import OrchestratorPlanner
from src.core.celery_app import celery_app
from typing import List

app = FastAPI(title="Autonomous Content Orchestrator")

# Mount storage for serving final videos
app.mount("/media", StaticFiles(directory="storage/media"), name="media")

templates = Jinja2Templates(directory="src/api/templates")

@app.get("/")
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    # Summary stats
    workflow_count = (await db.execute(select(func.count(Workflow.id)))).scalar()
    task_count = (await db.execute(select(func.count(Task.id)))).scalar()
    
    # Recent Workflows
    stmt = select(Workflow).order_by(Workflow.created_at.desc()).limit(10)
    result = await db.execute(stmt)
    recent_workflows = result.scalars().all()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "workflow_count": workflow_count,
        "task_count": task_count,
        "recent_workflows": recent_workflows
    })

@app.post("/goal")
async def create_goal(goal: str = Form(...)):
    planner = OrchestratorPlanner()
    workflow_id = await planner.create_workflow_plan(goal)
    
    # Trigger the dispatcher immediately
    celery_app.send_task("src.tasks.orchestrator.dispatch_tasks")
    
    return RedirectResponse(url="/", status_code=303)

@app.get("/workflow/{workflow_id}")
async def workflow_detail(request: Request, workflow_id: int, db: AsyncSession = Depends(get_db)):
    workflow = await db.get(Workflow, workflow_id)
    return templates.TemplateResponse("workflow_detail.html", {
        "request": request,
        "workflow": workflow
    })

@app.get("/analytics")
async def get_analytics(db: AsyncSession = Depends(get_db)):
    stmt = select(Analytics).order_by(Analytics.fetched_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()
