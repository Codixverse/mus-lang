"""
Parser for the Mus Programming Language.
"""

from dataclasses import dataclass
from typing import List, Optional, Union, Any
from .lexer import Token, TokenType
from .types import (
    MusType, MusInt, MusString, MusBool, MusArray,
    MusFunction, MusClass, MusObject, Environment
)

class ParserError(Exception):
    """Exception raised for parser errors."""
    def __init__(self, message: str, token: Token):
        self.message = message
        self.token = token
        super().__init__(f"{message} at line {token.line}, column {token.column}")

@dataclass(frozen=True)
class Expression:
    """Base class for expressions."""
    pass

@dataclass(frozen=True)
class Literal(Expression):
    """Literal expression (numbers, strings, booleans)."""
    value: Union[int, str, bool]
    token: Token

@dataclass(frozen=True)
class Variable(Expression):
    """Variable reference expression."""
    name: str
    token: Token

    def __hash__(self) -> int:
        return hash((self.name, self.token))

@dataclass(frozen=True)
class This(Expression):
    """'this' keyword expression."""
    token: Token

    def __hash__(self) -> int:
        return hash(self.token)

@dataclass(frozen=True)
class Super(Expression):
    """'super' keyword expression."""
    method: str
    token: Token

    def __hash__(self) -> int:
        return hash((self.method, self.token))

@dataclass(frozen=True)
class Binary(Expression):
    """Binary operation expression."""
    left: Expression
    operator: Token
    right: Expression

    def __hash__(self) -> int:
        return hash((self.left, self.operator, self.right))

@dataclass(frozen=True)
class Unary(Expression):
    """Unary operation expression."""
    operator: Token
    right: Expression

    def __hash__(self) -> int:
        return hash((self.operator, self.right))

@dataclass(frozen=True)
class Call(Expression):
    """Function/method call expression."""
    callee: Expression
    arguments: List[Expression]
    token: Token

    def __hash__(self) -> int:
        return hash((self.callee, tuple(self.arguments), self.token))

@dataclass(frozen=True)
class Get(Expression):
    """Property access expression."""
    object: Expression
    name: str
    token: Token

    def __hash__(self) -> int:
        return hash((self.object, self.name, self.token))

@dataclass(frozen=True)
class Set(Expression):
    """Property assignment expression."""
    object: Expression
    name: str
    value: Expression
    token: Token

    def __hash__(self) -> int:
        return hash((self.object, self.name, self.value, self.token))

@dataclass
class Statement:
    """Base class for statements."""
    pass

@dataclass
class ExpressionStmt(Statement):
    """Expression statement."""
    expression: Expression

@dataclass
class VarDeclaration(Statement):
    """Variable declaration statement."""
    name: str
    type_name: str
    initializer: Optional[Expression]
    token: Token

@dataclass
class FunctionDeclaration(Statement):
    """Function declaration statement."""
    name: str
    params: List[tuple[str, str]]
    body: List[Statement]
    token: Token

@dataclass
class ClassDeclaration(Statement):
    """Class declaration statement."""
    name: str
    superclass: Optional[str]
    fields: List[VarDeclaration]
    methods: List[FunctionDeclaration]
    token: Token

@dataclass
class Block(Statement):
    """Block statement."""
    statements: List[Statement]

@dataclass
class If(Statement):
    """If statement."""
    condition: Expression
    then_branch: Statement
    else_branch: Optional[Statement]

@dataclass
class While(Statement):
    """While statement."""
    condition: Expression
    body: Statement

@dataclass
class For(Statement):
    """For statement."""
    iterator: str
    iterable: Expression
    body: Statement

@dataclass
class Return(Statement):
    """Return statement."""
    value: Optional[Expression]
    token: Token

