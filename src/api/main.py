from fastapi import FastAPI, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.db.session import get_db
from src.models.models import Topic, Video, AnalyticsData
from src.core.celery_app import celery_app
from typing import List

app = FastAPI(title="Autonomous Content Engine")

# Mount storage for serving final videos (for dashboard)
app.mount("/media", StaticFiles(directory="storage/media"), name="media")

templates = Jinja2Templates(directory="src/api/templates")

@app.get("/")
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    # Fetch summary stats
    topic_count = await db.execute(select(func.count(Topic.id)))
    video_count = await db.execute(select(func.count(Video.id)))
    
    # Fetch recent videos
    stmt = select(Video).order_by(Video.created_at.desc()).limit(10)
    result = await db.execute(stmt)
    recent_videos = result.scalars().all()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "topic_count": topic_count.scalar(),
        "video_count": video_count.scalar(),
        "recent_videos": recent_videos
    })

@app.post("/trigger/discovery")
async def trigger_discovery():
    celery_app.send_task("src.tasks.discovery.run_discovery_task")
    return {"status": "Discovery task queued"}

@app.post("/trigger/pipeline")
async def trigger_pipeline():
    # Chain tasks: Discovery -> Script -> TTS -> Video -> Publish
    # For MVP, we can just send them individually or use a Celery chain
    # Here we trigger them sequentially in terms of queueing
    celery_app.send_task("src.tasks.discovery.run_discovery_task")
    celery_app.send_task("src.tasks.llm.generate_scripts_task")
    celery_app.send_task("src.tasks.tts.generate_voiceovers_task")
    celery_app.send_task("src.tasks.video.render_videos_task")
    celery_app.send_task("src.tasks.publishing.publish_videos_task")
    return {"status": "Full pipeline tasks queued"}

@app.get("/analytics")
async def get_analytics(db: AsyncSession = Depends(get_db)):
    stmt = select(AnalyticsData).order_by(AnalyticsData.fetched_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()
