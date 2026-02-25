import aiomysql
from src.domain.model.poll import Poll
from src.domain.port.poll_repository import IPollRepository
from src.infrastructure.database.database import get_pool


class MySQLPollRepository(IPollRepository):

    async def save(self, poll: Poll) -> Poll:
        pool = get_pool()

        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await conn.begin()

                    await cur.execute(
                        "INSERT INTO polls (id, question, active) VALUES (%s, %s, %s)",
                        (poll.id, poll.question, True)
                    )

                    for i, option_text in enumerate(poll.options):
                        await cur.execute(
                            "INSERT INTO options (poll_id, text, position) VALUES (%s, %s, %s)",
                            (poll.id, option_text, i)
                        )

                    await conn.commit()
                    print(f"[MySQLRepo] Encuesta guardada: {poll.id}")

                except Exception as e:
                    await conn.rollback()
                    raise RuntimeError(f"Error guardando encuesta: {e}") from e

        return await self.find_by_id(poll.id)

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
                        raise ValueError(
                            f"Opción {option_index} no existe en encuesta {poll_id}"
                        )

                    await cur.execute(
                        "INSERT INTO votes (poll_id, option_id) VALUES (%s, %s)",
                        (poll_id, option_row["id"])
                    )

                    await conn.commit()
                    print(f"[MySQLRepo] Voto registrado — encuesta: {poll_id}, opción: {option_index}")

                except Exception as e:
                    await conn.rollback()
                    raise RuntimeError(f"Error registrando voto: {e}") from e

        return await self.find_by_id(poll_id)