from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class BaseTaskSchema(BaseModel):
    pass

# Trend Discovery
class TrendDiscoveryInput(BaseTaskSchema):
    niche: str
    sources: List[str] = ["reddit", "google_trends"]
    limit: int = 10

class TrendItem(BaseModel):
    title: str
    summary: str
    url: Optional[str] = None
    relevance_score: float

class TrendDiscoveryOutput(BaseTaskSchema):
    trends: List[TrendItem]

# Script Generation
class ScriptGenerationInput(BaseTaskSchema):
    trend_item: TrendItem
    platform: str = "tiktok"
    tone: str = "engaging"

class ScriptGenerationOutput(BaseTaskSchema):
    hook: str
    body: str
    cta: str
    visual_cues: Optional[str] = None
    suggested_music_type: Optional[str] = None

# Voiceover Generation
class VoiceoverInput(BaseTaskSchema):
    text: str
    voice_id: Optional[str] = None
    provider: str = "elevenlabs"

class VoiceoverOutput(BaseTaskSchema):
    audio_url: str
    duration: float

# Video Rendering
class VideoRenderInput(BaseTaskSchema):
    script: ScriptGenerationOutput
    voiceover_url: str
    background_video_query: Optional[str] = None
    overlay_text: bool = True

class VideoRenderOutput(BaseTaskSchema):
    video_url: str
    thumbnail_url: Optional[str] = None

# Publishing
class PublishingInput(BaseTaskSchema):
    video_url: str
    caption: str
    platforms: List[str]
    affiliate_link: Optional[str] = None

class PublishingOutput(BaseTaskSchema):
    platform_ids: Dict[str, str] # e.g. {"tiktok": "123", "youtube": "456"}
