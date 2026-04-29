import json
from typing import List, Dict, Any
import openai
from src.core.config import settings
from src.models.models import Workflow, Task, TaskStatus
from src.db.session import AsyncSessionLocal
from src.schemas.tasks import (
    TrendDiscoveryInput, ScriptGenerationInput, 
    VoiceoverInput, VideoRenderInput, PublishingInput
)

class OrchestratorPlanner:
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.available_tools = [
            "trend_discovery",
            "script_generation",
            "voiceover_generation",
            "video_rendering",
            "social_publishing"
        ]

    async def create_workflow_plan(self, goal: str) -> int:
        """
        Takes a high-level goal and creates a Workflow and sequence of Tasks in the DB.
        """
        prompt = f"""
        You are an AI Content Business Orchestrator. 
        High-level Goal: {goal}
        
        Decompose this goal into a sequence of structured tasks.
        Available tools and their expected input keys:
        1. trend_discovery: {{ "niche": str, "limit": int }} -> returns {{ "trends": [{{ "title": str, "summary": str, "relevance_score": float }}] }}
        2. script_generation: {{ "trend_item": object, "platform": str }} -> returns {{ "hook": str, "body": str, "cta": str }}
        3. voiceover_generation: {{ "text": str }} -> returns {{ "audio_url": str, "duration": float }}
        4. video_rendering: {{ "script": object, "voiceover_url": str }} -> returns {{ "video_url": str }}
        5. social_publishing: {{ "video_url": str, "caption": str, "platforms": ["tiktok"] }} -> returns {{ "platform_ids": dict }}
        6. quality_check: {{ "script": object }} -> returns {{ "score": float, "feedback": str }}

        DYNAMIC DATA INJECTION:
        You MUST link tasks by using the placeholder syntax "{{{{index.field}}}}" to reference the output of a previous task (0-indexed).
        Example: If task 0 is trend_discovery, task 1 (script_generation) should use "{{{{0.trends}}}}" for its input.
        
        Return the plan as a JSON object:
        {{
            "tasks": [
                {{
                    "tool_name": "string",
                    "task_type": "string",
                    "input_data": {{}},
                    "depends_on_index": int or null
                }}
            ]
        }}
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are an expert at breaking down business goals into automated technical workflows."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        plan_data = json.loads(response.choices[0].message.content)
        
        async with AsyncSessionLocal() as session:
            workflow = Workflow(goal=goal)
            session.add(workflow)
            await session.flush() # Get workflow ID
            
            created_tasks = []
            for i, task_spec in enumerate(plan_data["tasks"]):
                depends_on = []
                if task_spec.get("depends_on_index") is not None:
                    # Map index to actual task ID later or use sequential if simple
                    # For now, let's store indices and resolve them in a second pass if needed, 
                    # or just assume they depend on previously created IDs.
                    idx = task_spec["depends_on_index"]
                    if idx < len(created_tasks):
                        depends_on = [created_tasks[idx].id]
                
                task = Task(
                    workflow_id=workflow.id,
                    task_type=task_spec["task_type"],
                    tool_name=task_spec["tool_name"],
                    input_data=task_spec["input_data"],
                    status=TaskStatus.PENDING,
                    depends_on=depends_on
                )
                session.add(task)
                await session.flush()
                created_tasks.append(task)
                
            await session.commit()
            return workflow.id
