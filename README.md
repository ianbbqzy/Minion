# Minion Movement Game

A 2D top-down game where minions move around on a beautiful tilemap.

## Setup

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the game:
   ```
   python main.py
   ```

## Game Controls

- Close the window to exit the game

## Features

- Beautiful tilemap with multiple tile types (grass, dirt, water, sand, paths)
- Animated minions that move in random directions
- Minions use sprite animations for different directions
- Random map generation creates a unique environment each time

## Project Structure

```
├── main.py              # Main entry point
├── requirements.txt     # Python dependencies
├── src/                 # Source code
│   ├── game.py          # Main game logic
│   ├── sprites.py       # Sprite classes (minions)
│   └── tilemap.py       # Tilemap handling
└── assets/              # Game assets
    ├── images/          # Images
    │   ├── tiles/       # Tile images
    │   └── minions/     # Minion sprite sheets
    └── sounds/          # Sound effects (future)
```

## Custom Sprites

To use custom sprites, place tile images in `assets/images/tiles/` named:
- grass.png
- dirt.png
- water.png
- path.png
- sand.png

For minion animations, place sprites in `assets/images/minions/` with naming format:
- minion_down_1.png, minion_down_2.png, etc.
- minion_up_1.png, minion_up_2.png, etc.
- minion_left_1.png, minion_left_2.png, etc.
- minion_right_1.png, minion_right_2.png, etc.

If these files don't exist, the game will generate placeholder graphics. 