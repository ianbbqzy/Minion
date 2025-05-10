#!/usr/bin/env python3
"""
Signal & Strategy: The Minion's Quest - Main Entry Point
"""
import sys
import os
import argparse
from src.game import Game

def create_env_file(api_key):
    """Create a .env file with the provided API key"""
    try:
        with open(".env", "w") as f:
            f.write(f"OPENAI_API_KEY={api_key}\n")
        print("Created .env file with your API key")
        return True
    except Exception as e:
        print(f"Error creating .env file: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Signal & Strategy: The Minion's Quest")
    parser.add_argument("--openai", "-o", action="store_true", help="Use OpenAI for minion decisions")
    parser.add_argument("--api-key", "-k", help="Set OpenAI API key (will be saved to .env file)")
    parser.add_argument("--create-env", "-e", action="store_true", help="Create a template .env file")
    
    args = parser.parse_args()
    
    # Handle API key argument
    if args.api_key:
        api_key = args.api_key
        if create_env_file(api_key):
            # Set API key in environment for current session
            os.environ["OPENAI_API_KEY"] = api_key
            # Force OpenAI mode if API key is provided
            args.openai = True
    
    # Create template .env file if requested
    if args.create_env and not args.api_key:
        if not os.path.exists(".env"):
            create_env_file("your_api_key_here")
            print("Please edit the .env file to add your OpenAI API key")
            sys.exit(0)
        else:
            print(".env file already exists. Use --api-key to update it.")
            sys.exit(1)
    
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: To use OpenAI, set your API key in one of these ways:")
        print("1. Create a .env file with OPENAI_API_KEY=your_key_here")
        print("2. Run with: python main.py --api-key your_key_here")
        print("3. Set the OPENAI_API_KEY environment variable")
        print("\nTo create a template .env file, run: python main.py --create-env")
        sys.exit(1)
    
    
    # Start the game
    game = Game()
    game.run() 