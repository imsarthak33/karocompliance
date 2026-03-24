"""
Voice Agent — Audio transcription via Whisper with strict Decimal typing.

Strict Mandates:
  • decimal.Decimal for confidence
  • Sentry span tracing
  • Explicit error logging
"""
import os
import tempfile
import logging
from decimal import Decimal

import sentry_sdk  # type: ignore
import whisper  # type: ignore
from pydantic import BaseModel, field_validator, ConfigDict  # type: ignore

logger = logging.getLogger(__name__)

# Note: Whisper large-v3 requires significant RAM/GPU.
# Lazy-load the model to avoid blocking import time in tests.
_whisper_model = None


def _get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        logger.info("Loading Whisper large-v3 model...")
        _whisper_model = whisper.load_model("large-v3")
    return _whisper_model


class TranscriptionResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    transcript: str
    language_detected: str
    confidence: Decimal

    @field_validator("confidence", mode="before")
    @classmethod
    def coerce_confidence(cls, v: object) -> Decimal:
        if v is None:
            return Decimal("0")
        try:
            return Decimal(str(v))
        except Exception:
            return Decimal("0")


class VoiceAgent:
    @staticmethod
    async def transcribe(audio_bytes: bytes, file_format: str = "ogg") -> TranscriptionResult:
        with sentry_sdk.start_span(op="agent.voice", description="transcribe") as span:
            span.set_data("audio_size_bytes", len(audio_bytes))
            span.set_data("file_format", file_format)

            with tempfile.NamedTemporaryFile(suffix=f".{file_format}", delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            try:
                model = _get_whisper_model()
                result = model.transcribe(tmp_path, language="hi", task="transcribe")

                transcription = TranscriptionResult(
                    transcript=result["text"],
                    language_detected=result.get("language", "hi"),
                    confidence=Decimal("1.0"),
                )

                span.set_data("transcript_length", len(transcription.transcript))
                span.set_data("language", transcription.language_detected)
                logger.info(
                    "Voice transcription complete: %d chars, language=%s",
                    len(transcription.transcript), transcription.language_detected,
                )
                return transcription

            except Exception as e:
                logger.exception("Voice transcription failed")
                sentry_sdk.capture_exception(e)
                raise

            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
