import os
import requests
import json
import random
from typing import Dict, List, Tuple, Union

class AIController:
    """
    Controls minion movement using OpenAI's API
    """
    
    def __init__(self) -> None:
        # OpenAI API key (should be stored securely in a real application)
        self.openai_api_key = os.environ.get("OPENAI_API_KEY", "your_api_key_here")
    
    def get_movement_direction(self) -> str:
        """
        Ask ChatGPT to decide which direction the minion should move.
        Returns a direction string: "up", "down", "left", or "right"
        """
        url = "https://api.openai.com/v1/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.openai_api_key}"
        }
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system", 
                    "content": "You are controlling a character in a game. Your only response should be a function call to move()."
                },
                {
                    "role": "user", 
                    "content": "Which direction should the character move next? Choose one: up, down, left, or right."
                }
            ],
            "functions": [
                {
                    "name": "move",
                    "description": "Move the character in a specific direction",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "direction": {
                                "type": "string",
                                "enum": ["up", "down", "left", "right"],
                                "description": "Direction to move"
                            }
                        },
                        "required": ["direction"]
                    }
                }
            ],
            "function_call": {"name": "move"}
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response_data = response.json()
            
            # Extract the direction from function call
            if "choices" in response_data and len(response_data["choices"]) > 0:
                choice = response_data["choices"][0]
                if "function_call" in choice["message"]:
                    function_args = json.loads(choice["message"]["function_call"]["arguments"])
                    return function_args["direction"]
            
            # Fallback to random direction if API call fails
            return random.choice(["up", "down", "left", "right"])
            
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            # Fallback to random direction
            return random.choice(["up", "down", "left", "right"])
    
    @staticmethod
    def direction_to_tuple(direction: str) -> Tuple[int, int]:
        """Convert a direction string to a (dx, dy) tuple"""
        direction_map = {
            "left": (-1, 0),
            "right": (1, 0),
            "up": (0, -1),
            "down": (0, 1)
        }
        return direction_map.get(direction, (0, 0))
