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
- [Demo Videos](#demo-videos)
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

## Demo Videos

### Process Claims Endpoint Demo

This video demonstrates the processing of multiple medical claims using the `/process-claim` endpoint:

https://github.com/your-username/medical-claims-processor/assets/videos/process-claims-demo.mp4

Key points demonstrated:

- Uploading multiple PDF files
- Real-time processing feedback
- Extracted information display
- Error handling scenarios

### Test Query Endpoint Demo

This video shows the document querying functionality using the `/test/query` endpoint:

https://github.com/your-username/medical-claims-processor/assets/videos/test-query-demo.mp4

Features shown:

- Document querying interface
- LLaMA model responses
- Different query types and responses
- Response accuracy demonstration

### How to Record Your Own Demo

If you want to record your own system demo:

1. **Recommended Screen Recording Tools**:

   - Windows: [OBS Studio](https://obsproject.com/) or Xbox Game Bar (Win + G)
   - Mac: QuickTime Player or [OBS Studio](https://obsproject.com/)
   - Linux: [SimpleScreenRecorder](https://www.maartenbaert.be/simplescreenrecorder/) or [OBS Studio](https://obsproject.com/)

2. **Recording Steps**:

   ```bash
   # 1. Start your application
   docker-compose up

   # 2. Start your screen recorder

   # 3. Demonstrate the following:
   # - Upload multiple PDFs
   # - Show the processing output
   # - Query the documents
   # - Show error handling

   # 4. Save the recording in MP4 format

   # 5. Add the video to your project's assets folder
   ```

3. **Video Guidelines**:

   - Resolution: 1920x1080 (Full HD) or 1280x720 (HD)
   - Format: MP4 with H.264 encoding
   - Duration: 2-5 minutes per endpoint
   - Include voice-over or text annotations for clarity

4. **Where to Upload**:
   - Add videos to your project's GitHub repository under `assets/videos/`
   - Update the video links in this README
   - Alternatively, host on a video platform and link here

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
