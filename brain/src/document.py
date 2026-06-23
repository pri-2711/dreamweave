from dataclasses import dataclass


@dataclass
class Document:
    id: int
    source: str
    filename: str
    content: str
    timestamp: str