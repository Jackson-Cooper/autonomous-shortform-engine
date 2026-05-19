import openai
import json
from src.core.config import settings
from src.schemas.tasks import ScriptGenerationInput, ScriptGenerationOutput
from typing import Dict, Any

async def script_generation_tool(input_data: Dict[str, Any]) -> Dict[str, Any]:
    trend_item = input_data.get("trend_item")
    if isinstance(trend_item, list) and len(trend_item) > 0:
        trend_item = trend_item[0]
    
    params = ScriptGenerationInput(
        trend_item=trend_item,
        platform=input_data.get("platform", "tiktok"),
        tone=input_data.get("tone", "engaging")
    )
    
    client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    prompt = f"""
    Create a viral short-form script for {params.platform} based on this trend:
    Title: {params.trend_item.title}
    Summary: {params.trend_item.summary}
    Tone: {params.tone}
    
    Requirements:
    - Powerful HOOK (first 3 seconds)
    - High-density BODY content
    - Clear CTA
    - Visual cues for the editor
    
    Format your response as a JSON object matching the ScriptGenerationOutput schema.
    """
    
    response = await client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": "You are an elite short-form content scriptwriter."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    
    script_data = json.loads(response.choices[0].message.content)
    return script_data
