import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from dotenv import load_dotenv
from src.infrastructure.database.database import create_pool, close_pool
from src.infrastructure.dependencies       import build_handler

load_dotenv()


def create_app() -> FastAPI:


    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await create_pool()
        handler = build_handler()

        app.state.handler = handler

        port = os.getenv("WS_PORT", "3000")
        print(f"LivePoll FastAPI corriendo en ws://localhost:{port}/ws")
        print(f"Docs disponibles en http://localhost:{port}/docs")
        print(f"Base de datos: {os.getenv('DB_NAME')}@{os.getenv('DB_HOST')}")
        print("   Esperando conexiones...\n")

        yield  

        await close_pool()
        print("\n[Server] Servidor detenido.")

    app = FastAPI(
        title       = "LivePoll API",
        description = "Encuestas en tiempo real con WebSockets",
        version     = "1.0.0",
        lifespan    = lifespan,
    )


    @app.get("/health", tags=["Status"])
    async def health_check():
        """Verifica que el servidor esté corriendo."""
        return {"status": "ok", "service": "LivePoll"}

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await app.state.handler.handle_connection(websocket)

    return app