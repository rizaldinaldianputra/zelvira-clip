from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseAgent(ABC):
    """
    Base class for all AI Clipper pipeline agents.
    Each agent has a single responsibility, validated Pydantic I/O,
    and structured error handling.
    """
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        pass
