from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Body
from pydantic import BaseModel
import os
import shutil
import json
from typing import List, Optional
from dotenv import load_dotenv

# Import our existing logic
from ingest import ingest_file
from helper import get_vectorstore, get_question_and_answers

# Load environment variables
load_dotenv()

app = FastAPI(title="MCQ Generator API")

# Initialize Vector Store
try:
    vector_store = get_vectorstore()
except Exception as e:
    print(f"Warning: Failed to initialize vector store: {e}")
    vector_store = None

class GenerateRequest(BaseModel):
    query: str
    standard: Optional[str] = None
    subject: Optional[str] = None
    chapter_name: Optional[str] = None

@app.post("/ingest")
async def ingest_document(
    file: UploadFile = File(...),
    standard: str = Form(...),
    subject: str = Form(...),
    chapter_number: str = Form(...),
    chapter_name: str = Form(...),
    syllabus: str = Form(...)
):
    """
    Uploads a file and ingests it into the vector database with metadata.
    """
    try:
        # Save file temporarily
        data_dir = "data"
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            
        file_path = os.path.join(data_dir, file.filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Construct metadata
        metadata = {
            "standard": standard,
            "subject": subject,
            "syllabus": syllabus,
            "chapter_number": chapter_number,
            "chapter_name": chapter_name
        }
        
        # Ingest
        success, message = ingest_file(file_path, metadata)
        
        if success:
            return {"status": "success", "message": message, "file": file.filename}
        else:
            raise HTTPException(status_code=500, detail=message)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate")
async def generate_questions(request: GenerateRequest):
    """
    Generates MCQs based on a query and metadata filters.
    """
    if not vector_store:
        raise HTTPException(status_code=503, detail="Vector store not initialized")
        
    try:
        # Construct metadata filter
        metadata_filter = {}
        if request.standard:
            metadata_filter["standard"] = request.standard
        if request.subject:
            metadata_filter["subject"] = request.subject
        if request.chapter_name:
            metadata_filter["chapter_name"] = request.chapter_name
            
        if not metadata_filter:
             raise HTTPException(status_code=400, detail="At least one metadata filter (standard, subject, chapter_name) must be provided.")

        # Generate questions
        response, docs = get_question_and_answers(
            vector_store, 
            query=request.query, 
            metadata_filter=metadata_filter
        )
        
        if response == "NO_RELEVANT_CONTENT":
            return {"status": "no_content", "message": "No relevant content found for your query."}
            
        try:
            # Parse JSON response from LLM
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            questions = json.loads(content.strip())
            return {"status": "success", "questions": questions}
        except json.JSONDecodeError:
             return {"status": "error", "message": "Failed to parse model response", "raw_response": response.content}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
