import uuid
from src.domain.model.poll import Poll
from src.domain.port.poll_repository import IPollRepository


class CreatePollUseCase:

    def __init__(self, repository: IPollRepository) -> None:
        self._repository = repository

    async def execute(self, question: str, options: list[str]) -> Poll:
        # ── Validaciones de negocio ───────────────────────────────
        if not question or not question.strip():
            raise ValueError("La pregunta no puede estar vacía.")

        options = [o.strip() for o in options if o.strip()]
        if len(options) < 2:
            raise ValueError("Se necesitan al menos 2 opciones.")

        if len(options) > 6:
            raise ValueError("Máximo 6 opciones por encuesta.")

        # ── Crear entidad y persistir ─────────────────────────────
        poll_id = uuid.uuid4().hex[:6].upper()  # ej: "ABC123"
        poll    = Poll(id=poll_id, question=question, options=options)

        return await self._repository.save(poll)