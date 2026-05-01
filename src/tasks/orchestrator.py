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
            while True:
                # Find pending tasks whose dependencies are completed
                stmt = select(Task).where(Task.status == TaskStatus.PENDING)
                result = await session.execute(stmt)
                pending_tasks = result.scalars().all()
                
                tasks_started = 0
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
                        tasks_started += 1

                        # Update Workflow status to RUNNING if it's currently PENDING
                        workflow = await session.get(Workflow, task.workflow_id)
                        if workflow and workflow.status == WorkflowStatus.PENDING:
                            workflow.status = WorkflowStatus.RUNNING

                        # Update status to running
                        task.status = TaskStatus.RUNNING
                        task.started_at = datetime.utcnow()
                        await session.commit()
                        # Execute the task
                        try:
                            print(f"Executing task {task.id} (tool: {task.tool_name})")
                            
                            # Dynamic data injection: resolve {{index.field}} from dependencies
                            resolved_input = task.input_data.copy()
                            
                            async def resolve_placeholders(data):
                                if isinstance(data, str) and data.startswith("{{") and data.endswith("}}"):
                                    parts = data[2:-2].split(".")
                                    if len(parts) == 2:
                                        try:
                                            dep_idx = int(parts[0])
                                            field = parts[1]
                                            # Find the task at that index in the workflow
                                            stmt = select(Task).where(Task.workflow_id == task.workflow_id).order_by(Task.id)
                                            res = await session.execute(stmt)
                                            all_workflow_tasks = res.scalars().all()
                                            if dep_idx < len(all_workflow_tasks):
                                                dep_task = all_workflow_tasks[dep_idx]
                                                if dep_task.output_data:
                                                    # If the field is 'object', return the whole dict
                                                    if field == "object":
                                                        return dep_task.output_data
                                                    return dep_task.output_data.get(field, data)
                                        except:
                                            return data
                                elif isinstance(data, dict):
                                    return {k: await resolve_placeholders(v) for k, v in data.items()}
                                elif isinstance(data, list):
                                    return [await resolve_placeholders(i) for i in data]
                                return data

                            resolved_input = await resolve_placeholders(resolved_input)
                            
                            output = await router.execute_task(task.tool_name, resolved_input)
                            
                            task.output_data = output
                            task.status = TaskStatus.COMPLETED
                            task.completed_at = datetime.utcnow()
                        except Exception as e:
                            print(f"Task {task.id} failed: {e}")
                            task.status = TaskStatus.FAILED
                            task.error_message = str(e)
                        
                        await session.commit()
                
                # If no tasks could be started in this loop, we might be blocked or done
                if tasks_started == 0:
                    break

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
