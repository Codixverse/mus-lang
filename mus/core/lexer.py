"""
Lexer for the Mus Programming Language.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Iterator, List, Optional

class TokenType(Enum):
    """Token types in the Mus language."""
    # Keywords
    CLASS = auto()
    FUN = auto()
    VAR = auto()
    IF = auto()
    ELSE = auto()
    ELIF = auto()
    WHILE = auto()
    FOR = auto()
    IN = auto()
    RETURN = auto()
    THIS = auto()
    SUPER = auto()
    EXTENDS = auto()
    NEW = auto()
    
    # Literals
    INTEGER = auto()
    STRING = auto()
    BOOLEAN = auto()
    
    # Operators
    PLUS = auto()
    MINUS = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    MODULO = auto()
    ASSIGN = auto()
    EQUALS = auto()
    NOT_EQUALS = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    
    # Delimiters
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    LEFT_BRACE = auto()
    RIGHT_BRACE = auto()
    LEFT_BRACKET = auto()
    RIGHT_BRACKET = auto()
    COMMA = auto()
    DOT = auto()
    ARROW = auto()  # =>
    SEMICOLON = auto()  # ;
    
    # Other
    IDENTIFIER = auto()
    COMMENT = auto()
    EOF = auto()

@dataclass(frozen=True)
class Token:
    """Token in the Mus language."""
    type: TokenType
    lexeme: str
    literal: Optional[object]
    line: int
    column: int

    def __str__(self) -> str:
        if self.literal is not None:
            return f"{self.type.name}({self.lexeme}, {self.literal})"
        return f"{self.type.name}({self.lexeme})"

class LexerError(Exception):
    """Exception raised for lexer errors."""
    def __init__(self, message: str, line: int, column: int):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"{message} at line {line}, column {column}")

class Lexer:
    """Lexer for the Mus language."""
    
    KEYWORDS = {
        'class': TokenType.CLASS,
        'fun': TokenType.FUN,
        'var': TokenType.VAR,
        'if': TokenType.IF,
        'else': TokenType.ELSE,
        'elif': TokenType.ELIF,
        'while': TokenType.WHILE,
        'for': TokenType.FOR,
        'in': TokenType.IN,
        'return': TokenType.RETURN,
        'this': TokenType.THIS,
        'super': TokenType.SUPER,
        'extends': TokenType.EXTENDS,
        'new': TokenType.NEW,
        'true': TokenType.BOOLEAN,
        'false': TokenType.BOOLEAN,
    }

    def __init__(self, source: str):
        self.source = source
        self.tokens: List[Token] = []
        self.start = 0
        self.current = 0
        self.line = 1
        self.column = 1

    def scan_tokens(self) -> List[Token]:
        """Scan the source code and return a list of tokens."""
        while not self.is_at_end():
            self.start = self.current
            self.scan_token()

        self.tokens.append(Token(TokenType.EOF, "", None, self.line, self.column))
        return self.tokens

    def scan_token(self) -> None:
        """Scan a single token."""
        c = self.advance()
        
        match c:
            # Single-character tokens
            case '(': self.add_token(TokenType.LEFT_PAREN)
            case ')': self.add_token(TokenType.RIGHT_PAREN)
            case '{': self.add_token(TokenType.LEFT_BRACE)
            case '}': self.add_token(TokenType.RIGHT_BRACE)
            case '[': self.add_token(TokenType.LEFT_BRACKET)
            case ']': self.add_token(TokenType.RIGHT_BRACKET)
            case ',': self.add_token(TokenType.COMMA)
            case '.': self.add_token(TokenType.DOT)
            case '+': self.add_token(TokenType.PLUS)
            case '*': self.add_token(TokenType.MULTIPLY)
            case '%': self.add_token(TokenType.MODULO)
            case ';': self.add_token(TokenType.SEMICOLON)
            
            # Two-character tokens
            case '=':
                if self.match('='): self.add_token(TokenType.EQUALS)
                elif self.match('>'): self.add_token(TokenType.ARROW)
                else: self.add_token(TokenType.ASSIGN)
            case '!':
                if self.match('='): self.add_token(TokenType.NOT_EQUALS)
                else: self.add_token(TokenType.NOT)
            case '>':
                if self.match('='): self.add_token(TokenType.GREATER_EQUAL)
                else: self.add_token(TokenType.GREATER)
            case '<':
                if self.match('='): self.add_token(TokenType.LESS_EQUAL)
                else: self.add_token(TokenType.LESS)
            case '-':
                if self.match('-'):
                    # Comment goes until end of line
                    while self.peek() != '\n' and not self.is_at_end():
                        self.advance()
                else:
                    self.add_token(TokenType.MINUS)
            case '/':
                if self.match('/'):
                    # Comment goes until end of line
                    while self.peek() != '\n' and not self.is_at_end():
                        self.advance()
                else:
                    self.add_token(TokenType.DIVIDE)
            
            # Whitespace
            case ' ' | '\r' | '\t':
                pass
            case '\n':
                self.line += 1
                self.column = 1
            
            # String literals
            case '"': self.string()
            
            # Default case for other characters
            case _:
                if c.isdigit():
                    self.number()
                elif c.isalpha() or c == '_':
                    self.identifier()
                else:
                    raise LexerError(f"Unexpected character: {c}", self.line, self.column)

    def identifier(self) -> None:
        """Scan an identifier."""
        while (c := self.peek()).isalnum() or c == '_':
            self.advance()

        text = self.source[self.start:self.current]
        token_type = self.KEYWORDS.get(text, TokenType.IDENTIFIER)
        literal = None
        
        if token_type == TokenType.BOOLEAN:
            literal = text == 'true'
            
        self.add_token(token_type, literal)

    def number(self) -> None:
        """Scan a number."""
        while self.peek().isdigit():
            self.advance()

        # Look for a decimal part
        if self.peek() == '.' and self.peek_next().isdigit():
            # Consume the "."
            self.advance()

            while self.peek().isdigit():
                self.advance()

        value = int(self.source[self.start:self.current])
        self.add_token(TokenType.INTEGER, value)

    def string(self) -> None:
        """Scan a string."""
        while self.peek() != '"' and not self.is_at_end():
            if self.peek() == '\n':
                self.line += 1
                self.column = 1
            self.advance()

        if self.is_at_end():
            raise LexerError("Unterminated string", self.line, self.column)

        # The closing "
        self.advance()

        # Trim the surrounding quotes
        value = self.source[self.start + 1:self.current - 1]
        self.add_token(TokenType.STRING, value)

    def match(self, expected: str) -> bool:
        """Check if the current character matches the expected one."""
        if self.is_at_end():
            return False
        if self.source[self.current] != expected:
            return False

        self.current += 1
        self.column += 1
        return True

    def peek(self) -> str:
        """Look at the current character without consuming it."""
        if self.is_at_end():
            return '\0'
        return self.source[self.current]

    def peek_next(self) -> str:
        """Look at the next character without consuming it."""
        if self.current + 1 >= len(self.source):
            return '\0'
        return self.source[self.current + 1]

    def is_at_end(self) -> bool:
        """Check if we've reached the end of the source code."""
        return self.current >= len(self.source)

    def advance(self) -> str:
        """Consume and return the current character."""
        c = self.source[self.current]
        self.current += 1
        self.column += 1
        return c

    def add_token(self, type_: TokenType, literal: Optional[object] = None) -> None:
        """Add a token to the list."""
        text = self.source[self.start:self.current]
        self.tokens.append(Token(type_, text, literal, self.line, self.column - len(text))) 