from src.domain.model.poll import Poll
from src.domain.port.poll_repository import IPollRepository


class VoteUseCase:

    def __init__(self, repository: IPollRepository) -> None:
        self._repository = repository

    async def execute(self, poll_id: str, option_index: int) -> Poll:
        poll = await self._repository.find_by_id(poll_id.upper())

        if poll is None:
            raise ValueError(f"Encuesta '{poll_id}' no encontrada.")

        if not poll.active:
            raise ValueError("La encuesta ya no está activa.")

        if option_index < 0 or option_index >= len(poll.options):
            raise ValueError(
                f"Opción inválida: {option_index}. "
                f"La encuesta tiene {len(poll.options)} opciones (0 a {len(poll.options) - 1})."
            )
        return await self._repository.register_vote(poll_id.upper(), option_index)