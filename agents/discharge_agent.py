from pydantic import BaseModel
from datetime import datetime
import re
import requests
from typing import Optional, Tuple
from db_manager import ChromaDocumentManager

class DischargeSummary(BaseModel):
    type: str = "discharge_summary"
    patient_name: str
    diagnosis: str
    admission_date: str
    discharge_date: str

class DischargeAgent:
    def __init__(self):
        """Initialize the discharge agent with LLaMA and ChromaDB connections."""
        self.llama_url = 'http://localhost:11434/api/generate'
        self.db_manager = ChromaDocumentManager()

    def _generate_llama_response(self, prompt: str) -> Optional[str]:
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
            else:
                print(f"Warning: LLaMA API returned status {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Warning: Could not connect to LLaMA model: {e}")
            return None

    def store_document(self, text: str, document_id: str) -> bool:
        """Store document in ChromaDB for later retrieval."""
        try:
            self.db_manager.store_document(text, document_id)
            return True
        except Exception as e:
            print(f"Error storing document in ChromaDB: {e}")
            return False

    def extract_discharge_info(self, document_id: str) -> DischargeSummary:
        """Extract discharge summary information using ChromaDB and LLaMA."""
        # Fetch all relevant sections from ChromaDB at once
        document_sections = {
            'demographics': self.db_manager.query_document(
                query="find patient name patient demographics name section patient information patient details registration data",
                document_id=document_id
            ),
            'diagnosis': self.db_manager.query_document(
                query="find primary diagnosis principal diagnosis final diagnosis chief complaint medical condition assessment impression clinical findings",
                document_id=document_id
            ),
            'dates': self.db_manager.query_document(
                query="find admission date discharge date hospital stay duration admitted on discharged on length of stay",
                document_id=document_id
            )
        }

        # Process each section with LLaMA
        patient_name = self._extract_patient_name(document_sections['demographics'])
        diagnosis = self._extract_diagnosis(document_sections['diagnosis'])
        admission_date, discharge_date = self._extract_dates(document_sections['dates'])

        return DischargeSummary(
            patient_name=patient_name,
            diagnosis=diagnosis,
            admission_date=admission_date,
            discharge_date=discharge_date
        )

    def _extract_patient_name(self, context: str) -> str:
        """Extract patient name using LLaMA to process ChromaDB data."""
        if not context:
            return "Unknown Patient"

        name_prompt = f"""Extract the patient's name from the following medical text.

Context:
{context}

Requirements:
1. Return ONLY the patient's full name
2. Ignore doctor names, staff names, or other people mentioned
3. If no clear patient name is found, return "UNKNOWN"
4. Format the response exactly as: PATIENT_NAME: [full name or UNKNOWN]

Example responses:
PATIENT_NAME: John A. Smith
PATIENT_NAME: UNKNOWN"""

        response = self._generate_llama_response(name_prompt)
        if match := re.search(r"PATIENT_NAME:\s*(.+?)(?:\n|$)", response):
            name = match.group(1).strip()
            if name != "UNKNOWN" and self._is_valid_patient_name(name):
                return self._format_name(name)

        return "Unknown Patient"

    def _extract_diagnosis(self, context: str) -> str:
        """Extract diagnosis using LLaMA to process ChromaDB data."""
        if not context:
            return "Unknown Diagnosis"

        diagnosis_prompt = f"""Extract the primary diagnosis from the following medical text.

Context:
{context}

Requirements:
1. Return ONLY the primary/principal diagnosis
2. Ignore secondary conditions or complications
3. If no clear diagnosis is found, return "UNKNOWN"
4. Format the response exactly as: PRIMARY_DIAGNOSIS: [diagnosis or UNKNOWN]

Example responses:
PRIMARY_DIAGNOSIS: Acute Myocardial Infarction
PRIMARY_DIAGNOSIS: UNKNOWN"""

        response = self._generate_llama_response(diagnosis_prompt)
        if match := re.search(r"PRIMARY_DIAGNOSIS:\s*(.+?)(?:\n|$)", response):
            diagnosis = match.group(1).strip()
            if diagnosis != "UNKNOWN":
                return diagnosis

        return "Unknown Diagnosis"

    def _extract_dates(self, context: str) -> Tuple[str, str]:
        """Extract admission and discharge dates using LLaMA to process ChromaDB data."""
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        if not context:
            return current_date, current_date

        dates_prompt = f"""Extract the admission and discharge dates from the following medical text.

Context:
{context}

Requirements:
1. Convert all dates to YYYY-MM-DD format
2. If a date is not found, return "UNKNOWN"
3. Format the response exactly as:
ADMISSION_DATE: [YYYY-MM-DD or UNKNOWN]
DISCHARGE_DATE: [YYYY-MM-DD or UNKNOWN]

Example responses:
ADMISSION_DATE: 2024-03-15
DISCHARGE_DATE: 2024-03-20

ADMISSION_DATE: UNKNOWN
DISCHARGE_DATE: UNKNOWN"""

        response = self._generate_llama_response(dates_prompt)
        
        admission_date = current_date
        discharge_date = current_date
        
        if response:
            if match := re.search(r"ADMISSION_DATE:\s*(\d{4}-\d{2}-\d{2})", response):
                admission_date = match.group(1)
            if match := re.search(r"DISCHARGE_DATE:\s*(\d{4}-\d{2}-\d{2})", response):
                discharge_date = match.group(1)

        return admission_date, discharge_date

    def _is_valid_patient_name(self, name: str) -> bool:
        """Enhanced validation for patient names."""
        if not name or len(name.strip()) < 3:
            return False

        # Clean and normalize the name
        name = name.strip()
        words = name.split()

        # Basic length and word count validation
        if len(words) < 2 or len(words) > 4:  # Allow for middle names/initials
            return False

        # Check each word
        for word in words:
            # Each word should be at least 2 characters (except middle initials)
            if len(word) == 1 and word != words[-1]:  # Allow single letter only for middle initial
                return False
            # First character should be uppercase
            if not word[0].isupper():
                return False
            # Rest should be letters, apostrophes, or hyphens
            if not re.match(r'^[A-Z][a-zA-Z\'-]*$', word):
                return False

        # Check for invalid patterns
        invalid_indicators = [
            # Titles and medical terms
            r'\b(?:DR|DOCTOR|PHYSICIAN|NURSE|MD|RN|PA|NP)\b',
            r'\b(?:HOSPITAL|CLINIC|CENTER|WARD|ROOM|ER|OR|ICU)\b',
            r'\b(?:ADMISSION|DISCHARGE|SUMMARY|REPORT|RECORD)\b',
            r'\b(?:DIAGNOSIS|TREATMENT|PROCEDURE|OPERATION)\b',
            
            # Common non-name words
            r'\b(?:THE|AND|OR|WITH|WITHOUT|NONE|YES|NO)\b',
            r'\b(?:NORMAL|ABNORMAL|POSITIVE|NEGATIVE)\b',
            r'\b(?:SIGNED|DICTATED|REVIEWED|NOTED)\b',
            
            # Numbers and special characters
            r'\d+',
            r'[#@%*=]',
            
            # Medical abbreviations
            r'\b(?:CBC|BMP|CMP|PT|PTT|INR|EKG|ECG|MRI|CT|XR)\b'
        ]

        name_upper = name.upper()
        for pattern in invalid_indicators:
            if re.search(pattern, name_upper):
                return False

        return True

    def _format_name(self, name: str) -> str:
        """Format patient name consistently."""
        # Handle comma-separated format (Last, First)
        if ',' in name:
            parts = name.split(',')
            if len(parts) == 2:
                last_name = parts[0].strip()
                first_name = parts[1].strip()
                name = f"{first_name} {last_name}"

        words = []
        for word in name.split():
            # Handle hyphenated names
            if '-' in word:
                parts = word.split('-')
                words.append('-'.join(p.capitalize() for p in parts))
            # Handle names with apostrophes
            elif "'" in word:
                parts = word.split("'")
                words.append("'".join(p.capitalize() for p in parts))
            # Handle middle initials
            elif len(word) == 1 or (len(word) == 2 and word.endswith('.')):
                words.append(word.upper().rstrip('.') + '.')
            # Regular names
            else:
                words.append(word.capitalize())

        return ' '.join(words)

    def _create_default_summary(self) -> DischargeSummary:
        """Create default summary for invalid input."""
        current_date = datetime.now().strftime("%Y-%m-%d")
        return DischargeSummary(
            patient_name="Unknown Patient",
            diagnosis="Unknown Diagnosis",
            admission_date=current_date,
            discharge_date=current_date
        )