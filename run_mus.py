#!/usr/bin/env python3
"""
Main entry point for the Mus Programming Language interpreter.
"""

import sys
import os
from mus.interpreter import Interpreter
from mus.exceptions import MusError, KeyboardInterruptError

def main():
    """Main entry point for the Mus interpreter."""
    if len(sys.argv) != 2:
        print("Usage: python run_mus.py <source_file.mus>")
        sys.exit(1)
        
    source_file = sys.argv[1]
    if not os.path.exists(source_file):
        print(f"File not found: {source_file}")
        sys.exit(1)
        
    try:
        with open(source_file, 'r', encoding='utf-8') as f:
            source = f.read()
        
        interpreter = Interpreter()
        interpreter.run(source)
        
    except KeyboardInterrupt:
        print("\nMus Program interrupted by user.")
        sys.exit(130)
    except KeyboardInterruptError as e:
        print(e.message)
        sys.exit(130)
    except MusError as e:
        print(f"Error: {e}")
        if hasattr(e, 'line_number') and e.line_number:
            if 1 <= e.line_number <= len(source):
                print(f"\nLine {e.line_number}: {source[e.line_number-1]}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 