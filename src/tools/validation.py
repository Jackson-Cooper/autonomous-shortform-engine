import openai
import json
from src.core.config import settings
from typing import Dict, Any

async def hook_quality_check_tool(input_data: Dict[str, Any]) -> Dict[str, Any]:
    script = input_data.get("script")
    if not script:
        return {"score": 0, "feedback": "No script provided"}
    
    client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    prompt = f"""
    Evaluate the following script hook for virality and engagement (TikTok/Shorts).
    Hook: {script.get('hook')}
    
    Provide a score from 0-10 and brief feedback.
    Format as JSON: {{"score": float, "feedback": "string"}}
    """
    
    response = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    
    result = json.loads(response.choices[0].message.content)
    return result
