from src.infrastructure.database.mysql.mysql_poll_repository import MySQLPollRepository
from src.application.usecase.create_poll_usecase              import CreatePollUseCase
from src.application.usecase.get_poll_usecase                 import GetPollUseCase
from src.application.usecase.vote_usecase                     import VoteUseCase
from src.infrastructure.websocket.websocket_handler           import WebSocketHandler


def build_handler() -> WebSocketHandler:
  
    repository = MySQLPollRepository()

    create_poll_usecase = CreatePollUseCase(repository)
    get_poll_usecase    = GetPollUseCase(repository)
    vote_usecase        = VoteUseCase(repository)

    handler = WebSocketHandler(
        create_poll_usecase = create_poll_usecase,
        get_poll_usecase    = get_poll_usecase,
        vote_usecase        = vote_usecase,
    )

    return handler