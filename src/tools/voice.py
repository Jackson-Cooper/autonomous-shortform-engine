import httpx
import os
from src.core.config import settings
from src.schemas.tasks import VoiceoverInput, VoiceoverOutput
from typing import Dict, Any

async def voiceover_generation_tool(input_data: Dict[str, Any]) -> Dict[str, Any]:
    params = VoiceoverInput(**input_data)
    
    if not settings.ELEVENLABS_API_KEY:
        # Mock for local testing
        return {
            "audio_url": "https://example.com/mock_audio.mp3",
            "duration": 15.0
        }
    
    voice_id = params.voice_id or "21m00Tcm4TlvDq8ikWAM"
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "xi-api-key": settings.ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "text": params.text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.5}
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            raise Exception(f"ElevenLabs error: {response.text}")
        
        filename = f"voiceover_{hash(params.text)}.mp3"
        filepath = os.path.join(settings.STORAGE_PATH, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, "wb") as f:
            f.write(response.content)
            
        return {
            "audio_url": filepath,
            "duration": 15.0 # In production, use ffprobe to get actual duration
        }
