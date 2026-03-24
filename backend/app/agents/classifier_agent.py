import json
import base64
from typing import Literal
from pydantic import BaseModel, Field  # type: ignore
from anthropic import AsyncAnthropic  # type: ignore
from openai import AsyncOpenAI  # type: ignore
from app.config import settings  # type: ignore

anthropic_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

DocumentType = Literal[
    'purchase_invoice', 'sale_invoice', 'bank_statement', 
    'credit_note', 'debit_note', 'purchase_register', 'salary_slip', 'unknown'
]

class ClassificationResult(BaseModel):
    type: DocumentType
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str

class ClassifierAgent:
    @staticmethod
    async def classify_pdf(pdf_text: str, file_name: str) -> ClassificationResult:
        text_str = str(pdf_text)
        excerpt = text_str[:500]  # type: ignore
        prompt = f"""You are a document classification expert for Indian GST compliance.
Classify the document into exactly one of these types: purchase_invoice, sale_invoice, bank_statement, credit_note, debit_note, purchase_register, salary_slip, unknown.
Return ONLY a JSON object: {{"type": "<type>", "confidence": 0.0-1.0, "reasoning": "<one sentence>"}}
Filename: {file_name}
Excerpt: {excerpt}"""

        response = await anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=150,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            result = json.loads(response.content[0].text)
            parsed = ClassificationResult(**result)
            if parsed.confidence < 0.7:
                parsed.type = 'unknown'
            return parsed
        except (json.JSONDecodeError, ValueError):
            return ClassificationResult(type='unknown', confidence=0.0, reasoning="Parsing failure")  # type: ignore

    @staticmethod
    async def classify_image(image_bytes: bytes) -> ClassificationResult:
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        prompt = """You are a document classification expert for Indian GST compliance.
Classify the document into exactly one of these types: purchase_invoice, sale_invoice, bank_statement, credit_note, debit_note, purchase_register, salary_slip, unknown.
Return ONLY a JSON object: {"type": "<type>", "confidence": 0.0-1.0, "reasoning": "<one sentence>"}"""

        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ],
                }
            ],
            max_tokens=150,
            temperature=0
        )
        try:
            result = json.loads(response.choices[0].message.content.strip('```json\n'))
            parsed = ClassificationResult(**result)
            if parsed.confidence < 0.7:
                parsed.type = 'unknown'
            return parsed
        except Exception:
            return ClassificationResult(type='unknown', confidence=0.0, reasoning="Vision parsing failure")  # type: ignore