#!/usr/bin/env python3
"""
Entry point for Socratic RAG System

Launches the main application with proper initialization and error handling.
"""

import sys
from colorama import Fore


def main():
    """Main entry point for Socratic RAG System"""
    try:
        from socratic_system.ui import SocraticRAGSystem

        system = SocraticRAGSystem()
        system.start()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Application interrupted by user.")
        sys.exit(0)
    except ImportError as e:
        print(f"{Fore.RED}Import error: {e}")
        print(f"{Fore.YELLOW}Please ensure all dependencies are installed:")
        print("  pip install chromadb anthropic sentence-transformers PyPDF2 colorama")
        sys.exit(1)
    except Exception as e:
        print(f"{Fore.RED}Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

# Get-ChildItem -Directory -Filter __pycache__ -Recurse | Remove-Item -Recurse -Force