class Parser:
    """Parser for the Mus language."""
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0

    def parse(self) -> List[Statement]:
        """Parse the tokens into an AST."""
        statements = []
        while not self.is_at_end():
            statements.append(self.declaration())
        return statements

    def declaration(self) -> Statement:
        """Parse a declaration."""
        try:
            if self.match(TokenType.CLASS):
                return self.class_declaration()
            if self.match(TokenType.FUN):
                return self.function_declaration()
            if self.match(TokenType.VAR):
                return self.var_declaration()
            return self.statement()
        except ParserError as error:
            self.synchronize()
            return ExpressionStmt(Literal(None, error.token))

    def class_declaration(self) -> ClassDeclaration:
        """Parse a class declaration."""
        name_token = self.consume(TokenType.IDENTIFIER, "Expected class name.")
        
        # Check for inheritance
        superclass = None
        if self.match(TokenType.EXTENDS):
            superclass_token = self.consume(TokenType.IDENTIFIER, "Expected superclass name.")
            superclass = superclass_token.lexeme
        
        self.consume(TokenType.LEFT_BRACE, "Expected '{' before class body.")
        
        fields = []
        methods = []
        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            if self.match(TokenType.VAR):
                fields.append(self.var_declaration())
            elif self.match(TokenType.FUN):
                methods.append(self.function_declaration())
            else:
                raise ParserError("Expected field or method declaration.", self.peek())
        
        self.consume(TokenType.RIGHT_BRACE, "Expected '}' after class body.")
        
        return ClassDeclaration(name_token.lexeme, superclass, fields, methods, name_token)

    def function_declaration(self) -> FunctionDeclaration:
        """Parse a function declaration."""
        name_token = self.consume(TokenType.IDENTIFIER, "Expected function name.")
        
        self.consume(TokenType.LEFT_PAREN, "Expected '(' after function name.")
        parameters = []
        
        if not self.check(TokenType.RIGHT_PAREN):
            while True:
                param_name = self.consume(TokenType.IDENTIFIER, "Expected parameter name.").lexeme
                self.consume(TokenType.ARROW, "Expected '=>' after parameter name.")
                param_type = self.consume(TokenType.IDENTIFIER, "Expected parameter type.").lexeme
                parameters.append((param_name, param_type))
                
                if not self.match(TokenType.COMMA):
                    break
        
        self.consume(TokenType.RIGHT_PAREN, "Expected ')' after parameters.")
        self.consume(TokenType.LEFT_BRACE, "Expected '{' before function body.")
        
        body = []
        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            body.append(self.declaration())
        
        self.consume(TokenType.RIGHT_BRACE, "Expected '}' after function body.")
        
        return FunctionDeclaration(name_token.lexeme, parameters, body, name_token)

    def var_declaration(self) -> VarDeclaration:
        """Parse a variable declaration."""
        name_token = self.consume(TokenType.IDENTIFIER, "Expected variable name.")
        
        self.consume(TokenType.ARROW, "Expected '=>' after variable name.")
        type_token = self.consume(TokenType.IDENTIFIER, "Expected variable type.")
        
        initializer = None
        if self.match(TokenType.ASSIGN):
            initializer = self.expression()
        
        return VarDeclaration(name_token.lexeme, type_token.lexeme, initializer, name_token)

    def statement(self) -> Statement:
        """Parse a statement."""
        if self.match(TokenType.IF):
            return self.if_statement()
        if self.match(TokenType.WHILE):
            return self.while_statement()
        if self.match(TokenType.FOR):
            return self.for_statement()
        if self.match(TokenType.RETURN):
            return self.return_statement()
        if self.match(TokenType.LEFT_BRACE):
            return Block(self.block())
        return self.expression_statement()

    def if_statement(self) -> If:
        """Parse an if statement."""
        self.consume(TokenType.LEFT_PAREN, "Expected '(' after 'if'.")
        condition = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expected ')' after condition.")
        
        then_branch = self.statement()
        else_branch = None
        
        if self.match(TokenType.ELSE):
            else_branch = self.statement()
        
        return If(condition, then_branch, else_branch)

    def while_statement(self) -> While:
        """Parse a while statement."""
        self.consume(TokenType.LEFT_PAREN, "Expected '(' after 'while'.")
        condition = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expected ')' after condition.")
        body = self.statement()
        
        return While(condition, body)

    def for_statement(self) -> For:
        """Parse a for statement."""
        self.consume(TokenType.LEFT_PAREN, "Expected '(' after 'for'.")
        
        # Parse initializer
        if self.match(TokenType.VAR):
            iterator = self.consume(TokenType.IDENTIFIER, "Expected iterator variable name.").lexeme
        else:
            iterator = self.consume(TokenType.IDENTIFIER, "Expected iterator variable name.").lexeme
        
        # Parse condition
        self.consume(TokenType.ASSIGN, "Expected '=' after iterator variable.")
        start = self.expression()
        self.consume(TokenType.SEMICOLON, "Expected ';' after loop initializer.")
        
        condition = self.expression()
        self.consume(TokenType.SEMICOLON, "Expected ';' after loop condition.")
        
        # Parse increment
        increment = self.expression()
        
        self.consume(TokenType.RIGHT_PAREN, "Expected ')' after for clauses.")
        
        # Parse body
        body = self.statement()
        
        # Desugar for loop into a while loop
        initializer = VarDeclaration(iterator, "integer", start, Token(TokenType.IDENTIFIER, iterator, None, 0, 0))
        
        # Create while loop body that includes the increment
        increment_stmt = ExpressionStmt(increment)
        if isinstance(body, Block):
            body.statements.append(increment_stmt)
        else:
            body = Block([body, increment_stmt])
        
        while_loop = While(condition, body)
        
        return Block([initializer, while_loop])

    def return_statement(self) -> Return:
        """Parse a return statement."""
        token = self.previous()
        value = None
        if not self.check(TokenType.RIGHT_BRACE):
            value = self.expression()
        
        return Return(value, token)

    def expression_statement(self) -> ExpressionStmt:
        """Parse an expression statement."""
        expr = self.expression()
        return ExpressionStmt(expr)

    def expression(self) -> Expression:
        """Parse an expression."""
        return self.assignment()

    def assignment(self) -> Expression:
        """Parse an assignment expression."""
        expr = self.equality()
        
        if self.match(TokenType.ASSIGN):
            equals = self.previous()
            value = self.assignment()
            
            if isinstance(expr, Variable):
                return Set(expr, expr.name, value, equals)
            elif isinstance(expr, Get):
                return Set(expr.object, expr.name, value, equals)
            
            raise ParserError("Invalid assignment target.", equals)
        
        return expr

    def equality(self) -> Expression:
        """Parse an equality expression."""
        expr = self.comparison()
        
        while self.match(TokenType.EQUALS, TokenType.NOT_EQUALS):
            operator = self.previous()
            right = self.comparison()
            expr = Binary(expr, operator, right)
        
        return expr

    def comparison(self) -> Expression:
        """Parse a comparison expression."""
        expr = self.term()
        
        while self.match(TokenType.GREATER, TokenType.GREATER_EQUAL,
                        TokenType.LESS, TokenType.LESS_EQUAL):
            operator = self.previous()
            right = self.term()
            expr = Binary(expr, operator, right)
        
        return expr

    def term(self) -> Expression:
        """Parse a term expression."""
        expr = self.factor()
        
        while self.match(TokenType.PLUS, TokenType.MINUS):
            operator = self.previous()
            right = self.factor()
            expr = Binary(expr, operator, right)
        
        return expr

    def factor(self) -> Expression:
        """Parse a factor expression."""
        expr = self.unary()
        
        while self.match(TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.MODULO):
            operator = self.previous()
            right = self.unary()
            expr = Binary(expr, operator, right)
        
        return expr

    def unary(self) -> Expression:
        """Parse a unary expression."""
        if self.match(TokenType.NOT, TokenType.MINUS):
            operator = self.previous()
            right = self.unary()
            return Unary(operator, right)
        
        return self.call()

    def call(self) -> Expression:
        """Parse a call expression."""
        expr = self.primary()
        
        while True:
            if self.match(TokenType.LEFT_PAREN):
                expr = self.finish_call(expr)
            elif self.match(TokenType.DOT):
                name = self.consume(TokenType.IDENTIFIER, "Expected property name after '.'.")
                expr = Get(expr, name.lexeme, name)
            elif self.match(TokenType.LEFT_BRACKET):
                index = self.expression()
                self.consume(TokenType.RIGHT_BRACKET, "Expected ']' after array index.")
                expr = Get(expr, str(index), self.previous())
            else:
                break
        
        return expr

    def finish_call(self, callee: Expression) -> Call:
        """Finish parsing a call expression."""
        arguments = []
        
        if not self.check(TokenType.RIGHT_PAREN):
            while True:
                arguments.append(self.expression())
                if not self.match(TokenType.COMMA):
                    break
        
        paren = self.consume(TokenType.RIGHT_PAREN, "Expected ')' after arguments.")
        
        return Call(callee, arguments, paren)

    def primary(self) -> Expression:
        """Parse a primary expression."""
        if self.match(TokenType.INTEGER, TokenType.STRING, TokenType.BOOLEAN):
            return Literal(self.previous().literal, self.previous())
        
        if self.match(TokenType.THIS):
            return This(self.previous())
        
        if self.match(TokenType.SUPER):
            token = self.previous()
            self.consume(TokenType.DOT, "Expected '.' after 'super'.")
            method = self.consume(TokenType.IDENTIFIER, "Expected superclass method name.")
            return Super(method.lexeme, token)
        
        if self.match(TokenType.IDENTIFIER):
            return Variable(self.previous().lexeme, self.previous())
        
        if self.match(TokenType.LEFT_PAREN):
            expr = self.expression()
            self.consume(TokenType.RIGHT_PAREN, "Expected ')' after expression.")
            return expr
        
        if self.match(TokenType.LEFT_BRACKET):
            elements = []
            if not self.check(TokenType.RIGHT_BRACKET):
                while True:
                    elements.append(self.expression())
                    if not self.match(TokenType.COMMA):
                        break
            
            self.consume(TokenType.RIGHT_BRACKET, "Expected ']' after array elements.")
            return Literal(elements, self.previous())
        
        if self.match(TokenType.NEW):
            name = self.consume(TokenType.IDENTIFIER, "Expected class name after 'new'.")
            self.consume(TokenType.LEFT_PAREN, "Expected '(' after class name.")
            
            arguments = []
            if not self.check(TokenType.RIGHT_PAREN):
                while True:
                    arguments.append(self.expression())
                    if not self.match(TokenType.COMMA):
                        break
            
            paren = self.consume(TokenType.RIGHT_PAREN, "Expected ')' after arguments.")
            
            return Call(Variable(name.lexeme, name), arguments, paren)
        
        raise ParserError("Expected expression.", self.peek())

    def match(self, *types: TokenType) -> bool:
        """Match the current token against the given types."""
        for type_ in types:
            if self.check(type_):
                self.advance()
                return True
        return False

    def check(self, type_: TokenType) -> bool:
        """Check if the current token is of the given type."""
        if self.is_at_end():
            return False
        return self.peek().type == type_

    def advance(self) -> Token:
        """Advance to the next token."""
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def is_at_end(self) -> bool:
        """Check if we've reached the end of the tokens."""
        return self.peek().type == TokenType.EOF

    def peek(self) -> Token:
        """Look at the current token."""
        return self.tokens[self.current]

    def previous(self) -> Token:
        """Get the previous token."""
        return self.tokens[self.current - 1]

    def consume(self, type_: TokenType, message: str) -> Token:
        """Consume a token of the given type."""
        if self.check(type_):
            return self.advance()
        raise ParserError(message, self.peek())

    def synchronize(self) -> None:
        """Synchronize the parser after an error."""
        self.advance()
        
        while not self.is_at_end():
            if self.previous().type == TokenType.RIGHT_BRACE:
                return
            
            if self.peek().type in {
                TokenType.CLASS,
                TokenType.FUN,
                TokenType.VAR,
                TokenType.IF,
                TokenType.WHILE,
                TokenType.FOR,
                TokenType.RETURN,
            }:
                return
            
            self.advance()

    def block(self) -> List[Statement]:
        """Parse a block of statements."""
        statements = []
        
        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            statements.append(self.declaration())
        
        self.consume(TokenType.RIGHT_BRACE, "Expected '}' after block.")
        return statements 