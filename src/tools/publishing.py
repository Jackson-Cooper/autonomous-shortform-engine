import os
from src.schemas.tasks import PublishingInput, PublishingOutput
from typing import Dict, Any
from src.core.config import settings
from zernio import Zernio

async def social_publishing_tool(input_data: Dict[str, Any]) -> Dict[str, Any]:
    params = PublishingInput(**input_data)

    client = Zernio(api_key=settings.ZERNIO_API_KEY)
    
    # Note: Zernio requires a public URL for media. 
    # For MVP local files, this will likely fail unless using a tunnel.
    # We'll pass the video_url and handle TikTok specifically as requested.
    

    # Add Instagram and YouTube account IDs in the future
    tiktok_account_id = settings.ZERNIO_TIKTOK_ACCOUNT_ID
    
    try:
        result = client.posts.create(
            content=params.caption,
            # scheduled_for can be set to a future datetime string if you want to schedule instead of publish immediately
            # publishNow can be set to False if you want to save as draft instead of publishing immediately
            media_items=[
                {"type": "video", "url": params.video_url} # This should be a public URL in production
            ],
            platforms=[
                {"platform": "tiktok", "accountId": tiktok_account_id}
            ],
            tiktok_settings={
                "privacy_level": "SELF_ONLY",  # or "PUBLIC_TO_EVERYONE"
                "allow_comment": True,
                "allow_duet": False,
                "allow_stitch": False,
                "content_preview_confirmed": True,
                "express_consent_given": True,
                "draft": True,
                # video_cover_timestamp_ms is optional, if not provided TikTok will choose a default thumbnail
                # video_cover_image_url can be provided if you want to specify a custom thumbnail, but it must be a public URL as well
                # draft can be set to True if you want to save as draft instead of publishing immediately
                # video_made_with_ai can be set to True if the content is AI-generated, which may affect how TikTok handles the post
                # commercialContentType can be set to "brand_content" if the post contains branded content, which may require additional disclosures on TikTok

            },
            publish_now=True
        )
        post = result.post
        print(f"Posted to TikTok via Zernio! {post.get('_id')}")
        return {
            "platform_ids": {"tiktok": post.get("_id")},
            "status": "success"
        }
    except Exception as e:
        print(f"Zernio Error: {e}")
        return {
            "error": str(e),
            "status": "failed"
        }
