from ast import Str
from dataclasses import dataclass, field

@dataclass
class Symbol():
    name: Str
    score: float
    position: int = field(init=False)

    