import base64
import anthropic  # type: ignore
from anthropic import AsyncAnthropic  # type: ignore
from openai import AsyncOpenAI  # type: ignore
from app.config import settings  # type: ignore

anthropic_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

class OCRService:
    @staticmethod
    async def extract_pdf_text(file_bytes: bytes) -> str:
        # Note: In a production environment, you would use a library like PyMuPDF 
        # to extract text directly from the PDF stream first.
        # For this orchestration, we provide a placeholder that triggers the classifier.
        return "Extracted PDF Text Placeholder - Replace with PyMuPDF output in production"

    @staticmethod
    async def extract_image_text(file_bytes: bytes) -> str:
        """Extracts text from images using GPT-4o Vision."""
        base64_image = base64.b64encode(file_bytes).decode('utf-8')
        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract all text from this image exactly as written. Preserve the layout if possible."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ],
                }
            ],
            max_tokens=2000,
            temperature=0
        )
        return response.choices[0].message.content

ocr_service = OCRService()
