from pydantic import BaseModel
from typing import List, Union
from datetime import datetime
import re
import requests
from agents.discharge_agent import DischargeSummary

class Question(BaseModel):
    question: str

class BillDocument(BaseModel):
    type: str = "bill"
    hospital_name: str
    total_amount: float
    date_of_service: str

class ClaimResponse(BaseModel):
    documents: List[Union[BillDocument, DischargeSummary]]

class BillAgent:
    def __init__(self):
        self.llama_url = 'http://localhost:11434/api/generate'

    def _generate_llama_response(self, prompt: str) -> str:
        """Generate response using Ollama's LLaMA model."""
        response = requests.post(
            self.llama_url,
            json={
                "model": "llama3.2",
                "prompt": prompt,
                "stream": False
            }
        )
        if response.status_code == 200:
            return response.json()['response']
        else:
            raise Exception("Error communicating with LLaMA model")

    def _find_total_amount(self, text: str) -> float:
        """Extract total amount from text using specific keywords."""
        # Look for amounts with specific total-related keywords
        total_patterns = [
            r'(?:total\s+(?:amount|due|balance|charges?|bill|payment))[\s:]*\$?\s*([\d,]+\.?\d*)',
            r'(?:amount\s+(?:due|total))[\s:]*\$?\s*([\d,]+\.?\d*)',
            r'(?:balance\s+(?:due|total))[\s:]*\$?\s*([\d,]+\.?\d*)',
            r'(?:total)[\s:]*\$?\s*([\d,]+\.?\d*)',
            r'(?:due)[\s:]*\$?\s*([\d,]+\.?\d*)',
            # Add pattern for amounts that appear after "Total:" or similar
            r'(?:Total|Amount Due|Balance Due|Payment Due):\s*\$?\s*([\d,]+\.?\d*)'
        ]
        
        text = text.lower()  # Convert to lowercase for case-insensitive matching
        
        for pattern in total_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    amount_str = match.group(1).replace(',', '')
                    amount = float(amount_str)
                    if amount > 0:
                        return amount
                except ValueError:
                    continue
        
        return 0.0

    def extract_bill_info(self, text: str) -> BillDocument:
        """Extract bill information from text."""
        # Initialize default values
        hospital_name = "Unknown Hospital"
        total_amount = 0.0
        date_of_service = datetime.now().strftime("%Y-%m-%d")

        # First try to find the total amount directly from the text
        total_amount = self._find_total_amount(text)

        # Use LLaMA to extract structured information
        prompt = f"""You are a medical bill analysis expert. Extract the following information from this medical bill text. Be precise and only extract what you are certain about.

Text to analyze:
{text}

Please provide the information in this exact format:
HOSPITAL: [Extract the full hospital/facility name]
TOTAL_AMOUNT: [Extract ONLY the final total amount due/billed. Look for keywords like 'Total Due', 'Amount Due', 'Total Balance', 'Total Payment Due']
DATE: [Extract the service date in YYYY-MM-DD format, prefer the actual service date over bill date]

Only include information you find in the text. If you can't find something, use UNKNOWN. For the total amount, be very specific - only extract the final amount that needs to be paid."""

        response = self._generate_llama_response(prompt)
        
        try:
            # Extract hospital name
            if match := re.search(r"HOSPITAL:\s*(.+?)(?:\n|$)", response):
                hospital_name = match.group(1).strip()
                if hospital_name.upper() == "UNKNOWN":
                    hospital_name = "Unknown Hospital"

            # Extract total amount from LLaMA response if we haven't found it yet
            if total_amount == 0.0:
                if match := re.search(r"TOTAL_AMOUNT:\s*\$?\s*([\d,]+\.?\d*)", response):
                    total_str = match.group(1).replace(',', '')
                    try:
                        llama_total = float(total_str)
                        if llama_total > 0:
                            total_amount = llama_total
                    except ValueError:
                        pass

            # Extract date
            if match := re.search(r"DATE:\s*(\d{4}-\d{2}-\d{2})", response):
                date_of_service = match.group(1)
            else:
                # Try to find any date in the text
                date_pattern = r'(\d{4}-\d{2}-\d{2})'
                if date_match := re.search(date_pattern, text):
                    date_of_service = date_match.group(1)

        except Exception as e:
            print(f"Error parsing bill information: {e}")

        return BillDocument(
            hospital_name=hospital_name,
            total_amount=total_amount,
            date_of_service=date_of_service
        )

    def process_claim(self, text: str) -> ClaimResponse:
        """Process a medical bill claim from text."""
        bill_info = self.extract_bill_info(text)
        return ClaimResponse(documents=[bill_info]) 