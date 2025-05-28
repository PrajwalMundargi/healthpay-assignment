from typing import Dict, List, Tuple
import requests
from pydantic import BaseModel

class DocumentType:
    BILL = "bill"
    DISCHARGE = "discharge_summary"
    UNKNOWN = "unknown"

class DocumentClassification(BaseModel):
    document_type: str
    confidence: float

class DocumentOrchestrator:
    def __init__(self):
        """Initialize the document orchestrator with LLaMA connection."""
        self.llama_url = 'http://localhost:11434/api/generate'

    def _generate_llama_response(self, prompt: str) -> str:
        """Generate response using Ollama's LLaMA model."""
        try:
            response = requests.post(
                self.llama_url,
                json={
                    "model": "llama3.2",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            if response.status_code == 200:
                return response.json()['response']
            return None
        except Exception:
            return None

    def classify_document(self, text: str) -> DocumentClassification:
        """
        Classify a document as either a bill or discharge summary.
        
        Args:
            text: The text content of the document
            
        Returns:
            DocumentClassification with document type and confidence
        """
        # Create a prompt that asks LLaMA to classify the document
        classification_prompt = f"""Classify this medical document as either a "bill" or "discharge_summary".

Key Indicators:
- Bills typically contain: amounts, charges, services, payments, insurance details
- Discharge summaries typically contain: patient info, diagnosis, treatment, medications, follow-up care

Text to classify (first 1000 characters):
{text[:1000]}...

Respond ONLY with:
DOCUMENT_TYPE: [bill or discharge_summary]
CONFIDENCE: [number between 0 and 1]"""

        response = self._generate_llama_response(classification_prompt)
        
        if not response:
            return DocumentClassification(
                document_type=DocumentType.UNKNOWN,
                confidence=0.0
            )

        # Extract classification and confidence
        doc_type = DocumentType.UNKNOWN
        confidence = 0.0

        for line in response.split('\n'):
            if line.startswith('DOCUMENT_TYPE:'):
                type_str = line.split(':')[1].strip().lower()
                if type_str == "bill":
                    doc_type = DocumentType.BILL
                elif type_str in ["discharge_summary", "discharge summary"]:
                    doc_type = DocumentType.DISCHARGE
            elif line.startswith('CONFIDENCE:'):
                try:
                    confidence = float(line.split(':')[1].strip())
                except ValueError:
                    confidence = 0.0

        return DocumentClassification(
            document_type=doc_type,
            confidence=confidence
        )

    def process_documents(self, documents: List[Tuple[str, str]]) -> Dict[str, List[str]]:
        """
        Process and classify multiple documents.
        
        Args:
            documents: List of tuples containing (document_id, text_content)
            
        Returns:
            Dictionary with document types as keys and lists of document IDs as values
        """
        classified_docs = {
            DocumentType.BILL: [],
            DocumentType.DISCHARGE: [],
            DocumentType.UNKNOWN: []
        }
        
        for doc_id, text in documents:
            classification = self.classify_document(text)
            classified_docs[classification.document_type].append(doc_id)
            
        return classified_docs 