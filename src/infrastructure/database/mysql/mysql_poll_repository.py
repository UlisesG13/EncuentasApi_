import aiomysql
from src.domain.model.poll import Poll
from src.domain.port.poll_repository import IPollRepository
from src.infrastructure.database.database import get_pool


class MySQLPollRepository(IPollRepository):

    async def save(self, poll: Poll) -> Poll:
        pool = get_pool()
        print(f"[MySQLRepo] Guardando encuesta: {poll.id}")

        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await conn.begin()

                    await cur.execute(
                        "INSERT INTO polls (id, question, active) VALUES (%s, %s, %s)",
                        (poll.id, poll.question, True)
                    )
                    print(f"[MySQLRepo] Poll insertado en tabla polls: {poll.id}")

                    for i, option_text in enumerate(poll.options):
                        await cur.execute(
                            "INSERT INTO options (poll_id, text, position) VALUES (%s, %s, %s)",
                            (poll.id, option_text, i)
                        )
                        print(f"[MySQLRepo] Opción {i} insertada: {option_text}")

                    await conn.commit()
                    print(f"[MySQLRepo] Encuesta guardada exitosamente: {poll.id}")

                except Exception as e:
                    await conn.rollback()
                    print(f"[MySQLRepo] Error al guardar encuesta: {type(e).__name__}: {e}")
                    raise RuntimeError(f"Error guardando encuesta: {e}") from e

        print(f"[MySQLRepo] Intentando recuperar encuesta guardada: {poll.id}")
        retrieved_poll = await self.find_by_id(poll.id)
        if retrieved_poll is None:
            print(f"[MySQLRepo] ADVERTENCIA: No se pudo recuperar la encuesta {poll.id}")
            print(f"[MySQLRepo] Retornando objeto Poll original como fallback")
            return poll
        
        print(f"[MySQLRepo] Encuesta recuperada exitosamente: {retrieved_poll.id}")
        return retrieved_poll

    async def find_by_id(self, poll_id: str) -> Poll | None:
        pool = get_pool()

        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:

                await cur.execute(
                    "SELECT id, question, active FROM polls WHERE id = %s",
                    (poll_id,)
                )
                poll_row = await cur.fetchone()

                if not poll_row:
                    return None

                await cur.execute(
                    "SELECT id, text, position FROM options "
                    "WHERE poll_id = %s ORDER BY position",
                    (poll_id,)
                )
                option_rows = await cur.fetchall()

                await cur.execute(
                    """
                    SELECT o.position, COUNT(v.id) AS vote_count
                    FROM options o
                    LEFT JOIN votes v ON v.option_id = o.id
                    WHERE o.poll_id = %s
                    GROUP BY o.id, o.position
                    ORDER BY o.position
                    """,
                    (poll_id,)
                )
                vote_rows = await cur.fetchall()

        options = [row["text"] for row in option_rows]
        votes   = [0] * len(options)

        for row in vote_rows:
            votes[row["position"]] = int(row["vote_count"])

        return Poll(
            id       = poll_row["id"],
            question = poll_row["question"],
            options  = options,
            votes    = votes,
            active   = bool(poll_row["active"]),
        )

    async def register_vote(self, poll_id: str, option_index: int) -> Poll:
        pool = get_pool()
        print(f"[MySQLRepo] Intentando registrar voto — encuesta: {poll_id}, opción: {option_index}")

        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                try:
                    await conn.begin()

                    await cur.execute(
                        "SELECT id FROM options WHERE poll_id = %s AND position = %s",
                        (poll_id, option_index)
                    )
                    option_row = await cur.fetchone()

                    if not option_row:
                        print(f"[MySQLRepo] ERROR: Opción {option_index} no existe en encuesta {poll_id}")
                        raise ValueError(
                            f"Opción {option_index} no existe en encuesta {poll_id}"
                        )

                    print(f"[MySQLRepo] Insertando voto para opción: {option_row['id']}")
                    await cur.execute(
                        "INSERT INTO votes (poll_id, option_id) VALUES (%s, %s)",
                        (poll_id, option_row["id"])
                    )

                    await conn.commit()
                    print(f"[MySQLRepo] Voto registrado exitosamente — encuesta: {poll_id}, opción: {option_index}")

                except Exception as e:
                    await conn.rollback()
                    print(f"[MySQLRepo] Error registrando voto: {type(e).__name__}: {e}")
                    raise RuntimeError(f"Error registrando voto: {e}") from e

        retrieved_poll = await self.find_by_id(poll_id)
        if retrieved_poll is None:
            print(f"[MySQLRepo] ADVERTENCIA: No se pudo recuperar la encuesta {poll_id} después de votar")
            raise RuntimeError(f"No se pudo recuperar la encuesta {poll_id} después de registrar el voto")
        
        return retrieved_poll

    async def find_all(self) -> list[Poll]:
        """Obtiene todas las encuestas disponibles."""
        pool = get_pool()

        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("SELECT id, question, active FROM polls ORDER BY id DESC")
                poll_rows = await cur.fetchall()

                if not poll_rows:
                    return []

                polls_list = []
                for poll_row in poll_rows:
                    poll_id = poll_row["id"]

                    await cur.execute(
                        "SELECT id, text, position FROM options "
                        "WHERE poll_id = %s ORDER BY position",
                        (poll_id,)
                    )
                    option_rows = await cur.fetchall()

                    await cur.execute(
                        """
                        SELECT o.position, COUNT(v.id) AS vote_count
                        FROM options o
                        LEFT JOIN votes v ON v.option_id = o.id
                        WHERE o.poll_id = %s
                        GROUP BY o.id, o.position
                        ORDER BY o.position
                        """,
                        (poll_id,)
                    )
                    vote_rows = await cur.fetchall()

                    options = [row["text"] for row in option_rows]
                    votes = [0] * len(options)

                    for row in vote_rows:
                        votes[row["position"]] = int(row["vote_count"])

                    poll = Poll(
                        id=poll_row["id"],
                        question=poll_row["question"],
                        options=options,
                        votes=votes,
                        active=bool(poll_row["active"]),
                    )
                    polls_list.append(poll)

                return polls_list