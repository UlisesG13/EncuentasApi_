from abc import ABC, abstractmethod
from src.domain.model.poll import Poll


class IPollRepository(ABC):
   

    @abstractmethod
    async def save(self, poll: Poll) -> Poll:
        """Persiste una encuesta nueva y retorna la entidad guardada."""
        ...

    @abstractmethod
    async def find_by_id(self, poll_id: str) -> Poll | None:
        """Busca una encuesta por su código. Retorna None si no existe."""
        ...

    @abstractmethod
    async def register_vote(self, poll_id: str, option_index: int) -> Poll:
        """Registra un voto y retorna la encuesta con conteos actualizados."""
        ...
