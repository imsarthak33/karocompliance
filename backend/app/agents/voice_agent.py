"""
Voice Agent — Audio transcription via Google Cloud Speech-to-Text.
"""
import logging
from decimal import Decimal
import sentry_sdk # type: ignore
from google.cloud import speech # type: ignore
from pydantic import BaseModel, field_validator, ConfigDict # type: ignore

logger = logging.getLogger(__name__)

# Initializes using the same GOOGLE_APPLICATION_CREDENTIALS your Storage uses
speech_client = speech.SpeechAsyncClient()

class TranscriptionResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    transcript: str
    language_detected: str
    confidence: Decimal

    @field_validator("confidence", mode="before")
    @classmethod
    def coerce_confidence(cls, v: object) -> Decimal:
        try:
            return Decimal(str(v)) if v is not None else Decimal("0")
        except Exception:
            return Decimal("0")

class VoiceAgent:
    @staticmethod
    async def transcribe(audio_bytes: bytes, file_format: str = "ogg") -> TranscriptionResult:
        with sentry_sdk.start_span(op="agent.voice", description="transcribe") as span:
            span.set_data("audio_size_bytes", len(audio_bytes))

            try:
                audio = speech.RecognitionAudio(content=audio_bytes)
                
                # WhatsApp audio notes are typically OGG_OPUS
                config = speech.RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
                    sample_rate_hertz=16000,
                    language_code="hi-IN", # Hindi (handles Hinglish well)
                    alternative_language_codes=["en-IN"],
                )

                response = await speech_client.recognize(config=config, audio=audio)
                
                if not response.results:
                    return TranscriptionResult(transcript="", language_detected="hi", confidence=Decimal("0")) # type: ignore

                # Aggregate the best transcripts from the audio chunks
                best_result = response.results[0].alternatives[0]
                full_transcript = " ".join([result.alternatives[0].transcript for result in response.results])
                
                transcription = TranscriptionResult( # type: ignore
                    transcript=full_transcript, # type: ignore
                    language_detected="hi-IN", # type: ignore
                    confidence=Decimal(str(best_result.confidence)), # type: ignore
                )

                span.set_data("transcript_length", len(full_transcript))
                logger.info("Voice transcription complete via GCP")
                return transcription

            except Exception as e:
                logger.exception("GCP Voice transcription failed")
                sentry_sdk.capture_exception(e)
                raise
