import httpx
from typing import List, Dict
from src.models.models import Topic, TopicStatus
from src.db.session import AsyncSessionLocal
from sqlalchemy import select

class DiscoveryAgent:
    def __init__(self):
        self.headers = {"User-Agent": "ContentEngine/0.1"}

    async def scrape_reddit(self, subreddit: str, limit: int = 10) -> List[Dict]:
        url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            if response.status_code != 200:
                return []
            
            data = response.json()
            topics = []
            for post in data.get("data", {}).get("children", []):
                post_data = post.get("data", {})
                topics.append({
                    "title": post_data.get("title"),
                    "content_summary": post_data.get("selftext") or post_data.get("title"),
                    "source": f"reddit/r/{subreddit}",
                    "original_url": f"https://reddit.com{post_data.get('permalink')}",
                    "niche": subreddit
                })
            return topics

    def score_topic(self, topic_data: Dict) -> Dict:
        # Simple scoring logic for now
        # In a real scenario, this would use LLM or more complex metrics
        virality_score = 0.5 # Placeholder
        monetization_potential = 0.5 # Placeholder
        
        # Heuristic: titles with "how to", "best", "AI", "money" get higher scores
        keywords = ["how to", "best", "ai", "money", "tool", "productivity", "career"]
        title_lower = topic_data["title"].lower()
        
        score_boost = sum(0.1 for word in keywords if word in title_lower)
        virality_score = min(1.0, virality_score + score_boost)
        
        topic_data["virality_score"] = virality_score
        topic_data["monetization_potential"] = monetization_potential
        topic_data["status"] = TopicStatus.QUALIFIED if virality_score > 0.6 else TopicStatus.DISCOVERED
        
        return topic_data

    async def run_discovery(self, subreddits: List[str]):
        all_topics = []
        for sub in subreddits:
            raw_topics = await self.scrape_reddit(sub)
            for raw in raw_topics:
                scored = self.score_topic(raw)
                all_topics.append(scored)
        
        async with AsyncSessionLocal() as session:
            for t_data in all_topics:
                # Check if exists
                stmt = select(Topic).where(Topic.original_url == t_data["original_url"])
                result = await session.execute(stmt)
                if result.scalar_one_or_none():
                    continue
                
                topic = Topic(**t_data)
                session.add(topic)
            await session.commit()
        
        return all_topics
