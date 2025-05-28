# Medical Claims Processing System

A sophisticated system for processing medical claims by analyzing medical bills and discharge summaries using AI. The system uses FastAPI for the backend, ChromaDB for document storage, and Ollama's LLaMA model for intelligent text processing.

## Table of Contents

- [Features](#features)
- [System Architecture](#system-architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Docker Setup](#docker-setup)
- [API Endpoints](#api-endpoints)
- [Usage Examples](#usage-examples)
- [Project Structure](#project-structure)
- [Components](#components)
- [Error Handling](#error-handling)
- [Future Improvements](#future-improvements)
- [Contributing](#contributing)

## Features

- Multiple PDF document processing
- Intelligent text extraction from medical documents
- Automated bill information extraction
- Discharge summary analysis
- Vector-based document storage using ChromaDB
- LLM-powered information extraction using Ollama
- Docker containerization for easy deployment
- GPU support for LLM processing

## System Architecture

The system consists of several key components:

1. **FastAPI Backend**

   - Handles HTTP requests
   - Manages file uploads
   - Coordinates processing pipeline

2. **Document Processing**

   - PDF text extraction
   - Document storage in ChromaDB
   - Vector-based document retrieval

3. **AI Processing**

   - Bill information extraction
   - Discharge summary analysis
   - LLaMA model integration

4. **Storage Layer**
   - ChromaDB for document storage
   - Vector embeddings for efficient retrieval
   - Persistent storage in Docker volumes

## Prerequisites

- Docker and Docker Compose
- NVIDIA GPU (optional, for improved performance)
- NVIDIA Container Toolkit (if using GPU)
- Python 3.11+ (for local development)

## Installation

### Using Docker (Recommended)

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd medical-claims-processor
   ```

2. Build and start the services:
   ```bash
   docker-compose up --build
   ```

### Local Development Setup

1. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Start the Ollama service separately:

   ```bash
   ollama run llama3.2
   ```

4. Run the FastAPI application:
   ```bash
   uvicorn app:app --reload
   ```

## Docker Setup

The project includes three main Docker configuration files:

1. `Dockerfile`: Builds the FastAPI application container
2. `docker-compose.yml`: Orchestrates the application and Ollama services
3. `.dockerignore`: Optimizes build context

To use GPU acceleration:

1. Install NVIDIA Container Toolkit
2. Verify GPU support:
   ```bash
   docker run --gpus all nvidia/cuda:11.0-base nvidia-smi
   ```

## API Endpoints

### 1. Process Claims

- **Endpoint**: `/process-claim`
- **Method**: POST
- **Description**: Process multiple medical bills and discharge summaries
- **Input**: Multiple PDF files
- **Output**: JSON with extracted information

```json
{
  "message": "Successfully processed N documents",
  "documents": [
    {
      "filename": "doc1.pdf",
      "bill_info": {
        "type": "bill",
        "hospital_name": "Example Hospital",
        "total_amount": 1234.56,
        "date_of_service": "2024-03-15"
      },
      "discharge_info": {
        "type": "discharge_summary",
        "patient_name": "John Doe",
        "diagnosis": "Example Diagnosis",
        "admission_date": "2024-03-10",
        "discharge_date": "2024-03-15"
      }
    }
  ]
}
```

### 2. Test Upload

- **Endpoint**: `/test/upload`
- **Method**: POST
- **Description**: Test endpoint for document upload and storage
- **Input**: Single PDF file
- **Output**: Document ID and success message

### 3. Test Query

- **Endpoint**: `/test/query`
- **Method**: POST
- **Description**: Query stored documents
- **Input**: Question in JSON format
- **Output**: AI-generated answer based on document context

## Usage Examples

### Python Client

```python
import requests

def process_claims(pdf_files):
    url = 'http://localhost:8000/process-claim'
    files = [('files', (f.name, f, 'application/pdf')) for f in pdf_files]
    response = requests.post(url, files=files)
    return response.json()

# Example usage
with open('claim1.pdf', 'rb') as f1, open('claim2.pdf', 'rb') as f2:
    result = process_claims([f1, f2])
print(result)
```

### cURL

```bash
curl -X POST "http://localhost:8000/process-claim" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "files=@claim1.pdf" \
     -F "files=@claim2.pdf"
```

## Project Structure

```
medical-claims-processor/
├── agents/
│   ├── bill_agent.py
│   └── discharge_agent.py
├── app.py
├── db_manager.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .dockerignore
```

## Components

### Bill Agent

- Extracts billing information from medical documents
- Uses pattern matching and LLM for information extraction
- Handles various bill formats and structures

### Discharge Agent

- Processes discharge summaries
- Extracts patient information, diagnoses, and dates
- Integrates with ChromaDB for document storage

### DB Manager

- Manages ChromaDB interactions
- Handles document storage and retrieval
- Implements vector-based search functionality

## Error Handling

The system implements comprehensive error handling:

- Input validation for PDF files
- Processing pipeline error management
- API error responses with detailed messages
- Docker container health checks

## Future Improvements

### 1. Performance Optimizations

- **Parallel Processing**: Implement concurrent processing of multiple documents
  ```python
  # Example of parallel processing implementation
  async def process_documents(files):
      tasks = [process_single_document(file) for file in files]
      return await asyncio.gather(*tasks)
  ```
- **Batch Processing**: Add support for processing documents in batches
- **Caching Layer**: Implement Redis caching for frequently accessed documents

### 2. Enhanced AI Processing

- **Model Improvements**:
  - Fine-tune LLaMA model on medical documents
  - Implement hybrid approach combining rule-based and AI processing
  - Add support for multiple LLM options (GPT-4, Claude, etc.)
- **Information Extraction**:
  - Improve accuracy of amount detection
  - Add support for more medical document types
  - Enhance entity recognition for medical terms

### 3. Document Processing

- **Format Support**:
  - Add support for more document formats (DOCX, Images, etc.)
  - Implement OCR for scanned documents
  - Handle digital signatures and stamps
- **Quality Control**:
  - Add document quality validation
  - Implement confidence scores for extracted information
  - Add automated verification steps

### 4. Security Enhancements

- **Data Protection**:
  ```python
  # Example of enhanced security implementation
  class SecureDocument(BaseModel):
      content: str
      encryption_key: str
      access_level: str
      audit_trail: List[AuditEvent]
  ```
- Implement end-to-end encryption
- Add role-based access control
- Enhanced audit logging

### 5. User Interface

- Add web interface for document upload
- Real-time processing status updates
- Interactive document viewer
- Custom dashboard for analytics

### 6. Integration Capabilities

- **Healthcare Systems**:
  - HL7 FHIR integration
  - EMR/EHR system connectivity
  - Insurance provider APIs
- **Export Options**:
  - Multiple export formats (PDF, Excel, JSON)
  - Custom report generation
  - Automated email notifications

### 7. Monitoring and Analytics

```python
# Example monitoring implementation
class ProcessingMetrics:
    def __init__(self):
        self.processing_times = []
        self.success_rate = 0
        self.error_counts = defaultdict(int)
        self.accuracy_scores = []

    def track_processing(self, duration, success, error_type=None):
        self.processing_times.append(duration)
        self.success_rate = sum(self.processing_times) / len(self.processing_times)
        if error_type:
            self.error_counts[error_type] += 1
```

- Real-time performance monitoring
- Error rate tracking
- Processing time analytics
- Accuracy metrics

### 8. Testing and Validation

- Expand unit test coverage
- Add integration tests
- Implement automated validation
- Create benchmark datasets

### 9. Scalability Improvements

- **Horizontal Scaling**:
  - Implement load balancing
  - Add distributed processing
  - Microservices architecture
- **Storage Optimization**:
  - Implement document archiving
  - Optimize database queries
  - Add data retention policies

### 10. Documentation and Maintenance

- API documentation automation
- System architecture diagrams
- Regular dependency updates
- Performance optimization guides

To implement these improvements:

1. Prioritize based on user needs
2. Create detailed technical specifications
3. Implement changes incrementally
4. Maintain backward compatibility
5. Regular testing and validation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
