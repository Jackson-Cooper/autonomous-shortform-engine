import json
from typing import Dict, Optional
import openai
from src.core.config import settings
from src.models.models import Topic, Script
from src.db.session import AsyncSessionLocal

class ScriptAgent:
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def generate_script(self, topic: Topic) -> Optional[Script]:
        prompt = f"""
        Generate a highly engaging viral short-form video script for TikTok/Shorts based on the following topic:
        Title: {topic.title}
        Content: {topic.content_summary}
        
        The script must have:
        1. A powerful HOOK (first 3 seconds) to stop the scroll.
        2. A concise BODY with high information density.
        3. A clear CTA (Call to Action) for monetization/engagement.
        
        Format the output as JSON:
        {{
            "hook": "string",
            "body": "string",
            "cta": "string",
            "visual_cues": "string describing what to show"
        }}
        """
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a world-class viral content creator and scriptwriter."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            script_data = json.loads(response.choices[0].message.content)
            
            script = Script(
                topic_id=topic.id,
                content=json.dumps(script_data),
                hook=script_data["hook"],
                body=script_data["body"],
                cta=script_data["cta"]
            )
            
            return script
        except Exception as e:
            print(f"Error generating script: {e}")
            return None

    async def process_topic(self, topic_id: int):
        async with AsyncSessionLocal() as session:
            topic = await session.get(Topic, topic_id)
            if not topic:
                return
            
            script = await self.generate_script(topic)
            if script:
                session.add(script)
                await session.commit()
                return script.id
        return None
