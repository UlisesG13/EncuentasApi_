from dataclasses import dataclass, field
from datetime import datetime
@dataclass

class Poll:
    id: str
    question: str
    options: list[str]
    votes: list[int] = field(default_factory=list)
    active: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.votes:
            self.votes = [0] * len(self.options)

    def add_vote(self, option_index: int) -> None:
        """Registra un voto. Lanza error si el índice es inválido."""
        if option_index < 0 or option_index >= len(self.options):
            raise ValueError(f"Opción inválida: {option_index}. "
                             f"La encuesta tiene {len(self.options)} opciones.")
        if not self.active:
            raise ValueError("La encuesta ya no está activa.")
        self.votes[option_index] += 1

    def get_total_votes(self) -> int:
        return sum(self.votes)

    def get_percentages(self) -> list[int]:
        total = self.get_total_votes()
        if total == 0:
            return [0] * len(self.options)
        return [round((v / total) * 100) for v in self.votes]

    def to_result(self) -> dict:
        """Serializa el estado actual para enviar al cliente WebSocket."""
        return {
            "pollId":      self.id,
            "question":    self.question,
            "options":     self.options,
            "votes":       self.votes,
            "total":       self.get_total_votes(),
            "percentages": self.get_percentages(),
        }