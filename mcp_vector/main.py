"""
MCP Vector Server main module
"""
import os
import sys
import json
import logging
import argparse
import asyncio
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
import signal
import uvicorn
from fastapi import FastAPI, Response, Request, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from .mcp.vector_handler import MCPVectorHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("mcp-vector")

# Global variables
mcp_handler = None
app = FastAPI(title="MCP Vector Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MCP Request models
class VectorSearchRequest(BaseModel):
    query: str = Field(..., description="Query string to search for")
    top_k: int = Field(5, description="Number of results to return")
    paths: Optional[List[str]] = Field(None, description="Optional list of specific paths to search within")

class VectorRunRequest(BaseModel):
    paths: Optional[List[str]] = Field(None, description="Optional list of specific paths to process")

# MCP Routes
@app.post("/mcp/vector_search")
async def mcp_vector_search(request: VectorSearchRequest):
    """MCP endpoint for vector search"""
    global mcp_handler
    if not mcp_handler:
        raise HTTPException(status_code=503, detail="MCP handler not initialized")
    
    try:
        result = await mcp_handler.vector_search(
            query=request.query,
            top_k=request.top_k,
            paths=request.paths
        )
        return result
    except Exception as e:
        logger.error(f"Error in vector_search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mcp/vector_status")
async def mcp_vector_status():
    """MCP endpoint for getting vector database status"""
    global mcp_handler
    if not mcp_handler:
        raise HTTPException(status_code=503, detail="MCP handler not initialized")
    
    try:
        result = await mcp_handler.vector_status()
        return result
    except Exception as e:
        logger.error(f"Error in vector_status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/vector_run")
async def mcp_vector_run(request: VectorRunRequest):
    """MCP endpoint for running embedding on all files"""
    global mcp_handler
    if not mcp_handler:
        raise HTTPException(status_code=503, detail="MCP handler not initialized")
    
    try:
        result = await mcp_handler.vector_run(paths=request.paths)
        return result
    except Exception as e:
        logger.error(f"Error in vector_run: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# HTTP API Routes (non-MCP)
@app.post("/api/vector/search")
async def http_vector_search(request: VectorSearchRequest):
    """HTTP API endpoint for vector search"""
    global mcp_handler
    if not mcp_handler:
        raise HTTPException(status_code=503, detail="MCP handler not initialized")
    
    try:
        result = await mcp_handler.vector_search(
            query=request.query,
            top_k=request.top_k,
            paths=request.paths
        )
        return result
    except Exception as e:
        logger.error(f"Error in HTTP vector_search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/vector/status")
async def http_vector_status():
    """HTTP API endpoint for getting vector database status"""
    global mcp_handler
    if not mcp_handler:
        raise HTTPException(status_code=503, detail="MCP handler not initialized")
    
    try:
        result = await mcp_handler.vector_status()
        return result
    except Exception as e:
        logger.error(f"Error in HTTP vector_status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/vector/run")
async def http_vector_run(request: VectorRunRequest):
    """HTTP API endpoint for running embedding on all files"""
    global mcp_handler
    if not mcp_handler:
        raise HTTPException(status_code=503, detail="MCP handler not initialized")
    
    try:
        result = await mcp_handler.vector_run(paths=request.paths)
        return result
    except Exception as e:
        logger.error(f"Error in HTTP vector_run: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Standard endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    global mcp_handler
    return {"status": "healthy", "initialized": mcp_handler is not None}

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="MCP Vector Server")
    
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to")
    parser.add_argument("--model", type=str, help="Name of the embedding model")
    parser.add_argument("--db-path", type=str, help="Path to store the vector database")
    parser.add_argument("--watch-folder", action="append", help="Folder to watch (can be specified multiple times)")
    
    return parser.parse_args()

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from file or environment"""
    config = {
        "host": os.environ.get("MCP_VECTOR_HOST", "127.0.0.1"),
        "port": int(os.environ.get("MCP_VECTOR_PORT", "5000")),
        "model_name": os.environ.get("MCP_VECTOR_MODEL", "paraphrase-multilingual-MiniLM-L12-v2"),
        "db_path": os.environ.get("MCP_VECTOR_DB_PATH", os.path.expanduser("~/.mcp-vector/db")),
        "watch_folders": os.environ.get("MCP_VECTOR_WATCH_FOLDERS", "").split(";") if os.environ.get("MCP_VECTOR_WATCH_FOLDERS") else [],
        "supported_extensions": set(os.environ.get("MCP_VECTOR_EXTENSIONS", "").split(",")) if os.environ.get("MCP_VECTOR_EXTENSIONS") else None,
    }
    
    # Load from config file if specified
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                
                # Update config with file values
                for key, value in file_config.items():
                    if key == "watch_folders" and isinstance(value, list):
                        config["watch_folders"] = value
                    elif key == "supported_extensions" and isinstance(value, list):
                        config["supported_extensions"] = set(value)
                    elif key in config:
                        config[key] = value
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
    
    return config

def setup_signal_handlers():
    """Set up signal handlers for graceful shutdown"""
    def handle_signal(sig, frame):
        logger.info(f"Received signal {sig}, shutting down...")
        if mcp_handler:
            mcp_handler.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

def main():
    """Main entry point"""
    global mcp_handler
    
    # Parse command line arguments
    args = parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Override config with command line arguments
    if args.host:
        config["host"] = args.host
    if args.port:
        config["port"] = args.port
    if args.model:
        config["model_name"] = args.model
    if args.db_path:
        config["db_path"] = args.db_path
    if args.watch_folder:
        config["watch_folders"] = args.watch_folder
    
    # Ensure we have at least one watch folder
    if not config["watch_folders"]:
        logger.warning("No watch folders specified, using current directory")
        config["watch_folders"] = [os.getcwd()]
    
    # Ensure paths are expanded
    config["db_path"] = os.path.expanduser(config["db_path"])
    config["watch_folders"] = [os.path.expanduser(path) for path in config["watch_folders"]]
    
    logger.info(f"Server configuration: {json.dumps({k: v for k, v in config.items() if k != 'supported_extensions'}, indent=2)}")
    
    # Set up signal handlers
    setup_signal_handlers()
    
    # Initialize MCP handler
    try:
        mcp_handler = MCPVectorHandler(
            model_name=config["model_name"],
            db_path=config["db_path"],
            watch_folders=config["watch_folders"],
            supported_extensions=config["supported_extensions"]
        )
        logger.info("MCP handler initialized")
    except Exception as e:
        logger.error(f"Error initializing MCP handler: {e}")
        sys.exit(1)
    
    # Run the server
    uvicorn.run(app, host=config["host"], port=config["port"])

if __name__ == "__main__":
    main()
