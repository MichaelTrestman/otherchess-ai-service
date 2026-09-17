from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import time
import logging

from ai_engine import AIEngine
from models import BoardState, MoveRequest, MoveResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Expansion Chess AI API",
    description="AI move calculation service for Expansion Chess",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI engine
ai_engine = AIEngine()

@app.get("/")
async def root():
    return {"message": "Expansion Chess AI API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "ai_engine": "ready"}

@app.post("/api/v1/ai/move", response_model=MoveResponse)
async def get_ai_move(request: MoveRequest):
    """
    Calculate the best move for the given board state and AI type.
    """
    start_time = time.time()
    
    try:
        logger.info(f"Processing AI move request for {request.ai_type} AI, side: {request.side}")
        
        # Validate board state
        if not request.board_state.is_valid():
            raise HTTPException(status_code=400, detail="Invalid board state")
        
        # Calculate move
        move_result = ai_engine.calculate_move(
            board_state=request.board_state,
            ai_type=request.ai_type,
            side=request.side
        )
        
        if not move_result:
            raise HTTPException(status_code=500, detail="AI engine failed to calculate move")
        
        # Calculate thinking time
        thinking_time_ms = int((time.time() - start_time) * 1000)
        
        # Create response
        response = MoveResponse(
            move=move_result["move"],
            score=move_result["score"],
            thinking_time_ms=thinking_time_ms,
            ai_type=request.ai_type,
            side=request.side
        )
        
        logger.info(f"AI move calculated successfully in {thinking_time_ms}ms")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in AI move calculation: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/ai/types")
async def get_ai_types():
    """
    Get list of available AI types.
    """
    return {
        "ai_types": ai_engine.get_available_ai_types(),
        "default": "smart2"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
