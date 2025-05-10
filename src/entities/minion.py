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
        
        # Store analysis results from camera detection
        self.facial_expression = None
        self.detected_gesture = None
        
    def receive_gesture(self, gesture):
        """Process a gesture from the guide and update item priorities"""
        self.last_gesture = gesture
    
    def receive_analysis_results(self, facial_expression, gesture):
        """Receive analysis results from camera detection"""
        self.facial_expression = facial_expression
        self.detected_gesture = gesture
        
        # Store the gesture as the last_gesture to be used in decision making
        if gesture and gesture.lower() != "unknown":
            self.last_gesture = gesture
            print(f"Minion {self.team_id} received new gesture: {gesture}")
            return True
        else:
            print(f"Minion {self.team_id} received unclear gesture")
            return False
    
    async def decide_move(self, grid, ai_service=None, collected_items=None, target_items=None):
        """Decide next move based on personality and grid state"""
        # Get AI response and cache it for both move and dialogue
        self.ai_response = await ai_service.get_minion_action(
            self, 
            grid, 
            self.last_gesture or "no gesture", 
            collected_items or [],
            target_items
        )
        return self.ai_response
    