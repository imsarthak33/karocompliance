from typing import List
from openai import AsyncOpenAI  # type: ignore
from anthropic import AsyncAnthropic  # type: ignore
from app.config import settings  # type: ignore
from supabase import create_client, Client  # type: ignore

# Part of NemoClaw Reference Stack Tools
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
anthropic_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

class RAGAgent:
    @staticmethod
    async def get_embedding(text: str) -> List[float]:
        response = await openai_client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding

    @classmethod
    async def retrieve_relevant_rules(cls, query: str, top_k: int = 5) -> str:
        query_embedding = await cls.get_embedding(query)
        
        response = supabase.rpc(
            'match_documents',
            {'query_embedding': query_embedding, 'match_threshold': 0.75, 'match_count': top_k}
        ).execute()
        
        if not response.data:
            return "No specific GST rules found in the database."
            
        context_chunks = [doc['content'] for doc in response.data]
        return "\n\n---\n\n".join(context_chunks)

    @classmethod
    async def answer_gst_question(cls, question: str) -> str:
        context = await cls.retrieve_relevant_rules(question)
        
        system_prompt = """You are an expert Indian GST practitioner. 
Answer the user's question based strictly on the provided regulatory context.
If the answer is not contained in the context, explicitly state: 'Please consult a GST practitioner for this specific query.'
Do not hallucinate rules or sections."""

        user_prompt = f"Context:\n{context}\n\nQuestion: {question}"

        response = await anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=500,
            temperature=0.1,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        
        return response.content[0].text