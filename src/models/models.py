from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from sqlalchemy import String, Text, Float, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.session import Base

class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class Workflow(Base):
    __tablename__ = "workflows"

    id: Mapped[int] = mapped_column(primary_key=True)
    goal: Mapped[str] = mapped_column(Text)  # High-level user goal
    status: Mapped[WorkflowStatus] = mapped_column(SQLEnum(WorkflowStatus), default=WorkflowStatus.PENDING)
    
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tasks: Mapped[List["Task"]] = relationship(back_populates="workflow", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    workflow_id: Mapped[int] = mapped_column(ForeignKey("workflows.id"))
    
    task_type: Mapped[str] = mapped_column(String(100))  # e.g., "trend_discovery", "script_generation"
    tool_name: Mapped[str] = mapped_column(String(100))  # e.g., "gemini_research", "openai_gpt4"
    
    status: Mapped[TaskStatus] = mapped_column(SQLEnum(TaskStatus), default=TaskStatus.PENDING)
    
    input_data: Mapped[Dict[str, Any]] = mapped_column(JSON)  # Arguments for the tool
    output_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # Result from the tool
    
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Dependencies (simple sequential or DAG)
    depends_on: Mapped[Optional[List[int]]] = mapped_column(JSON) # List of Task IDs
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    workflow: Mapped["Workflow"] = relationship(back_populates="tasks")

class Analytics(Base):
    __tablename__ = "analytics"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tasks.id"))
    
    platform: Mapped[str] = mapped_column(String(50))
    external_id: Mapped[str] = mapped_column(String(255)) # ID on TikTok/YT/IG
    
    views: Mapped[int] = mapped_column(default=0)
    likes: Mapped[int] = mapped_column(default=0)
    shares: Mapped[int] = mapped_column(default=0)
    comments: Mapped[int] = mapped_column(default=0)
    retention_rate: Mapped[Optional[float]] = mapped_column(Float)
    conversion_rate: Mapped[Optional[float]] = mapped_column(Float)
    
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
