from dataclasses import dataclass, field

@dataclass
class Symbol():
    name: str
    score: float
    position: int = field(init=False, repr=False)

    