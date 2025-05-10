#!/usr/bin/env python
import time
import os
import subprocess
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class GameRestartHandler(FileSystemEventHandler):
    def __init__(self):
        self.process = None
        self.start_game()
        
    def start_game(self):
        """Start the game process"""
        # Kill existing process if it exists
        if self.process:
            print("Terminating existing game process...")
            self.process.terminate()
            self.process.wait()
            
        print("\n--- RESTARTING GAME ---\n")
        
        # Start the game with or without OpenAI
        cmd = [sys.executable, "main.py"]
            
        self.process = subprocess.Popen(cmd)
            
    def on_modified(self, event):
        """Restart the game when a Python file is modified"""
        if event.src_path.endswith('.py'):
            print(f"Change detected in {event.src_path}")
            self.start_game()
            
    def on_created(self, event):
        """Restart the game when a new Python file is created"""
        if event.src_path.endswith('.py'):
            print(f"New file created: {event.src_path}")
            self.start_game()
            
    def __del__(self):
        """Clean up process when the handler is destroyed"""
        if self.process:
            self.process.terminate()
            
def main():
    # Create event handler
    event_handler = GameRestartHandler()
    
    # Set up the observer to watch the source directory
    observer = Observer()
    observer.schedule(event_handler, path='src', recursive=True)
    observer.start()
    
    print(f"Auto-runner started! Watching for changes in src/ directory...")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping auto-runner...")
        observer.stop()
        
    observer.join()
    
if __name__ == "__main__":
    main() 