from src.domain.model.poll import Poll
from src.domain.port.poll_repository import IPollRepository


class GetPollUseCase:
    """
    Caso de uso: Obtener el estado actual de una encuesta.
    Se usa cuando un cliente se une a una sala existente.
    """

    def __init__(self, repository: IPollRepository) -> None:
        self._repository = repository

    async def execute(self, poll_id: str) -> Poll:
        if not poll_id or not poll_id.strip():
            raise ValueError("El código de sala no puede estar vacío.")

        poll = await self._repository.find_by_id(poll_id.upper())

        if poll is None:
            raise ValueError(f"Encuesta '{poll_id}' no encontrada.")

        return poll