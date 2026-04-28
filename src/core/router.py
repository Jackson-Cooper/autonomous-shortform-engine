from typing import Dict, Any, Callable, Awaitable
from src.schemas.tasks import (
    TrendDiscoveryInput, ScriptGenerationInput, 
    VoiceoverInput, VideoRenderInput, PublishingInput
)

class ToolRouter:
    def __init__(self):
        self.tools: Dict[str, Callable[[Any], Awaitable[Any]]] = {}

    def register_tool(self, name: str, func: Callable[[Any], Awaitable[Any]]):
        self.tools[name] = func

    async def execute_task(self, tool_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not found in router")
        
        result = await self.tools[tool_name](input_data)
        return result

# Global router instance
router = ToolRouter()

# Register tools
from src.tools.discovery import trend_discovery_tool
from src.tools.script import script_generation_tool
from src.tools.voice import voiceover_generation_tool
from src.tools.video import video_rendering_tool
from src.tools.publishing import social_publishing_tool
from src.tools.validation import hook_quality_check_tool

router.register_tool("trend_discovery", trend_discovery_tool)
router.register_tool("script_generation", script_generation_tool)
router.register_tool("voiceover_generation", voiceover_generation_tool)
router.register_tool("video_rendering", video_rendering_tool)
router.register_tool("social_publishing", social_publishing_tool)
router.register_tool("quality_check", hook_quality_check_tool)
