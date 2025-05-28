from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import PyPDF2
import os
from typing import Dict, List
import tempfile
import requests
from db_manager import ChromaDocumentManager
from pydantic import BaseModel
from agents.bill_agent import BillAgent, Question
from agents.discharge_agent import DischargeAgent

# Get Ollama URL from environment variable or use default
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')

app = FastAPI()

# Initialize managers
db_manager = ChromaDocumentManager()
bill_agent = BillAgent()
discharge_agent = DischargeAgent()

def extract_text_from_pdf(pdf_file) -> str:
    """Extract text from uploaded PDF file."""
    try:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(pdf_file.file.read())
            temp_file_path = temp_file.name

        with open(temp_file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted

        os.unlink(temp_file_path)
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing PDF: {str(e)}")

def generate_llama_response(prompt: str) -> str:
    """Generate response using Ollama's LLaMA model."""
    response = requests.post(
        f'{OLLAMA_BASE_URL}/api/generate',
        json={
            "model": "llama3.2",
            "prompt": prompt,
            "stream": False
        }
    )
    if response.status_code == 200:
        return response.json()['response']
    else:
        raise HTTPException(status_code=500, detail="Error communicating with LLaMA model")

@app.post("/test/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and process a PDF file."""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    text = extract_text_from_pdf(file)
    document_id = file.filename.replace('.pdf', '')
    
    # Store in ChromaDB
    if not discharge_agent.store_document(text, document_id):
        raise HTTPException(status_code=500, detail="Failed to store document in ChromaDB")

    return JSONResponse(content={
        "message": "PDF processed and stored in ChromaDB successfully",
        "document_id": document_id
    })

@app.post("/test/query")
async def query_document(question: Question):
    """Query the document using LLaMA model."""
    context = db_manager.query_document(question.question)
    
    if not context:
        return JSONResponse(content={"answer": "No relevant information found"})
    
    prompt = f"""Based on the following context, please answer the question.
    
Context:
{context}

Question: {question.question}

Answer:"""
    
    response = generate_llama_response(prompt)
    
    return JSONResponse(content={"answer": response.strip()})

@app.post("/process-claim")
async def process_claim(files: List[UploadFile] = File(...)):
    """Process multiple medical bills and discharge summary claims."""
    processed_documents = []
    
    for file in files:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail=f"File {file.filename} must be a PDF")
        
        # Extract text from PDF
        text = extract_text_from_pdf(file)
        document_id = file.filename.replace('.pdf', '')
        
        try:
            # Store document in ChromaDB first
            if not discharge_agent.store_document(text, document_id):
                raise HTTPException(status_code=500, detail=f"Failed to store document {file.filename} in ChromaDB")
            
            # Process both bill and discharge information
            # Note: Bill agent still processes directly, while discharge agent uses ChromaDB
            bill_info = bill_agent.extract_bill_info(text)
            discharge_info = discharge_agent.extract_discharge_info(document_id)
            
            # Add to processed documents - convert Pydantic models to dict
            processed_documents.append({
                "filename": file.filename,
                "bill_info": bill_info.model_dump(),
                "discharge_info": discharge_info.model_dump()
            })
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing claim for {file.filename}: {str(e)}")
    
    return {
        "message": f"Successfully processed {len(processed_documents)} documents",
        "documents": processed_documents
    }
