import asyncio
from src.core.celery_app import celery_app
from src.agents.discovery_agent import DiscoveryAgent

@celery_app.task(name="src.tasks.discovery.run_discovery_task")
def run_discovery_task(subreddits=None):
    if subreddits is None:
        subreddits = ["programming", "artificial", "careerguidance"]
    
    async def _run():
        agent = DiscoveryAgent()
        await agent.run_discovery(subreddits)
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    loop.run_until_complete(_run())
    return f"Discovery completed for {subreddits}"
