import asyncio
from src.core.celery_app import celery_app
from src.agents.publishing_agent import PublishingAgent
from src.db.session import AsyncSessionLocal
from src.models.models import Video
from sqlalchemy import select

@celery_app.task(name="src.tasks.publishing.publish_videos_task")
def publish_videos_task():
    async def _run():
        agent = PublishingAgent()
        async with AsyncSessionLocal() as session:
            # Find videos that are completed but not published
            stmt = select(Video).where(Video.status == "completed")
            result = await session.execute(stmt)
            videos = result.scalars().all()
            
            for video in videos:
                await agent.process_publishing(video.id)
            
            await session.commit()

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    loop.run_until_complete(_run())
    return "Publishing completed"
