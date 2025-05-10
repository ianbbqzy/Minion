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
        