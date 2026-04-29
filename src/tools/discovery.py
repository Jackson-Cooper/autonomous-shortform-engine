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
        try:
            text = response.text.strip()
            # Clean up markdown code blocks
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            
            # Robust JSON extraction: find the first [ and last ]
            start_idx = text.find("[")
            end_idx = text.rfind("]")
            if start_idx != -1 and end_idx != -1:
                text = text[start_idx:end_idx+1]
            
            trends_data = json.loads(text)
            return {"trends": trends_data}
        except Exception as e:
            print(f"Gemini parsing error: {e}. Raw response: {response.text}")
            # Return empty trends instead of failing entire task
            return {"trends": []}
    
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
