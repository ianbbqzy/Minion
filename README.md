# Signal & Strategy: The Minion's Quest

A strategic communication game where guides use gestures to direct minions in collecting targets.

## Overview

This game features two teams, each consisting of a Guide and a Minion. Guides communicate through gestures to help their Minions navigate a grid and collect specific target items. The first team to collect all their target items wins.

## Features

- Strategic gameplay with gesture-based communication
- AI-driven minion behavior
- OpenAI integration for gesture recognition via webcam
- Personality-driven minion responses

## Installation

1. Clone this repository
2. Install dependencies:
   ```
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Run the game:
   ```
   python main.py
   ```

## Command Line Options


## Project Structure

```
src/
├── ai/                 # AI and OpenAI integration
├── entities/           # Game entities (minions, guides)
├── input/              # Input handling
├── rendering/          # Rendering and UI components
└── utils/              # Utility classes and constants
```

## Gameplay

- Use the "Take AI Turn" button or Space key to have AI make decisions
- Press R to restart the game
- Arrow keys and number keys (1-3) can be used for manual gestures
- With a webcam and OpenAI API key, you can use actual hand gestures

## Credits

Created for a hackathon project. 