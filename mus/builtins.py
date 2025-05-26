"""
Built-in functions for the Mus language.
"""

from typing import List, Any
from .types import Environment, Function

def define_builtins(environment: Environment) -> None:
    """Define built-in functions in the given environment."""
    
    # Define out function
    def out_impl(args: List[Any]) -> None:
        """Print the given arguments to stdout."""
        print(*args)
    
    # Create the out function with a single parameter of type 'any'
    out_func = Function('out', [('message', 'any')], ['print(message)'])
    environment.functions['out'] = out_func
    
    # Define error function
    def error_impl(args: List[Any]) -> None:
        """Print the given arguments to stderr."""
        import sys
        print(*args, file=sys.stderr)
    
    # Create the error function with a single parameter of type 'any'
    error_func = Function('error', [('message', 'any')], ['print(message, file=sys.stderr)'])
    environment.functions['error'] = error_func
    
    # Define warn function
    def warn_impl(args: List[Any]) -> None:
        """Print a warning message to stderr."""
        import sys
        print("Warning:", *args, file=sys.stderr)
    
    # Create the warn function with a single parameter of type 'any'
    warn_func = Function('warn', [('message', 'any')], ['print("Warning:", message, file=sys.stderr)'])
    environment.functions['warn'] = warn_func 