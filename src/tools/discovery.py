import httpx
from src.schemas.tasks import TrendDiscoveryInput, TrendDiscoveryOutput, TrendItem
from src.core.config import settings
import google.generativeai as genai

async def trend_discovery_tool(input_data: Dict[str, Any]) -> Dict[str, Any]:
    # Parse input
    params = TrendDiscoveryInput(**input_data)
    
    # Priority: Gemini for deep trend research
    if settings.GEMINI_API_KEY:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""
        Research and identify the top {params.limit} trending topics for short-form content in the niche of {params.niche}.
        Focus on high engagement, buyer intent, and affiliate potential.
        Sources: {', '.join(params.sources)}
        
        Return the results as a list of JSON objects with keys: title, summary, url, relevance_score (0-1).
        """
        
        response = model.generate_content(prompt)
        # Note: In production, we'd use structured output features or more robust parsing
        try:
            # Basic cleanup if Gemini wraps in code blocks
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:-3].strip()
            elif text.startswith("```"):
                text = text[3:-3].strip()
            
            trends_data = json.loads(text)
            return {"trends": trends_data}
        except Exception as e:
            print(f"Gemini parsing error: {e}")
    
    # Fallback to a simple mock/scraper if Gemini fails or is missing
    return {
        "trends": [
            {
                "title": f"The future of {params.niche} in 2026",
                "summary": "Why AI agents are changing everything.",
                "url": "https://example.com/trend1",
                "relevance_score": 0.95
            }
        ]
    }

from typing import Dict, Any
import json
