"""
Mus Programming Language.
"""

from typing import List, Optional
from .core.lexer import Lexer, Token, TokenType, LexerError
from .core.parser import Parser, Statement, ParserError
from .core.interpreter import Interpreter, InterpreterError
from .core.types import Environment

class Mus:
    """Main class for the Mus language."""
    
    def __init__(self, debug: bool = True):
        self.interpreter = Interpreter()
        self.had_error = False
        self.had_runtime_error = False
        self.debug = debug
    
    def run_file(self, path: str) -> None:
        """Run a Mus program from a file."""
        try:
            with open(path, 'r', encoding='utf-8-sig') as file:
                source = file.read()
            if self.debug:
                print(f"Running file: {path}")
                print("Source code:")
                print("---")
                print(source)
                print("---")
            self.run(source)
            
            if self.had_error:
                raise SystemExit(65)
            if self.had_runtime_error:
                raise SystemExit(70)
        except FileNotFoundError:
            print(f"Error: Could not find file '{path}'")
            raise SystemExit(66)
        except Exception as e:
            print(f"Error: {str(e)}")
            if self.debug:
                import traceback
                traceback.print_exc()
            raise SystemExit(1)
    
    def run_repl(self) -> None:
        """Run the Mus REPL (Read-Eval-Print Loop)."""
        while True:
            try:
                line = input('mus> ')
                if not line:
                    continue
                if line.lower() in ('exit', 'quit'):
                    break
                self.run(line)
                self.had_error = False
            except KeyboardInterrupt:
                print('\nKeyboardInterrupt')
            except EOFError:
                break
            except Exception as e:
                print(f"Error: {str(e)}")
                if self.debug:
                    import traceback
                    traceback.print_exc()
    
    def run(self, source: str) -> None:
        """Run a Mus program from source code."""
        try:
            # Lexical analysis
            if self.debug:
                print("\nLexical analysis...")
            lexer = Lexer(source)
            tokens = lexer.scan_tokens()
            if self.debug:
                print("Tokens:", [str(token) for token in tokens])
            
            # Parsing
            if self.debug:
                print("\nParsing...")
            parser = Parser(tokens)
            statements = parser.parse()
            
            # Stop if there was a syntax error
            if self.had_error:
                return
            
            # Interpretation
            if self.debug:
                print("\nInterpreting...")
            self.interpreter.interpret(statements)
            
        except LexerError as e:
            self.error(e.line, e.column, str(e))
            if self.debug:
                print(f"Lexer error details: {e}")
        except ParserError as e:
            self.error(e.token.line, e.token.column, str(e))
            if self.debug:
                print(f"Parser error details: {e}")
        except InterpreterError as e:
            self.runtime_error(e)
            if self.debug:
                print(f"Interpreter error details: {e}")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            if self.debug:
                import traceback
                traceback.print_exc()
    
    def error(self, line: int, column: int, message: str) -> None:
        """Report an error."""
        self.report(line, column, "", message)
        self.had_error = True
    
    def runtime_error(self, error: InterpreterError) -> None:
        """Report a runtime error."""
        self.report(error.token.line, error.token.column, "Runtime Error", str(error))
        self.had_runtime_error = True
    
    def report(self, line: int, column: int, where: str, message: str) -> None:
        """Print an error message."""
        print(f"[line {line}, column {column}] Error{' ' + where if where else ''}: {message}")

def main() -> None:
    """Main entry point for the Mus language."""
    import sys
    
    mus = Mus(debug=True)
    
    if len(sys.argv) > 2:
        print("Usage: mus [script]")
        sys.exit(64)
    elif len(sys.argv) == 2:
        mus.run_file(sys.argv[1])
    else:
        print("Mus Programming Language v0.1.0")
        print("Type 'exit' or 'quit' to exit")
        mus.run_repl()

if __name__ == '__main__':
    main() 