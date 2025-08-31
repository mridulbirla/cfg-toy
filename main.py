import logging
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn

from config import Config
from database.clickhouse_client import ClickHouseClient
from cfg.query_generator import QueryGenerator
from evaluation.evaluator import Evaluator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CFG + Eval Toy API", version="1.0.0")

# Initialize components
db_client = ClickHouseClient()
query_generator = QueryGenerator()
evaluator = Evaluator()

# Pydantic models
class QueryRequest(BaseModel):
    natural_language_query: str

class QueryResponse(BaseModel):
    generated_query: Optional[str] = None
    clarification: Optional[str] = None
    status: str
    results: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        is_connected = db_client.test_connection()
        return {
            "status": "healthy" if is_connected else "unhealthy",
            "database_connected": is_connected,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

@app.post("/query", response_model=QueryResponse)
async def generate_and_execute_query(request: QueryRequest):
    """Generate ClickHouse query from natural language and execute it"""
    try:
        # Generate query using GPT-5 CFG
        response = query_generator.generate_query(request.natural_language_query)
        
        # Check if we need clarification
        if response["status"] == "needs_clarification":
            return QueryResponse(
                generated_query=None,
                clarification=response["clarification"],
                status="needs_clarification",
                results=None,
                execution_time=None
            )
        
        # Execute query if we have one
        if response["query"]:
            result = db_client.execute_query(response["query"])
            return QueryResponse(
                generated_query=response["query"],
                clarification=response["clarification"],
                status="success",
                results=result,
                execution_time=result["execution_time"]
            )
        else:
            return QueryResponse(
                generated_query=None,
                clarification=response["clarification"],
                status="error",
                results=None,
                execution_time=None
            )
        
    except Exception as e:
        logger.error(f"Query generation/execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/evaluate")
async def run_evaluation():
    """Run evaluation tests and return results"""
    try:
        evaluation_results = evaluator.run_evaluation()
        return evaluation_results
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=Config.PORT,
        reload=Config.DEBUG
    )
