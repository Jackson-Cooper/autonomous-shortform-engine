import os
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
from src.models.models import Video, Script, Voiceover
from src.db.session import AsyncSessionLocal
from src.core.config import settings

class VideoAgent:
    def __init__(self):
        self.output_dir = f"{settings.STORAGE_PATH}/final"
        os.makedirs(self.output_dir, exist_ok=True)

    def assemble_video(self, script: Script, voiceover: Voiceover, background_video_path: str) -> str:
        # Load audio
        audio = AudioFileClip(voiceover.audio_url)
        
        # Load background video
        bg = VideoFileClip(background_video_path)
        
        # Loop or trim background to match audio duration
        if bg.duration < audio.duration:
            bg = bg.loop(duration=audio.duration)
        else:
            bg = bg.subclip(0, audio.duration)
        
        bg = bg.set_audio(audio)
        
        # Simple text overlay for hook (Placeholder - requires ImageMagick)
        # For MVP, if TextClip fails, we just return the video with audio
        try:
            txt_clip = TextClip(script.hook, fontsize=70, color='white', font='Arial-Bold', method='caption', size=(bg.w*0.8, None))
            txt_clip = txt_clip.set_pos('center').set_duration(3) # Show hook for 3 seconds
            final_video = CompositeVideoClip([bg, txt_clip])
        except Exception as e:
            print(f"TextClip Error (likely ImageMagick missing): {e}")
            final_video = bg

        output_path = f"{self.output_dir}/video_{script.id}.mp4"
        final_video.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24)
        
        return output_path

    async def process_video_rendering(self, script_id: int, background_video_path: Optional[str] = None):
        async with AsyncSessionLocal() as session:
            script = await session.get(Script, script_id)
            if not script or not script.voiceover:
                return
            
            # If no background provided, use a placeholder or download one
            if not background_video_path:
                # Mock path for now
                background_video_path = f"{settings.STORAGE_PATH}/mock_bg.mp4"
                if not os.path.exists(background_video_path):
                    # Create a dummy video if it doesn't exist (ffmpeg command)
                    os.system(f"ffmpeg -f lavfi -i color=c=blue:s=1080x1920:d=60 -vf 'noise=alls=10:allf=t+u' {background_video_path}")

            final_path = self.assemble_video(script, script.voiceover, background_video_path)
            
            video = Video(
                script_id=script.id,
                final_video_url=final_path,
                status="completed"
            )
            session.add(video)
            await session.commit()
            return video.id
