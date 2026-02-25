import json
import asyncio

from fastapi import WebSocket, WebSocketDisconnect

from src.application.usecase.create_poll_usecase import CreatePollUseCase
from src.application.usecase.get_poll_usecase    import GetPollUseCase
from src.application.usecase.vote_usecase        import VoteUseCase
from src.infrastructure.websocket.message_parser import MessageParser


class WebSocketHandler:

    def __init__(
        self,
        create_poll_usecase: CreatePollUseCase,
        get_poll_usecase:    GetPollUseCase,
        vote_usecase:        VoteUseCase,
    ) -> None:
        self._create_poll = create_poll_usecase
        self._get_poll    = get_poll_usecase
        self._vote        = vote_usecase
        self._parser      = MessageParser()

        # Salas: { poll_id: set[WebSocket] }
        self._rooms: dict[str, set] = {}

    # ── Punto de entrada para cada conexión nueva ─────────────────

    async def handle_connection(self, websocket: WebSocket) -> None:
        await websocket.accept()
        print(f"[WS] Nueva conexión: {websocket.client}")

        poll_id_ref = {"value": None}

        try:
            while True:
                raw_message = await websocket.receive_text()
                await self._handle_message(websocket, raw_message, poll_id_ref)

        except WebSocketDisconnect:
            pass
        except Exception as e:
            print(f"[WS] Error inesperado: {e}")
        finally:
            self._leave_room(websocket, poll_id_ref["value"])
            print(f"[WS] Conexión cerrada: {websocket.client}")

    # ── Router de mensajes ────────────────────────────────────────

    async def _handle_message(self, websocket, raw_message: str, poll_id_ref: dict) -> None:
        try:
            data = self._parser.parse(raw_message)
        except ValueError as e:
            await self._send_error(websocket, str(e))
            return

        msg_type = data["type"]

        if msg_type == "CREATE_POLL":
            await self._handle_create_poll(websocket, data, poll_id_ref)
        elif msg_type == "JOIN_POLL":
            await self._handle_join_poll(websocket, data, poll_id_ref)
        elif msg_type == "VOTE":
            await self._handle_vote(websocket, data)

    # ── Handlers individuales ─────────────────────────────────────

    async def _handle_create_poll(self, websocket, data: dict, poll_id_ref: dict) -> None:
        try:
            poll = await self._create_poll.execute(
                question = data.get("question", ""),
                options  = data.get("options", []),
            )
            self._join_room(websocket, poll.id)
            poll_id_ref["value"] = poll.id

            await self._send(websocket, {
                "type":     "POLL_CREATED",
                "pollId":   poll.id,
                "question": poll.question,
                "options":  poll.options,
            })
            print(f"[Handler] Encuesta creada: {poll.id}")

        except (ValueError, RuntimeError) as e:
            await self._send_error(websocket, str(e))

    async def _handle_join_poll(self, websocket, data: dict, poll_id_ref: dict) -> None:
        try:
            poll = await self._get_poll.execute(poll_id=data.get("pollId", ""))
            self._join_room(websocket, poll.id)
            poll_id_ref["value"] = poll.id

            await self._send(websocket, {"type": "POLL_STATE", **poll.to_result()})
            print(f"[Handler] Cliente unido a sala: {poll.id}")

        except (ValueError, RuntimeError) as e:
            await self._send_error(websocket, str(e))

    async def _handle_vote(self, websocket, data: dict) -> None:
        try:
            poll_id      = data.get("pollId", "")
            option_index = data.get("optionIndex")

            if option_index is None:
                raise ValueError('Falta el campo "optionIndex".')

            poll = await self._vote.execute(
                poll_id=poll_id, option_index=int(option_index)
            )

            await self._broadcast_to_room(poll.id, {"type": "POLL_UPDATE", **poll.to_result()})
            print(f"[Handler] Voto registrado — sala: {poll.id}")

        except (ValueError, RuntimeError) as e:
            await self._send_error(websocket, str(e))

    # ── Gestión de salas ──────────────────────────────────────────

    def _join_room(self, websocket, poll_id: str) -> None:
        if poll_id not in self._rooms:
            self._rooms[poll_id] = set()
        self._rooms[poll_id].add(websocket)

    def _leave_room(self, websocket, poll_id: str | None) -> None:
        if poll_id and poll_id in self._rooms:
            self._rooms[poll_id].discard(websocket)
            if not self._rooms[poll_id]:
                del self._rooms[poll_id]

    async def _broadcast_to_room(self, poll_id: str, message: dict) -> None:
        room = self._rooms.get(poll_id, set())
        if not room:
            return
        json_msg = json.dumps(message)
        await asyncio.gather(
            *[client.send_text(json_msg) for client in room],
            return_exceptions=True,
        )

    async def _send(self, websocket, message: dict) -> None:
        await websocket.send_text(json.dumps(message))

    async def _send_error(self, websocket, error_message: str) -> None:
        await self._send(websocket, {"type": "ERROR", "message": error_message})