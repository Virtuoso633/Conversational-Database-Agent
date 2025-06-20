# app.py
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Optional
import json
from datetime import datetime
from src.database_manager import DatabaseManager
from src.nlp_processor import NLPProcessor
from src.conversation_manager import ConversationManager
from config.settings import config

app = FastAPI(title="Conversational DB Agent")

db_manager = DatabaseManager(config.MONGODB_URI, config.DATABASE_NAME)
if not db_manager.connect():
    raise RuntimeError("Database connection failed")

nlp_processor = NLPProcessor(db_manager)
conv_manager = ConversationManager()

class QueryRequest(BaseModel):
    session_id: Optional[str] = None
    collection: str
    query_text: str

class QueryResponse(BaseModel):
    session_id: str
    data: List[dict] = Field(default_factory=list)
    execution_time: float
    error: Optional[str] = None
    error_type: Optional[str] = None

def convert_datetime_to_str(obj):
    """Recursively convert datetime objects to ISO strings"""
    if isinstance(obj, dict):
        return {k: convert_datetime_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_datetime_to_str(i) for i in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    return obj

@app.post("/query", response_model=QueryResponse)
def handle_query(request: QueryRequest):
    # Manage session
    session_id = request.session_id or conv_manager.session_id
    if not request.session_id:
        conv_manager.session_id = session_id

    # Log user message
    conv_manager.add_user_message_to_analytics(request.query_text)

    # Parse and execute query
    intent = nlp_processor.parse_query(request.query_text, request.collection)
    
    # Handle error responses
    if intent.get("query_type") == "error":
        error_type = intent.get("error_type", "unknown")
        error_msg = intent.get("error_message", "Could not process request")
        
        # Log and return error
        conv_manager.add_ai_message_to_analytics(
            text=f"ERROR: {error_msg}",
            intent=intent,
            success_flag=False,
            exec_time=0.0
        )
        return QueryResponse(
            session_id=session_id,
            data=[],
            execution_time=0.0,
            error=error_msg,
            error_type=error_type
        )
    
    # Execute valid query
    result = nlp_processor.execute_intent(request.collection, intent)
    
    # Prepare and sanitize response
    response_data = convert_datetime_to_str(result.get("data", []))
    execution_time = result.get("execution_time_seconds", 0.0)
    success = result.get("success", False)
    
    # Log AI response
    conv_manager.add_ai_message_to_analytics(
        text=str(response_data),
        intent=intent,
        success_flag=success,
        exec_time=execution_time
    )
    
    # Save interaction to memory
    conv_manager.save_interaction_to_memory(
        user_input=request.query_text,
        ai_output=str(response_data)
    )

    return QueryResponse(
        session_id=session_id,
        data=response_data,
        execution_time=execution_time
    )
