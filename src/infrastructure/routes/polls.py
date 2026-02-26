import logging
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class CreatePollRequest(BaseModel):
    question: str
    options: list[str]


class VoteRequest(BaseModel):
    optionIndex: int


class PollResponse(BaseModel):
    pollId: str
    question: str
    options: list[str]
    votes: list[int]
    total: int
    percentages: list[int]


def create_polls_router():
    router = APIRouter(prefix="/api/polls", tags=["Polls"])

    @router.get("", response_model=list[PollResponse])
    async def list_polls(req: Request):

        try:
            handler = req.app.state.handler
            repository = handler._create_poll._repository
            polls = await repository.find_all()
            return [poll.to_result() for poll in polls]
        except Exception as e:
            logger.error(f"[ListPolls] Error inesperado: {type(e).__name__}: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error al listar encuestas: {str(e)}")

    @router.post("", response_model=PollResponse)
    async def create_poll(request: CreatePollRequest, req: Request):
        try:
            handler = req.app.state.handler
            poll = await handler._create_poll.execute(
                question=request.question,
                options=request.options
            )
            
            poll_dict = poll.to_result()
            logger.info(f"[CreatePoll] Encuesta creada: {poll_dict}")
            
            return poll_dict
            
        except ValueError as e:
            logger.error(f"[CreatePoll] ValueError: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"[CreatePoll] Error inesperado: {type(e).__name__}: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error al crear encuesta: {str(e)}")

    @router.post("/{poll_id}/vote", response_model=PollResponse)
    async def vote_poll(poll_id: str, request: VoteRequest, req: Request):
        """
        Registra un voto en una encuesta.
        
        - **poll_id**: ID de la encuesta
        - **optionIndex**: Índice de la opción elegida (0, 1, 2, ...)
        
        Retorna el estado actualizado de la encuesta.
        """
        try:
            handler = req.app.state.handler
            poll = await handler._vote.execute(
                poll_id=poll_id,
                option_index=request.optionIndex
            )
            poll_dict = poll.to_result()
            logger.info(f"[Vote] Voto registrado en encuesta: {poll_id}")
            return poll_dict
            
        except ValueError as e:
            logger.error(f"[Vote] ValueError: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"[Vote] Error inesperado: {type(e).__name__}: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error al votar: {str(e)}")

    @router.get("/{poll_id}", response_model=PollResponse)
    async def get_poll(poll_id: str, req: Request):
        """
        Obtiene el estado actual de una encuesta.
        
        - **poll_id**: ID de la encuesta
        
        Retorna la pregunta, opciones y votos actuales.
        """
        try:
            handler = req.app.state.handler
            poll = await handler._get_poll.execute(poll_id=poll_id)
            poll_dict = poll.to_result()
            logger.info(f"[GetPoll] Obteniendo encuesta: {poll_id}")
            return poll_dict
            
        except ValueError as e:
            logger.error(f"[GetPoll] ValueError: {str(e)}")
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"[GetPoll] Error inesperado: {type(e).__name__}: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error al obtener encuesta: {str(e)}")

    return router
