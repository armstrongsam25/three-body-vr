# Three Body VR

A game inspired by Liu Cixin's *The Three Body Problem* — enter the virtual reality world of Trisolaris and attempt to solve the chaotic three-body problem.

## The World

You find yourself in the VR world of Trisolaris, a planet orbiting three suns in an unpredictable, chaotic pattern. Civilizations rise and fall in the brief Stable Eras between Chaotic Eras. Use your wits to observe, predict, and attempt to stabilize the system.

## Features

- **N-body Physics Simulation**: Realistic Newtonian gravity with the three suns
- **Dynamic Eras**: Stable Eras (predictable) and Chaotic Eras (unpredictable) that affect gameplay
- **Civilization Management**: Build and protect your civilization through the cycles
- **Progressive Discovery**: Unlock deeper understanding of the three-body problem
- **Visual Feedback**: See orbital paths, gravitational fields, and civilization status

## Running

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Controls

- Click to place observation points
- Arrow keys / WASD to navigate
- Space to advance time
- E to toggle between observation and prediction mode

## Tech

- Python 3.12+
- Pygame 2.6+
- NumPy (physics calculations)
- ModernGL (GPU-accelerated rendering)

## Status

🚧 Early development — week-long game jam in progress