"""
Unified server startup script that serves both API and web client
"""
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from api.config import settings
from api.endpoints import auth, references, documents, registers

# Create FastAPI app
app = FastAPI(
    title="Construction Time Management System",
    description="REST API and Web Client for construction time management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(references.router, prefix=settings.API_PREFIX)
app.include_router(documents.router, prefix=settings.API_PREFIX)
app.include_router(registers.router, prefix=settings.API_PREFIX)

# API health check
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# Check if web client dist exists
web_dist_path = Path(__file__).parent / "web-client" / "dist"

if web_dist_path.exists():
    # Mount static files
    app.mount("/assets", StaticFiles(directory=str(web_dist_path / "assets")), name="assets")
    
    # Serve index.html for all non-API routes (SPA routing)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve the SPA for all non-API routes"""
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("redoc"):
            return {"error": "Not found"}
        
        # Serve static files if they exist
        file_path = web_dist_path / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        
        # Otherwise serve index.html (SPA routing)
        return FileResponse(web_dist_path / "index.html")
else:
    @app.get("/")
    async def root():
        """Root endpoint when web client is not built"""
        return {
            "message": "Construction Time Management API",
            "version": "1.0.0",
            "docs": "/docs",
            "note": "Web client not built. Run build_web.bat to build the client."
        }

if __name__ == "__main__":
    print("=" * 50)
    print("Construction Time Management System")
    print("=" * 50)
    print(f"API Server: http://localhost:8000")
    print(f"API Docs: http://localhost:8000/docs")
    if web_dist_path.exists():
        print(f"Web Client: http://localhost:8000")
    else:
        print("Web Client: Not built (run build_web.bat)")
    print("=" * 50)
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
