import httpx
from typing import List, Optional
from src.core.config import settings
import os

class MediaSourcingAgent:
    def __init__(self):
        self.api_key = settings.PEXELS_API_KEY
        self.base_url = "https://api.pexels.com/videos/search"

    async def get_stock_videos(self, query: str, limit: int = 3) -> List[str]:
        if not self.api_key:
            return []
        
        headers = {"Authorization": self.api_key}
        params = {
            "query": query,
            "per_page": limit,
            "orientation": "portrait"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url, headers=headers, params=params)
            if response.status_code != 200:
                return []
            
            data = response.json()
            video_urls = []
            for v in data.get("videos", []):
                # Get the best vertical file
                files = v.get("video_files", [])
                best_file = next((f["link"] for f in files if f.get("width", 0) < f.get("height", 0)), files[0]["link"])
                video_urls.append(best_file)
            return video_urls

    async def download_asset(self, url: str, filename: str) -> str:
        path = f"{settings.STORAGE_PATH}/{filename}"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            with open(path, "wb") as f:
                f.write(response.content)
        return path
