import random

class Guide:
    def __init__(self, team_id, target_items):
        self.team_id = team_id  # 1 or 2
        self.target_items = target_items  # List of 5 items to collect
        
        # Available gestures
        self.gestures = [
            "wink left eye",   # Prioritize donuts
            "wink right eye",  # Prioritize sushi 
            "nod twice",       # Prioritize bananas
            "point up",        # Move up
            "point down",      # Move down
            "point left",      # Move left
            "point right",     # Move right
        ]
        
        # Keep track of which items are most needed
        self.item_counts = {
            1: self.target_items.count(1),  # Count of sushi needed
            2: self.target_items.count(2),  # Count of donuts needed
            3: self.target_items.count(3),  # Count of bananas needed
        }
        
        # Track what the minion has collected
        self.collected_items = []
        
    def update_collected(self, collected_items):
        """Update the guide's knowledge of what items have been collected"""
        self.collected_items = collected_items
        
    def decide_gesture(self, grid, minion_pos, enemy_pos=None):
        """
        Decide which gesture to send based on:
        1. Which target items are still needed
        2. What items are nearby
        3. Where the enemy is
        """
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
        
        # If there's a direct path to a needed item, point to it
        for direction, (dy, dx) in [("point up", (-1, 0)), ("point down", (1, 0)), 
                                   ("point left", (0, -1)), ("point right", (0, 1))]:
            new_y, new_x = y + dy, x + dx
            # Check bounds
            if 0 <= new_y < len(grid) and 0 <= new_x < len(grid[0]):
                item = grid[new_y][new_x]
                # If it's a collectible item that we need
                if 1 <= item <= 3 and needed_items.get(item, 0) > 0:
                    return direction
        
        # If no direct paths, prioritize the most needed item type
        most_needed = max(needed_items.items(), key=lambda x: x[1])
        most_needed_item, most_needed_count = most_needed
        
        # If we still need this item
        if most_needed_count > 0:
            # Check if this item type is nearby
            if nearby_items.get(most_needed_item, 0) > 0:
                # Signal based on item type
                if most_needed_item == 1:  # Sushi
                    return "wink right eye"
                elif most_needed_item == 2:  # Donut
                    return "wink left eye"
                elif most_needed_item == 3:  # Banana
                    return "nod twice"
        
        # If no clear priority, give a random directional gesture
        # to encourage exploration
        return random.choice(["point up", "point down", "point left", "point right"]) 