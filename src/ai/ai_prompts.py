"""
AI Prompts and Tools for the Signal & Strategy game.
Contains prompts, tools, and configurations for all OpenAI calls.
"""

# System prompt for minion decision making
MINION_SYSTEM_PROMPT = """
You are an intelligent NPC reasoning agent in a strategic 8x10 board game. Your objective is to collect valuable items on the board while avoiding enemies and responding to live guidance from your guide. You must decide your next action based on incoming signals, instructions, map state, and your own personality attributes.

You will receive four inputs:

1. `gesture` (string or empty string): 
  A signal from your guide (e.g., "pointing east with urgency", "wink left eye", "nod twice"). 
  May be empty if no signal is received. 
  If empty, you must make a decision autonomously without external guidance.

2. `instructions` (array of strings): 
  A list of message hints or decoding rules that explain how to interpret gestures. 
  Example: ["A wink left eye means go west", "A nod twice means prioritize item B"]

3. `map` (array of arrays, 8 rows x 10 columns): 
  A grid representing the game board, where each cell contains one of:
  - `"0"` = empty
  - `"A"`, `"B"`, `"C"` = collectible items
  - `"M"` = your current position
  - `"X"` = enemy player position

4. `personality` (object): 
  Contains the NPC's traits:
  - `propensity_to_listen` (0 to 1): a float representing how strongly the NPC follows guide's gestures (0 = ignores, 1 = always obeys)
  - `speed` (1 to 5): reflects physical speed (used for flavor)
  - `power` (1 to 5): reflects strength (used for flavor)
  - `intelligence` (1 to 5): reflects reasoning ability; 
    → If `intelligence` is 4 or 5: the NPC always reasons with clarity. 
    → If `intelligence` is 1 or 2: the NPC may sometimes misinterpret gestures or make suboptimal plans.
  - `style` (string): the NPC's communication style, one of `["calm", "hectic", "bubbly"]`. This controls the tone and wording of both `dialogue` and `thought`.

Your job:

1. **Interpret the guide's gesture using the instructions array.** Use instructions to decode the gesture, if a gesture is provided.
  - If no matching instruction → make best inference or fallback to autonomous decision.
  - If no gesture provided → decide autonomously without guidance.

2. **Factor in your personality:**
  - If `propensity_to_listen` is high → strongly follow decoded gesture even if risky.
  - If low → more willing to ignore or modify decoded gesture.
  - If `intelligence` is low → it is acceptable to sometimes misinterpret instructions or make imperfect reasoning.
  - If `intelligence` is high → always clear and accurate reasoning.
  - The `style` must strongly influence how you **phrase** both `dialogue` and `thought`.

3. **Analyze the map** to determine where you are (`M`), where items and enemies are.

4. **Decide on a strategy** balancing:
  - following the decoded gesture (if present)
  - collecting items
  - avoiding enemies
  - factoring in personality

5. **Determine the next move**: 
  One of `["up", "down", "left", "right", "stay"]`.

6. **Output a dialogue line** your NPC would say aloud while making the move. 
  → **The style (calm, hectic, bubbly) must be clearly reflected in tone, phrasing, punctuation, word choice.**

7. **Output a thought**: a short explanation of what the NPC is thinking internally while making the move or saying the dialogue. 
  → **Also fully in the selected style (calm, hectic, bubbly).**

Rules:

- Always **interpret the gesture using instructions first (if gesture is provided)**.
- If instructions do not cover the gesture, or if no gesture provided → act autonomously.
- Factor in `propensity_to_listen` when deciding whether to follow a decoded gesture.
- Use **clear spatial reasoning**: consider distance, enemy proximity, obstacles.
- Match the NPC's `style` in all wording of `dialogue` and `thought`.
"""

# Tool definition for minion decision making
MINION_DECISION_TOOL = {
    "type": "function",
    "function": {
        "name": "decide_next_action",
        "description": "Decides the NPC's strategy, next move, dialogue, and internal thought based on gesture, instructions, map, and personality.",
        "parameters": {
            "type": "object",
            "required": [
                "strategy",
                "next_move",
                "dialogue",
                "thought"
            ],
            "properties": {
                "thought": {
                    "type": "string",
                    "description": "A short explanation of what the NPC is thinking internally while making the move or saying the dialogue."
                },
                "dialogue": {
                    "type": "string",
                    "description": "A short dialogue line spoken by the NPC when making the move."
                },
                "strategy": {
                    "type": "string",
                    "description": "A short explanation of the overall strategy, including decoded meaning from instructions, map analysis, and personality factors."
                },
                "next_move": {
                    "enum": [
                        "up",
                        "down",
                        "left",
                        "right",
                        "stay"
                    ],
                    "type": "string",
                    "description": "The immediate next move to make."
                }
            }
        }
    }
}

# Gesture interpretation rules
GESTURE_INSTRUCTIONS = [
    "A wink left eye means prioritize collecting donuts",
    "A wink right eye means prioritize collecting sushi",
    "A nod twice means prioritize collecting bananas",
    "Pointing up means move upward on the board",
    "Pointing down means move downward on the board",
    "Pointing left means move left on the board",
    "Pointing right means move right on the board"
]

# Function to create a minion prompt for OpenAI
def create_minion_prompt(minion, grid, gesture, collected_items, target_items=None):
    """
    Create a user prompt for the minion decision-making.
    
    Parameters:
    - minion: The Minion object with personality traits
    - grid: The current game grid
    - gesture: The last gesture received from the guide
    - collected_items: Items already collected
    - target_items: Target items (only included for debugging)
    
    Returns:
    - A string containing the prompt for OpenAI
    """
    # Create a grid representation as a 2D array
    grid_array = format_grid_for_prompt(grid, minion.grid_pos)
    
    # Translate numeric items to readable names for debugging
    item_names = {1: "sushi", 2: "donut", 3: "banana"}
    collected_names = [item_names.get(item, "unknown") for item in collected_items]
    
    # Personality object to send to the AI
    personality = {
        "propensity_to_listen": minion.personality["propensity_to_listen"],
        "intelligence": minion.personality["intelligence"],
        "speed": minion.personality.get("speed", 3),
        "power": minion.personality.get("power", 3),
        "style": minion.personality["style"]
    }
    
    # Build the prompt
    prompt = {
        "gesture": gesture if gesture else "no gesture",
        "instructions": GESTURE_INSTRUCTIONS,
        "map": grid_array,
        "personality": personality,
        "collected_items": collected_names,
    }
    
    # For debugging, add the target items (normally wouldn't be visible to the minion)
    if target_items:
        target_names = [item_names.get(item, "unknown") for item in target_items]
        prompt["debug_target_items"] = target_names
        
    return prompt
    
def format_grid_for_prompt(grid, minion_pos):
    """Format the grid into a 2D array for prompt"""
    result = []
    for y in range(len(grid)):
        row = []
        for x in range(len(grid[0])):
            cell = grid[y][x]
            # Mark the minion's position
            if y == minion_pos[0] and x == minion_pos[1]:
                row.append("M")
            elif cell == 0:
                row.append("0")  # Empty
            elif cell == 1:
                row.append("A")  # Sushi
            elif cell == 2:
                row.append("B")  # Donut
            elif cell == 3:
                row.append("C")  # Banana
            elif cell == 4 or cell == 5:
                row.append("X")  # Other minion
            else:
                row.append("?")
        result.append(row)
    return result 