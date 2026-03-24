import json
import re
import pandas as pd  # type: ignore
import io
from typing import List, Optional
from pydantic import BaseModel  # type: ignore
from anthropic import AsyncAnthropic  # type: ignore
from app.config import settings  # type: ignore

anthropic_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

class LineItem(BaseModel):
    description: Optional[str]
    hsn_sac: Optional[str]
    quantity: Optional[float]
    unit_price: Optional[float]
    taxable_value: Optional[float]
    gst_rate: Optional[float]
    cgst: Optional[float]
    sgst: Optional[float]
    igst: Optional[float]
    total: Optional[float]

class InvoiceData(BaseModel):
    invoice_number: Optional[str]
    invoice_date: Optional[str]
    vendor_name: Optional[str]
    vendor_gstin: Optional[str]
    buyer_name: Optional[str]
    buyer_gstin: Optional[str]
    line_items: List[LineItem] = []
    total_taxable_value: Optional[float]
    total_cgst: Optional[float]
    total_sgst: Optional[float]
    total_igst: Optional[float]
    total_invoice_value: Optional[float]
    place_of_supply: Optional[str]
    is_reverse_charge: bool = False
    currency: str = "INR"

class BankTransaction(BaseModel):
    date: str
    description: str
    debit_amount: Optional[float]
    credit_amount: Optional[float]
    balance: Optional[float]
    reference_number: Optional[str]

class ExtractionAgent:
    GSTIN_REGEX = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")

    @classmethod
    async def parse_invoice(cls, ocr_text: str, doc_type: str) -> InvoiceData:
        system_prompt = """You are an expert at extracting data from Indian GST invoices.
Extract ALL required fields. If a field is not found, return null. Never invent data.
Return ONLY valid JSON matching the exact schema requested, with no markdown formatting.
Note: Indian vendor names often mix Hindi and English (e.g., 'Shri Ram Traders', 'Ganesh Enterprises')."""
        
        user_prompt = f"Document Type: {doc_type}\n\nOCR Text:\n{ocr_text}\n\nExtract and map to the JSON schema."
        
        response = await anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=2000,
            temperature=0,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        
        try:
            data = json.loads(response.content[0].text.strip('```json\n'))
            invoice = InvoiceData(**data)
            
            # Validate GSTINs
            if invoice.vendor_gstin and not cls.GSTIN_REGEX.match(invoice.vendor_gstin):  # type: ignore
                invoice.vendor_gstin = f"UNVERIFIED:{invoice.vendor_gstin}"
            
            return invoice
        except Exception as e:
            raise ValueError(f"Failed to extract invoice data: {str(e)}")

    @classmethod
    async def parse_bank_statement(cls, ocr_text: str) -> List[BankTransaction]:
        prompt = """Extract bank transactions from the following OCR text. 
Return ONLY a JSON array of objects with keys: date, description, debit_amount, credit_amount, balance, reference_number.
Return null for missing float values."""
        
        response = await anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=4000,
            temperature=0,
            messages=[{"role": "user", "content": f"{prompt}\n\n{ocr_text}"}]
        )
        data = json.loads(response.content[0].text.strip('```json\n'))
        return [BankTransaction(**tx) for tx in data]

    @classmethod
    async def parse_excel_register(cls, file_bytes: bytes) -> List[dict]:
        df = pd.read_excel(io.BytesIO(file_bytes))
        head_csv = df.head(3).to_csv(index=False)
        
        prompt = f"""Identify the columns for invoice_number, date, vendor_name, total_amount, and gstin from this CSV header and sample data. 
Return ONLY a JSON dictionary mapping standard keys to the exact column names found in the CSV.
Sample data:\n{head_csv}"""
        
        response = await anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=300,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )
        col_map = json.loads(response.content[0].text.strip('```json\n'))
        
        extracted = []
        for _, row in df.iterrows():
            tx = {standard_key: row.get(excel_col) for standard_key, excel_col in col_map.items()}
            extracted.append(tx)
        return extracted
