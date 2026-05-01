import os
import logging
from src.core.config import settings
from src.schemas.tasks import VoiceoverInput
from typing import Dict, Any
from elevenlabs.client import ElevenLabs
from moviepy.editor import AudioFileClip

logger = logging.getLogger(__name__)

async def voiceover_generation_tool(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converts text to speech using ElevenLabs and returns the local path and duration.
    """
    try:
        params = VoiceoverInput(**input_data)

        client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)

        # Ensure the storage directory exists
        output_dir = os.path.join(settings.STORAGE_PATH, "voiceovers")
        os.makedirs(output_dir, exist_ok=True)
        
        # Create a unique filename based on the hash of the text
        filename = f"voiceover_{hash(params.text)}.mp3"
        output_path = os.path.join(output_dir, filename)

        # Call ElevenLabs API
        audio_generator = client.text_to_speech.convert(
            text=params.text,
            voice_id=params.voice_id or "HNLnm2dLXPBSK0FmAPS0", # Default voice
            model_id="eleven_v3",
            output_format="mp3_44100_128",
        )

        # ElevenLabs SDK returns an iterator of bytes
        with open(output_path, "wb") as f:
            for chunk in audio_generator:
                if chunk:
                    f.write(chunk)

        # Get audio duration using MoviePy
        duration = 0.0
        try:
            audio_clip = AudioFileClip(output_path)
            duration = audio_clip.duration
            audio_clip.close()
        except Exception as e:
            logger.error(f"Failed to get audio duration for {output_path}: {e}")
            duration = 15.0 # Fallback placeholder

        return {
            "audio_url": output_path,
            "duration": duration
        }

    except Exception as e:
        logger.error(f"Voiceover generation failed: {str(e)}")
        raise Exception(f"Voiceover generation failed: {str(e)}")
