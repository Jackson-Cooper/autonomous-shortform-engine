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
        Available tools: {', '.join(self.available_tools)}
        
        For each task, specify:
        1. tool_name: One of the available tools.
        2. task_type: A descriptive string.
        3. input_data: A JSON object matching the expected schema for that tool.
        4. depends_on_index: (Optional) The index of the task this task depends on (0-based).
        
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
