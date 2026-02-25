import os
import uvicorn
from dotenv import load_dotenv
from src.infrastructure.server import create_app

load_dotenv()

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host    = "0.0.0.0",
        port    = int(os.getenv("WS_PORT", 8000)),
        reload  = True, 
        log_level = "info",
    )
