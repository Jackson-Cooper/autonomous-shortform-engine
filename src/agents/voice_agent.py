 import httpx
import os
from typing import Optional
from src.core.config import settings
from src.models.models import Script, Voiceover
from src.db.session import AsyncSessionLocal

class VoiceAgent:
    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY
        self.url = "https://api.elevenlabs.io/v1/text-to-speech"

    async def generate_voiceover(self, script: Script) -> Optional[Voiceover]:
        if not self.api_key:
            # Mock for local testing if no API key
            audio_path = f"{settings.STORAGE_PATH}/mock_audio_{script.id}.mp3"
            os.makedirs(os.path.dirname(audio_path), exist_ok=True)
            with open(audio_path, "wb") as f:
                f.write(b"mock audio content")
            
            return Voiceover(
                script_id=script.id,
                audio_url=audio_path,
                duration=10.0 # Placeholder
            )

        voice_id = script.voice_id or "21m00Tcm4TlvDq8ikWAM" # Default voice
        endpoint = f"{self.url}/{voice_id}"
        
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "text": f"{script.hook}. {script.body}. {script.cta}",
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(endpoint, json=payload, headers=headers)
            if response.status_code != 200:
                print(f"ElevenLabs Error: {response.text}")
                return None
            
            audio_path = f"{settings.STORAGE_PATH}/voice_{script.id}.mp3"
            os.makedirs(os.path.dirname(audio_path), exist_ok=True)
            with open(audio_path, "wb") as f:
                f.write(response.content)
            
            # In a real scenario, we'd use ffprobe to get duration
            return Voiceover(
                script_id=script.id,
                audio_url=audio_path,
                duration=15.0 # Placeholder
            )

    async def process_script(self, script_id: int):
        async with AsyncSessionLocal() as session:
            script = await session.get(Script, script_id)
            if not script:
                return
            
            voiceover = await self.generate_voiceover(script)
            if voiceover:
                session.add(voiceover)
                await session.commit()
                return voiceover.id
        return None
