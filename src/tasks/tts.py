import asyncio
from src.core.celery_app import celery_app
from src.agents.voice_agent import VoiceAgent
from src.db.session import AsyncSessionLocal
from src.models.models import Script
from sqlalchemy import select

@celery_app.task(name="src.tasks.tts.generate_voiceovers_task")
def generate_voiceovers_task():
    async def _run():
        agent = VoiceAgent()
        async with AsyncSessionLocal() as session:
            # Find scripts without voiceovers
            stmt = select(Script).where(Script.voiceover == None)
            result = await session.execute(stmt)
            scripts = result.scalars().all()
            
            for script in scripts:
                await agent.process_script(script.id)
            
            await session.commit()

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    loop.run_until_complete(_run())
    return "Voiceover generation completed"
