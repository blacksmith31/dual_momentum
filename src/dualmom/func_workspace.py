from ast import Str
from dataclasses import dataclass, field

@dataclass
class Symbol():
    name: Str
    score: float
    position: int = field(init=False)

    
class Strategy:
    # def get_history()

    # def apply_indicator()

    # def get_score()
    pass