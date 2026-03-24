import tempfile
import whisper  # type: ignore
import os
from pydantic import BaseModel  # type: ignore

# Note: Whisper large-v3 requires significant RAM/GPU
model = whisper.load_model("large-v3")

class TranscriptionResult(BaseModel):
    transcript: str
    language_detected: str
    confidence: float

class VoiceAgent:
    @staticmethod
    async def transcribe(audio_bytes: bytes, file_format: str = 'ogg') -> TranscriptionResult:
        with tempfile.NamedTemporaryFile(suffix=f'.{file_format}', delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            # Task: transcribe with Hindi as default for Indian context
            result = model.transcribe(tmp_path, language="hi", task="transcribe")
            
            return TranscriptionResult(**{
                "transcript": result["text"],
                "language_detected": result.get("language", "hi"),
                "confidence": 1.0 
            })
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
