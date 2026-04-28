import asyncio
from src.core.celery_app import celery_app
from src.agents.video_agent import VideoAgent
from src.db.session import AsyncSessionLocal
from src.models.models import Script, Video
from sqlalchemy import select

@celery_app.task(name="src.tasks.video.render_videos_task")
def render_videos_task():
    async def _run():
        agent = VideoAgent()
        async with AsyncSessionLocal() as session:
            # Find scripts with voiceovers but no videos
            stmt = select(Script).where(Script.voiceover != None)
            result = await session.execute(stmt)
            scripts = result.scalars().all()
            
            for script in scripts:
                # Check if video already exists
                v_stmt = select(Video).where(Video.script_id == script.id)
                v_res = await session.execute(v_stmt)
                if not v_res.scalar_one_or_none():
                    await agent.process_video_rendering(script.id)
            
            await session.commit()

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    loop.run_until_complete(_run())
    return "Video rendering completed"
