"""
Custom exceptions for the Mus Programming Language.
"""

from colorama import init, Fore, Style

# Initialize colorama
init()

class Colors:
    ERROR = Fore.RED
    WARNING = Fore.YELLOW
    INFO = Fore.BLUE
    SUCCESS = Fore.GREEN
    RESET = Style.RESET_ALL
    BOLD = Style.BRIGHT

def format_error(message: str, line_number: int = None, error_type: str = "Error") -> str:
    """Format an error message with colors and line number."""
    error_prefix = f"{Colors.ERROR}{Colors.BOLD}{error_type}:{Colors.RESET} "
    if line_number:
        return f"{error_prefix}{message} (line {line_number})"
    return f"{error_prefix}{message}"

class MusError(Exception):
    """Base class for all Mus language errors."""
    def __init__(self, message: str, line_number: int):
        self.message = message
        self.line_number = line_number
        super().__init__(f"Mus Error: {message} (line {line_number})")

class ParserError(MusError):
    """Raised when there is a syntax error in the Mus code."""
    def __init__(self, message: str, line_number: int = None):
        self.message = format_error(message, line_number, "Syntax Error")
        super().__init__(self.message, line_number)

class TypeError(MusError):
    """Raised when there is a type mismatch in the Mus code."""
    def __init__(self, message: str, line_number: int = None):
        self.message = format_error(message, line_number, "Type Error")
        super().__init__(self.message, line_number)

class RuntimeError(MusError):
    """Raised when there is a runtime error in the Mus code."""
    def __init__(self, message: str, line_number: int = None):
        self.message = format_error(message, line_number, "Runtime Error")
        super().__init__(self.message, line_number)

class NameError(MusError):
    """Raised when a variable, function, or class is not found."""
    def __init__(self, message: str, line_number: int = None):
        self.message = format_error(message, line_number, "Name Error")
        super().__init__(self.message, line_number)

class KeyboardInterruptError(MusError):
    """Exception raised when the program is interrupted by the user."""
    def __init__(self):
        self.message = format_error("Program interrupted by user", None, "Interrupt Error")
        super().__init__(self.message) 