"""
Token definitions for the Mus language lexer.
"""

from enum import Enum, auto

class TokenType(Enum):
    """Enum representing different token types in Mus language."""
    KEYWORD = auto()
    IDENTIFIER = auto()
    TYPE = auto()
    OPERATOR = auto()
    STRING = auto()
    NUMBER = auto()
    BOOLEAN = auto()
    SEPARATOR = auto()
    COMMENT = auto()
    UNKNOWN = auto()

class Token:
    """Class representing a token in the Mus language."""
    def __init__(self, type: TokenType, value: str, line: int):
        self.type = type
        self.value = value
        self.line = line

    def __repr__(self):
        return f"Token(type={self.type}, value='{self.value}', line={self.line})" 