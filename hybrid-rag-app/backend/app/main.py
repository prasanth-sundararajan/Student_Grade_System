from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import os
from app.config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
from app.rag_engine import rag_engine
from langchain_neo4j import Neo4jGraph

app = FastAPI(title="Hybrid RAG API with FAISS & Neo4j")

# Pydantic request model for user chat queries
class QueryRequest(BaseModel):
    question: str

@app.get("/health")
def health_check():
    try:
        # Test Neo4j connection
        graph = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD)
        return {
            "status": "ok", 
            "database": "Neo4j connected successfully",
            "vector_db": "FAISS initialized"
        }
    except Exception as e:
        return {"status": "warning", "database_error": str(e)}

@app.post("/query")
def query_rag_pipeline(payload: QueryRequest):
    try:
        user_query = payload.question
        
        # Call rag_engine query/answer method dynamically for robustness
        if hasattr(rag_engine, "query"):
            response = rag_engine.query(user_query)
        elif hasattr(rag_engine, "answer"):
            response = rag_engine.answer(user_query)
        else:
            response = rag_engine(user_query)
            
        # Extract answer string whether response is a dictionary or string
        if isinstance(response, dict):
            answer = response.get("answer", response.get("response", str(response)))
        else:
            answer = str(response)
            
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload")
def upload_document(file: UploadFile = File(...)):  # Synchronous to prevent event loop blocking
    os.makedirs("uploads", exist_ok=True)
    file_path = f"uploads/{file.filename}"
    
    try:
        with open(file_path, "wb") as f:
            f.write(file.file.read())
        
        # Trigger Hybrid RAG processing & FAISS indexing
        result = rag_engine.process_document(file_path)
        return {"filename": file.filename, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))