import os
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv  # type: ignore
from supabase import create_client, Client  # type: ignore
from langchain_community.document_loaders import PyMuPDFLoader  # type: ignore
from langchain_text_splitters import RecursiveCharacterTextSplitter  # type: ignore
from openai import AsyncOpenAI  # type: ignore

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from the backend/.env file
# Adjusted to look for .env in the backend directory
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Initialize Clients
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
if not supabase_url or not supabase_key:
    raise ValueError("Missing Supabase credentials in environment variables (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY).")

supabase: Client = create_client(supabase_url, supabase_key)
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configuration
PDF_DIRECTORY = Path(__file__).resolve().parent.parent / 'data' / 'gst_rules'
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
EMBEDDING_MODEL = "text-embedding-3-small"

async def get_embedding(text: str) -> list[float]:
    """Fetch embeddings from OpenAI."""
    response = await openai_client.embeddings.create(
        input=text,
        model=EMBEDDING_MODEL
    )
    return response.data[0].embedding

async def process_and_upload_pdf(file_path: Path):
    """Loads a PDF, chunks it, embeds the chunks, and uploads to Supabase."""
    logger.info(f"Processing {file_path.name}...")

    # 1. Load PDF
    try:
        loader = PyMuPDFLoader(str(file_path))
        documents = loader.load()
    except Exception as e:
        logger.error(f"Failed to load {file_path.name}: {e}")
        return

    # 2. Split Text
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    logger.info(f"Split {file_path.name} into {len(chunks)} chunks.")

    # 3. Embed and Upload in batches
    batch_size = 50
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        records_to_insert = []

        for chunk in batch:
            try:
                # Generate embedding
                embedding = await get_embedding(chunk.page_content)
                
                # Prepare record
                record = {
                    "content": chunk.page_content,
                    "metadata": {
                        "source_file": file_path.name,
                        "page_number": chunk.metadata.get("page", 0),
                        "chunk_index": i + batch.index(chunk)
                    },
                    "embedding": embedding
                }
                records_to_insert.append(record)
            except Exception as e:
                logger.error(f"Error embedding chunk from {file_path.name}: {e}")

        # 4. Insert into Supabase
        if records_to_insert:
            try:
                supabase.table("gst_knowledge_base").insert(records_to_insert).execute()
                logger.info(f"Successfully uploaded batch of {len(records_to_insert)} chunks.")
            except Exception as e:
                logger.error(f"Database insertion failed for batch: {e}")

async def main():
    if not PDF_DIRECTORY.exists():
        logger.warning(f"Directory not found: {PDF_DIRECTORY}. Creating it now.")
        PDF_DIRECTORY.mkdir(parents=True)
        logger.info("Please drop your GST PDFs into the 'backend/data/gst_rules' folder and run this script again.")
        return

    pdf_files = list(PDF_DIRECTORY.glob("*.pdf"))
    if not pdf_files:
        logger.info(f"No PDFs found in {PDF_DIRECTORY}.")
        return

    logger.info(f"Found {len(pdf_files)} PDFs to process.")
    
    for pdf in pdf_files:
        await process_and_upload_pdf(pdf)
        
    logger.info("Vector database seeding complete!")

if __name__ == "__main__":
    asyncio.run(main())
