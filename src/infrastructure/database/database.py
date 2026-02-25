import os
import aiomysql
from dotenv import load_dotenv

load_dotenv()

# Pool global — se inicializa una sola vez en el arranque
_pool: aiomysql.Pool | None = None


async def create_pool() -> aiomysql.Pool:
    """
    Crea el pool de conexiones async a MySQL.
    Se llama una sola vez desde dependencies.py al arrancar el servidor.
    """
    global _pool
    _pool = await aiomysql.create_pool(
        host     = os.getenv("DB_HOST", "localhost"),
        port     = int(os.getenv("DB_PORT", 3306)),
        user     = os.getenv("DB_USER", "root"),
        password = os.getenv("DB_PASSWORD", ""),
        db       = os.getenv("DB_NAME", "livepoll"),
        autocommit = False,
        minsize  = 2,
        maxsize  = 10,
        charset  = "utf8mb4",
    )
    print("[DB] Pool de conexiones MySQL creado ✓")
    return _pool


def get_pool() -> aiomysql.Pool:
    """Retorna el pool ya inicializado. Falla si no se llamó create_pool() antes."""
    if _pool is None:
        raise RuntimeError("El pool de base de datos no ha sido inicializado. "
                           "Llama a create_pool() primero.")
    return _pool


async def close_pool() -> None:
    """Cierra el pool al apagar el servidor."""
    global _pool
    if _pool:
        _pool.close()
        await _pool.wait_closed()
        _pool = None
        print("[DB] Pool de conexiones cerrado.")