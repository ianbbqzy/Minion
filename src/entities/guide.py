import random

class Guide:
    def __init__(self, team_id, target_items):
        self.team_id = team_id  # 1 or 2
        self.target_items = target_items  # List of 5 items to collect
        
        # Keep track of which items are most needed
        self.item_counts = {
            1: self.target_items.count(1),  # Count of sushi needed
            2: self.target_items.count(2),  # Count of donuts needed
            3: self.target_items.count(3),  # Count of bananas needed
        }
        
        # Track what the minion has collected
        self.collected_items = []
        
        # Store the last detected gesture from vision model
        self.last_detected_gesture = None
        self.last_detected_facial_expression = None
        
    def update_collected(self, collected_items):
        """Update the guide's knowledge of what items have been collected"""
        self.collected_items = collected_items
        
    def receive_detection_results(self, facial_expression, gesture):
        """Store detection results from the vision model"""
        self.last_detected_facial_expression = facial_expression
        self.last_detected_gesture = gesture
        return True
        
    def decide_gesture(self, grid, minion_pos, enemy_pos=None):
        """
        Decide which gesture to send based on:
        1. If using webcam: return the last detected gesture from vision model
        2. Otherwise, generate a random gesture (for AI-only mode)
        """
        # If we have a detected gesture from the vision model, use it
        if self.last_detected_gesture and self.last_detected_gesture.lower() != "unknown":
            detected_gesture = self.last_detected_gesture
            # Clear it so it doesn't get reused unless explicitly set again
            self.last_detected_gesture = None
            return detected_gesture
            
        # Otherwise, generate a random gesture for AI-only mode
        # Count what's still needed
        needed_items = {
            1: self.target_items.count(1) - self.collected_items.count(1),  # Sushi needed
            2: self.target_items.count(2) - self.collected_items.count(2),  # Donuts needed
            3: self.target_items.count(3) - self.collected_items.count(3),  # Bananas needed
        }
        
        # Find nearby items (within 3 cells)
        nearby_items = {}
        y, x = minion_pos
        
        # Check in a 7x7 grid around the minion (3 cells in each direction)
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                new_y, new_x = y + dy, x + dx
                
                # Check bounds
                if 0 <= new_y < len(grid) and 0 <= new_x < len(grid[0]):
                    item = grid[new_y][new_x]
                    
                    # If it's a collectible item
                    if 1 <= item <= 3:
                        # Count this type of item
                        nearby_items[item] = nearby_items.get(item, 0) + 1
        
        # For demonstration only, generate natural language descriptions
        directions = ["pointing up", "pointing down", "pointing left", "pointing right"]
        expressions = ["smiling", "frowning", "raising eyebrows", "squinting"]
        
        # Return a natural language description as would come from the vision model
        if random.random() < 0.7:  # 70% chance for direction guidance
            return random.choice(directions)
        else:
            return random.choice(expressions) 