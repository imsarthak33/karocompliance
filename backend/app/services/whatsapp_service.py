import os
import httpx  # type: ignore

WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")

async def download_media(media_id: str) -> bytes:
    """Downloads binary media directly from Meta Graph API."""
    url = f"https://graph.facebook.com/v18.0/{media_id}"
    headers = {"Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"}
    
    async with httpx.AsyncClient() as client:
        # Step 1: Get the media URL
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        media_json = response.json()
        media_url = media_json.get("url")
        if not media_url:
            raise Exception("Meta API did not return a media URL")
            
        # Step 2: Download the actual bytes
        media_response = await client.get(media_url, headers=headers)
        media_response.raise_for_status()
        
        return media_response.content
    
    raise Exception("Failed to download media: unknown error in extraction path")
