import asyncio
from src.core.celery_app import celery_app
from src.agents.script_agent import ScriptAgent
from src.db.session import AsyncSessionLocal
from src.models.models import Topic, TopicStatus
from sqlalchemy import select

@celery_app.task(name="src.tasks.llm.generate_scripts_task")
def generate_scripts_task():
    async def _run():
        agent = ScriptAgent()
        async with AsyncSessionLocal() as session:
            # Find qualified topics without scripts
            stmt = select(Topic).where(
                Topic.status == TopicStatus.QUALIFIED
            )
            result = await session.execute(stmt)
            topics = result.scalars().all()
            
            for topic in topics:
                # Need to refresh or check scripts explicitly because of async session
                # For MVP, just try processing
                await agent.process_topic(topic.id)
                topic.status = TopicStatus.PROCESSING
            
            await session.commit()
            
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    loop.run_until_complete(_run())
    return "Script generation completed"
