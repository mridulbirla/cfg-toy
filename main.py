import logging
import time
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn
import json
import asyncio

from config import Config
from database.clickhouse_client import ClickHouseClient
from cfg.query_generator import QueryGenerator
from evaluation.evaluator import Evaluator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CFG + Eval Toy API", version="1.0.0")

# Load configuration from file if it exists
Config.load_config_from_file()

# Initialize components
db_client = ClickHouseClient(auto_connect=False)
query_generator = QueryGenerator()
evaluator = Evaluator(query_generator=query_generator, db_client=db_client)

# Pydantic models
class QueryRequest(BaseModel):
    natural_language_query: str

class QueryResponse(BaseModel):
    generated_query: Optional[str] = None
    clarification: Optional[str] = None
    status: str
    results: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None

class ConfigRequest(BaseModel):
    clickhouse: Optional[Dict[str, Any]] = None
    openai: Optional[Dict[str, Any]] = None

class TestResponse(BaseModel):
    connected: bool
    error: Optional[str] = None

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

@app.post("/evaluate-stream")
async def run_evaluation_stream():
    """Run evaluation tests with streaming progress updates"""
    async def generate_progress():
        try:
            # Send initial progress
            yield f"data: {json.dumps({'type': 'start', 'message': 'Starting evaluation...'})}\n\n"
            
            # Store progress updates
            progress_updates = []
            
            def progress_callback(current, total, description, status, result):
                progress_data = {
                    'type': 'progress',
                    'current': current,
                    'total': total,
                    'description': description,
                    'status': status,
                    'progress_percent': (current / total) * 100
                }
                progress_updates.append(progress_data)
            
            # Run evaluation with progress callback
            evaluation_results = evaluator.run_evaluation(progress_callback)
            
            # Send all progress updates
            for update in progress_updates:
                yield f"data: {json.dumps(update)}\n\n"
            
            # Send final results
            yield f"data: {json.dumps({'type': 'complete', 'results': evaluation_results})}\n\n"
            
        except Exception as e:
            logger.error(f"Streaming evaluation failed: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_progress(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

@app.post("/config")
async def update_configuration(request: ConfigRequest):
    """Update application configuration"""
    try:
        config_dict = request.dict()
        Config.update_config(config_dict)
        
        # Reconnect clients with new configuration
        if "clickhouse" in config_dict:
            db_client.reconnect()
        if "openai" in config_dict:
            query_generator.reconnect()
        
        return {"status": "success", "message": "Configuration updated successfully"}
    except Exception as e:
        logger.error(f"Configuration update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/test-clickhouse", response_model=TestResponse)
async def test_clickhouse_connection(request: ConfigRequest):
    """Test ClickHouse connection with provided configuration"""
    try:
        config_dict = request.dict()
        connected, error = db_client.test_connection_with_config(config_dict)
        return TestResponse(connected=connected, error=error)
    except Exception as e:
        logger.error(f"ClickHouse test failed: {e}")
        return TestResponse(connected=False, error=str(e))

@app.post("/test-openai", response_model=TestResponse)
async def test_openai_connection(request: ConfigRequest):
    """Test OpenAI connection with provided configuration"""
    try:
        config_dict = request.dict()
        connected, error = query_generator.test_connection_with_config(config_dict)
        return TestResponse(connected=connected, error=error)
    except Exception as e:
        logger.error(f"OpenAI test failed: {e}")
        return TestResponse(connected=False, error=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=Config.PORT,
        reload=Config.DEBUG
    )
