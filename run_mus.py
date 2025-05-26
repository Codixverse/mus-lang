#!/usr/bin/env python3
"""
Script to run Mus programs.
"""

from mus import Mus

def main():
    """Main entry point."""
    import sys
    
    mus = Mus()
    
    if len(sys.argv) > 2:
        print("Usage: python run_mus.py [script]")
        sys.exit(64)
    elif len(sys.argv) == 2:
        mus.run_file(sys.argv[1])
    else:
        print("Mus Programming Language v0.1.0")
        print("Type 'exit' or 'quit' to exit")
        mus.run_repl()

if __name__ == '__main__':
    main() 