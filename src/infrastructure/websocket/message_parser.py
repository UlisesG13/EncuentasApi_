import json

class MessageParser:
    VALID_TYPES = {"CREATE_POLL", "JOIN_POLL", "VOTE"}

    def parse(self, raw_message: str) -> dict:
        try:
            data = json.loads(raw_message)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON inválido: {e}")

        if not isinstance(data, dict):
            raise ValueError("El mensaje debe ser un objeto JSON.")

        msg_type = data.get("type")
        if not msg_type:
            raise ValueError('El mensaje debe incluir el campo "type".')

        if msg_type not in self.VALID_TYPES:
            raise ValueError(
                f'Tipo desconocido: "{msg_type}". '
                f'Tipos válidos: {", ".join(self.VALID_TYPES)}'
            )

        return data