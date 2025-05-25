"""
Lexer for the Mus language.
"""

import re
from typing import List, Iterator
from .tokens import Token, TokenType
from .exceptions import ParserError

class Lexer:
    """Lexer for tokenizing Mus source code."""
    
    KEYWORDS = {
        'var', 'fun', 'if', 'else', 'while', 'for', 'return',
        'class', 'extends', 'new', 'this', 'out', 'debug'
    }
    
    TYPES = {
        'string', 'integer', 'bool', 'array'
    }
    
    OPERATORS = {
        '+', '-', '*', '/', '%', '=', '==', '!=', '<', '>', '<=', '>=',
        '&&', '||', '!', '.', '=>'
    }
    
    def __init__(self, source: str):
        self.source = source
        self.position = 0
        self.line = 1
        self.current_char = self.source[0] if source else None
    
    def advance(self):
        """Move to the next character."""
        self.position += 1
        if self.position < len(self.source):
            self.current_char = self.source[self.position]
        else:
            self.current_char = None
    
    def skip_whitespace(self):
        """Skip whitespace characters."""
        while self.current_char and self.current_char.isspace():
            if self.current_char == '\n':
                self.line += 1
            self.advance()
    
    def skip_comment(self):
        """Skip comment characters."""
        while self.current_char and self.current_char != '\n':
            self.advance()
    
    def identifier(self) -> Token:
        """Process an identifier or keyword."""
        result = ''
        while self.current_char and (self.current_char.isalnum() or self.current_char == '_'):
            result += self.current_char
            self.advance()
        
        if result in self.KEYWORDS:
            return Token(TokenType.KEYWORD, result, self.line)
        elif result in self.TYPES:
            return Token(TokenType.TYPE, result, self.line)
        else:
            return Token(TokenType.IDENTIFIER, result, self.line)
    
    def number(self) -> Token:
        """Process a number."""
        result = ''
        while self.current_char and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        return Token(TokenType.NUMBER, result, self.line)
    
    def string(self) -> Token:
        """Process a string literal."""
        result = ''
        self.advance()  # Skip opening quote
        while self.current_char and self.current_char != '"':
            if self.current_char == '\\':
                self.advance()
                if self.current_char in {'"', 'n', 't', '\\'}:
                    result += '\\' + self.current_char
            else:
                result += self.current_char
            self.advance()
        self.advance()  # Skip closing quote
        return Token(TokenType.STRING, result, self.line)
    
    def operator(self) -> Token:
        """Process an operator."""
        result = self.current_char
        self.advance()
        if self.current_char and result + self.current_char in self.OPERATORS:
            result += self.current_char
            self.advance()
        return Token(TokenType.OPERATOR, result, self.line)
    
    def get_next_token(self) -> Token:
        """Get the next token from the source code."""
        while self.current_char:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue
            
            if self.current_char == '-' and self.peek() == '-':
                self.skip_comment()
                continue
            
            if self.current_char.isalpha() or self.current_char == '_':
                return self.identifier()
            
            if self.current_char.isdigit():
                return self.number()
            
            if self.current_char == '"':
                return self.string()
            
            if self.current_char in self.OPERATORS:
                return self.operator()
            
            if self.current_char in {'(', ')', '{', '}', '[', ']', ',', ';'}:
                token = Token(TokenType.SEPARATOR, self.current_char, self.line)
                self.advance()
                return token
            
            raise ParserError(f"Invalid character: {self.current_char}", self.line)
        
        return Token(TokenType.UNKNOWN, '', self.line)
    
    def peek(self) -> str:
        """Look at the next character without consuming it."""
        peek_pos = self.position + 1
        if peek_pos < len(self.source):
            return self.source[peek_pos]
        return None
    
    def tokenize(self) -> List[Token]:
        """Tokenize the entire source code."""
        tokens = []
        while True:
            token = self.get_next_token()
            if token.type == TokenType.UNKNOWN:
                break
            tokens.append(token)
        return tokens 