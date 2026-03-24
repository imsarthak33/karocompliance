from anthropic import AsyncAnthropic  # type: ignore
from app.config import settings  # type: ignore
from app.services import whatsapp_service  # type: ignore

anthropic_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

class CommunicationAgent:
    SYSTEM_PROMPT = """You are a professional assistant for a CA firm in India. Write WhatsApp messages to clients in natural, polite Hinglish (mix of Hindi and English).
Keep messages under 150 words. Be specific about what is needed. Never use formal English that sounds robotic. Sound like a helpful office assistant. Use respectful language — address client as 'aap'."""

    @classmethod
    async def request_missing_document(cls, client_wa_number: str, firm_wa_id: str, missing_items: list[str], deadline: str) -> str:
        items_str = ", ".join(missing_items)
        prompt = f"Write a message asking the client for these missing documents: {items_str}. The deadline is {deadline}. Warn them gently about late penalty/interest if missed."
        
        response = await anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=200,
            system=cls.SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        )
        
        msg_text = response.content[0].text
        await whatsapp_service.send_text_message(client_wa_number, msg_text, firm_wa_id)
        return msg_text

    @classmethod
    async def send_anomaly_alert_to_ca(cls, ca_firm_id: str, description: str):
        # Trigger real-time notifications via WebSocket (placeholder for now)
        print(f"Alerting CA Firm {ca_firm_id}: {description}")
        pass
