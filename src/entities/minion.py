import random

class Minion:
    def __init__(self, team_id, grid_pos, personality=None):
        self.team_id = team_id  # 1 or 2
        self.grid_pos = grid_pos  # [y, x]
        
        # Set personality traits (or generate random)
        if personality is None:
            self.personality = {
                "propensity_to_listen": random.uniform(0.3, 1.0),
                "intelligence": random.randint(1, 5),
                "speed": random.randint(1, 5),
                "power": random.randint(1, 5),
                "style": random.choice(["calm", "hectic", "bubbly", "serious", "confused"])
            }
        else:
            self.personality = personality
            
        # Store received gestures
        self.last_gesture = None
        
        # Item priorities based on gestures (higher = more priority)
        # Default: equal priority for all items
        self.item_priorities = {
            1: 1.0,  # Sushi priority
            2: 1.0,  # Donut priority
            3: 1.0,  # Banana priority
        }
        
        # Cache for OpenAI responses
        self.ai_response = None
        
    def receive_gesture(self, gesture):
        """Process a gesture from the guide and update item priorities"""
        self.last_gesture = gesture
        
        # For direct movement commands, we can still return them immediately
        if gesture in ["point up", "point down", "point left", "point right"]:
            return gesture.split(" ")[1]  # Extract direction
        return None
        
    
    def decide_move(self, grid, ai_service=None, collected_items=None, target_items=None):
        """Decide next move based on personality and grid state"""
        # Get AI response and cache it for both move and dialogue
        self.ai_response = ai_service.get_minion_action(
            self, 
            grid, 
            self.last_gesture or "no gesture", 
            collected_items or [],
            target_items
        )
        return self.ai_response.get("move", "stay")
    
    def generate_dialogue(self, move, grid, ai_service=None, collected_items=None):
        """Generate dialogue based on personality and current state"""
        # If using OpenAI and we have a cached response, use it
        if self.ai_response:
            return self.ai_response.get("dialogue", "..."), self.ai_response.get("thought", "...")
        
        # Original local AI logic for dialogue
        style = self.personality["style"]
        intelligence = self.personality["intelligence"]
        
        # Get the item at the target position (if any)
        y, x = self.grid_pos
        if move == "up":
            y -= 1
        elif move == "down":
            y += 1
        elif move == "left":
            x -= 1
        elif move == "right":
            x += 1
            
        # Check if the position is valid
        if 0 <= y < len(grid) and 0 <= x < len(grid[0]):
            target_item = grid[y][x]
        else:
            target_item = 0
            
        dialogue = ""
        thought = ""
        
        # Generate dialogue based on personality style
        if style == "calm":
            if 1 <= target_item <= 3:
                item_name = ["", "sushi", "donut", "banana"][target_item]
                dialogue = f"I see a {item_name}. Let me get that."
                thought = f"The guide wants me to collect {item_name}s, I believe."
            else:
                dialogue = f"Moving {move}."
                thought = "I should keep looking for important items."
                
        elif style == "hectic":
            if 1 <= target_item <= 3:
                item_name = ["", "sushi", "donut", "banana"][target_item]
                dialogue = f"OH! {item_name.upper()}! GOTTA GET IT NOW!"
                thought = f"NEED {item_name.upper()}! NEED IT BAD! Was that right??"
            else:
                dialogue = f"ZOOMING {move.upper()}! GOTTA GO FAST!"
                thought = "WHERE'S THE STUFF? GOTTA FIND THE THINGS!"
                
        elif style == "bubbly":
            if 1 <= target_item <= 3:
                item_name = ["", "sushi", "donut", "banana"][target_item]
                dialogue = f"Ooooh {item_name} time, let's gooo!"
                thought = f"Hmm... hope I got that right! Or maybe it was something else? Oh well, {item_name.upper()}!"
            else:
                dialogue = f"La la la~ Going {move}~"
                thought = "What was I supposed to be looking for again? Oh, something fun!"
                
        elif style == "serious":
            if 1 <= target_item <= 3:
                item_name = ["", "sushi", "donut", "banana"][target_item]
                dialogue = f"Target acquired: {item_name}. Moving to collect."
                thought = f"Based on the guide's signal, the {item_name} is a priority target."
            else:
                dialogue = f"Proceeding {move}."
                thought = "Must locate additional priority items. Analyzing environment."
                
        elif style == "confused":
            if 1 <= target_item <= 3:
                item_name = ["", "sushi", "donut", "banana"][target_item]
                dialogue = f"Is... is that a {item_name}? I think I should grab it?"
                thought = f"Wait, was I supposed to get {item_name}s? Or avoid them? Oh no..."
            else:
                dialogue = f"I'll try... {move}? I guess?"
                thought = "What did that gesture mean again? So many rules to remember..."
        
        # Modify based on intelligence
        if intelligence <= 2:
            # Add some confusion or misunderstanding
            thought += " ...I think?"
            
        return dialogue, thought 