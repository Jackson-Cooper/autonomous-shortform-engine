import asyncio
from datetime import datetime
from src.core.celery_app import celery_app
from src.core.router import router
from src.models.models import Task, TaskStatus, Workflow, WorkflowStatus
from src.db.session import AsyncSessionLocal
from sqlalchemy import select, and_

@celery_app.task(name="src.tasks.orchestrator.dispatch_tasks")
def dispatch_tasks():
    """
    Main background loop to find and execute tasks.
    """
    async def _run():
        async with AsyncSessionLocal() as session:
            # Find pending tasks whose dependencies are completed
            stmt = select(Task).where(Task.status == TaskStatus.PENDING)
            result = await session.execute(stmt)
            pending_tasks = result.scalars().all()
            
            for task in pending_tasks:
                # Check dependencies
                can_run = True
                if task.depends_on:
                    for dep_id in task.depends_on:
                        dep_task = await session.get(Task, dep_id)
                        if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                            can_run = False
                            break
                
                if can_run:
                    # Update status to running
                    task.status = TaskStatus.RUNNING
                    task.started_at = datetime.utcnow()
                    await session.commit()
                    
                    # Execute the task
                    try:
                        print(f"Executing task {task.id} (tool: {task.tool_name})")
                        # We merge previous outputs into inputs if needed, or the planner handles it
                        # For now, let's assume inputs are complete or the tool knows where to look.
                        output = await router.execute_task(task.tool_name, task.input_data)
                        
                        task.output_data = output
                        task.status = TaskStatus.COMPLETED
                        task.completed_at = datetime.utcnow()
                    except Exception as e:
                        print(f"Task {task.id} failed: {e}")
                        task.status = TaskStatus.FAILED
                        task.error_message = str(e)
                    
                    await session.commit()

            # Check if workflows are completed
            w_stmt = select(Workflow).where(Workflow.status == WorkflowStatus.RUNNING)
            w_res = await session.execute(w_stmt)
            running_workflows = w_res.scalars().all()
            for w in running_workflows:
                # If all tasks are completed/failed, mark workflow complete
                all_done = all(t.status in [TaskStatus.COMPLETED, TaskStatus.FAILED] for t in w.tasks)
                if all_done:
                    w.status = WorkflowStatus.COMPLETED
                    await session.commit()

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    loop.run_until_complete(_run())
    return "Dispatch cycle completed"
