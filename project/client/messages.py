from dataclasses import dataclass
from typing import Any

@dataclass
class Message:
    role: str = ""
    content: str = ""
    type: str = ""
    raw_content: Any = None

    def as_chat(self) -> str:
        return f"{self.role if self.role == 'assistant' else 'tool'}: {self.content}"

@dataclass   
class UserMessage(Message):
    role: str = "user"

@dataclass
class AssistantMessage(Message):
    role: str = "assistant"