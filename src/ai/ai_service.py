import os
import openai
from dotenv import load_dotenv
import json
from src.ai.ai_prompts import MINION_SYSTEM_PROMPT, MINION_DECISION_TOOL, create_minion_prompt

# Find and load environment variables from .env file
# First try in the current directory, then in the project root
if os.path.exists(".env"):
    load_dotenv()
elif os.path.exists(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")):
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
else:
    print("Warning: No .env file found. Please create one with your OPENAI_API_KEY.")

class AIService:
    def __init__(self, api_key=None):
        # Use API key from parameter, environment variable, or .env file
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            print("Warning: No OpenAI API key found. Please set OPENAI_API_KEY.")
        
        # Initialize OpenAI client if we have an API key
        if self.api_key:
            # api_type_to_use = os.getenv("OPENAI_API_TYPE", "openai")
            self.client = openai.OpenAI(api_key=self.api_key)
        else:
            self.client = None
            
        self.model = "gpt-3.5-turbo"  # Default model, can be changed to gpt-4 for better reasoning
        
    def get_minion_action(self, minion, grid, gesture, collected_items, target_items=None):
        """
        Get a minion's action decision from OpenAI
        
        Parameters:
        - minion: The Minion object with personality traits
        - grid: The current game grid
        - gesture: The last gesture received from the guide
        - collected_items: Items already collected
        - target_items: Target items (only included for debugging)
        
        Returns:
        - A dictionary with move, dialogue, and thoughts
        """
        # If no client is available, return a default response
        if not self.client:
            return {
                "move": "stay",
                "dialogue": "I need my guide's API key to think properly!",
                "thought": "My connection to the hive mind seems... broken?"
            }
            
        # Create a prompt for the minion using the new prompt creator
        user_prompt = create_minion_prompt(minion, grid, gesture, collected_items, target_items)
        
        try:
            # Call OpenAI API with function calling and our new system prompt
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": MINION_SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps(user_prompt)}
                ],
                tools=[MINION_DECISION_TOOL],
                tool_choice={"type": "function", "function": {"name": "decide_next_action"}}
            )
            
            # Extract tool call result
            if response.choices[0].message.tool_calls:
                tool_call = response.choices[0].message.tool_calls[0]
                result = json.loads(tool_call.function.arguments)
                
                # Map from the new response format to the old one
                return {
                    "move": result.get("next_move", "stay"),
                    "dialogue": result.get("dialogue", "..."),
                    "thought": result.get("thought", "..."),
                    "strategy": result.get("strategy", "No strategy available")
                }
                
            # Fallback in case function calling fails
            return {
                "move": "stay",
                "dialogue": "I'm not sure what to do.",
                "thought": "The signal is confusing me..."
            }
            
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            # Return a default response if API call fails
            return {
                "move": "stay",
                "dialogue": "Hmm, I need to think...",
                "thought": "My guide's instructions are unclear."
            } 