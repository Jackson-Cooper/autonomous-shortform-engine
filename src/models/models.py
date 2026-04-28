from datetime import datetime
from enum import Enum
from typing import List, Optional
from sqlalchemy import String, Text, Float, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.session import Base

class TopicStatus(str, Enum):
    DISCOVERED = "discovered"
    SCORING = "scoring"
    QUALIFIED = "qualified"
    REJECTED = "rejected"
    PROCESSING = "processing"
    COMPLETED = "completed"

class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    source: Mapped[str] = mapped_column(String(100))  # reddit, google_trends, etc.
    original_url: Mapped[Optional[str]] = mapped_column(String(1000))
    content_summary: Mapped[str] = mapped_column(Text)
    
    virality_score: Mapped[float] = mapped_column(Float, default=0.0)
    sentiment_score: Mapped[float] = mapped_column(Float, default=0.0)
    monetization_potential: Mapped[float] = mapped_column(Float, default=0.0)
    
    status: Mapped[TopicStatus] = mapped_column(SQLEnum(TopicStatus), default=TopicStatus.DISCOVERED)
    niche: Mapped[Optional[str]] = mapped_column(String(100))
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    scripts: Mapped[List["Script"]] = relationship(back_populates="topic")

class Script(Base):
    __tablename__ = "scripts"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"))
    content: Mapped[str] = mapped_column(Text)  # JSON or structured text
    hook: Mapped[str] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text)
    cta: Mapped[str] = mapped_column(Text)
    
    voice_provider: Mapped[str] = mapped_column(String(50), default="elevenlabs")
    voice_id: Mapped[Optional[str]] = mapped_column(String(100))
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    topic: Mapped["Topic"] = relationship(back_populates="scripts")
    video: Mapped[Optional["Video"]] = relationship(back_populates="script")
    voiceover: Mapped[Optional["Voiceover"]] = relationship(back_populates="script")

class Voiceover(Base):
    __tablename__ = "voiceovers"

    id: Mapped[int] = mapped_column(primary_key=True)
    script_id: Mapped[int] = mapped_column(ForeignKey("scripts.id"))
    audio_url: Mapped[str] = mapped_column(String(1000))
    duration: Mapped[float] = mapped_column(Float)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    script: Mapped["Script"] = relationship(back_populates="voiceover")

class MediaAssetType(str, Enum):
    VIDEO = "video"
    IMAGE = "image"
    MUSIC = "music"
    OVERLAY = "overlay"

class MediaAsset(Base):
    __tablename__ = "media_assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    file_url: Mapped[str] = mapped_column(String(1000))
    asset_type: Mapped[MediaAssetType] = mapped_column(SQLEnum(MediaAssetType))
    tags: Mapped[Optional[str]] = mapped_column(String(500))  # comma separated
    source: Mapped[Optional[str]] = mapped_column(String(100)) # pexels, etc.
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Video(Base):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(primary_key=True)
    script_id: Mapped[int] = mapped_column(ForeignKey("scripts.id"))
    final_video_url: Mapped[Optional[str]] = mapped_column(String(1000))
    status: Mapped[str] = mapped_column(String(50), default="pending") # pending, rendering, completed, failed
    
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON) # transitions, music choice, etc.
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    script: Mapped["Script"] = relationship(back_populates="video")
    analytics: Mapped[List["AnalyticsData"]] = relationship(back_populates="video")

class AnalyticsData(Base):
    __tablename__ = "analytics_data"

    id: Mapped[int] = mapped_column(primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id"))
    platform: Mapped[str] = mapped_column(String(50)) # tiktok, shorts, reels
    
    views: Mapped[int] = mapped_column(default=0)
    likes: Mapped[int] = mapped_column(default=0)
    shares: Mapped[int] = mapped_column(default=0)
    comments: Mapped[int] = mapped_column(default=0)
    retention_rate: Mapped[float] = mapped_column(Float, default=0.0)
    conversion_count: Mapped[int] = mapped_column(default=0)
    
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    video: Mapped["Video"] = relationship(back_populates="analytics")
