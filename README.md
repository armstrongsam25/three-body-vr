# 🌌 Three Body VR

A game inspired by Liu Cixin's *The Three Body Problem* — enter the VR world of Trisolaris and attempt to solve the chaotic three-body problem.

~3,650 lines of Python code. Built in a week-long game jam.

## 🎮 Gameplay

You find yourself on **Trisolaris**, a planet orbiting three suns in an unpredictable, chaotic pattern. Civilizations rise and fall as the eras shift between Stable (predictable) and Chaotic (deadly). Your goal: observe, predict, and guide civilization toward understanding the three-body problem.

### Core Mechanics

- **Orbital Observation** — Watch the three suns dance. Study their patterns.
- **Prediction Mode** — Draw predicted orbital paths and earn accuracy scores (E key)
- **Civilization Management** — Grow your population during Stable Eras, hunker down during Chaos
- **Knowledge System** — Accumulate understanding, unlock discoveries, earn milestones
- **Difficulty Scaling** — 4 levels from "Stable Observer" to "Dark Forest"

### Features

- ⚛️ **N-body Physics** — Velocity Verlet integration with realistic gravitational forces
- 🌡️ **Planet Temperature** — Your planet heats up near suns and freezes in deep space
- 💥 **Sun Collisions** — When suns get too close: particle effects, shockwaves, screen shake
- 🎨 **Visual Effects** — Nebula clouds, multi-layer parallax starfield, bloom, scanlines, vignette
- 📜 **Lore System** — Quotes and narrative from The Three Body Problem universe
- 🏆 **8 Achievements** — Unlock milestones from "First Cycle" to "Enlightenment"
- 🎬 **4 Scenarios** — Classic Trisolaris, Figure-Eight, Tight Embrace, Vast Expanse
- 💾 **Save/Load** — Quick save (F5) and quick load (F9)

## 🚀 Running

```bash
# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Play
python main.py
```

### Controls

| Key | Action |
|-----|--------|
| Space | Pause / Resume |
| E | Toggle Prediction Mode |
| R | Reset Simulation |
| H | Toggle Help |
| Tab | Toggle Event Log |
| M | Mute / Unmute |
| F5 / F9 | Quick Save / Load |
| F | Fullscreen |
| 0 / 1 / 2 / 5 | Set Time Speed (paused / 1× / 2× / 5×) |
| [ / ] | Fine-tune Time Scale |
| + / - | Zoom In / Out |
| Arrow Keys | Pan View |
| Mouse Drag / Scroll | Pan / Zoom |
| Left Click | Draw prediction path (in Predict mode) |
| Right Click | Pan (in Predict mode) |
| Esc | Menu / Quit |

## 🏗️ Architecture

```
threebody-vr/
├── main.py              # Game loop, state machine, input handling
├── src/
│   ├── nbody.py         # N-body physics engine (Velocity Verlet)
│   ├── renderer.py      # Camera, sun glow, orbit trails, VR effects
│   ├── civilization.py  # Population, era tracking, collapse system
│   ├── prediction.py    # Orbital prediction overlay & knowledge discovery
│   ├── effects.py       # Nebula, shockwaves, screen shake, transitions
│   ├── starfield.py     # Multi-layer parallax starfield & bloom
│   ├── progression.py   # Difficulty levels, scenario management
│   ├── menu.py          # Main menu & pause menu screens
│   ├── scenario_select.py  # Scenario/difficulty selection screen
│   ├── achievements.py  # Achievements & stats display
│   ├── audio.py         # Procedural audio generation
│   ├── lore.py          # Lore quotes & narrative
│   ├── save_system.py   # JSON save/load system
│   └── constants.py     # Physics constants, colors, config
└── requirements.txt
```

## 🛠️ Tech Stack

- Python 3.12+
- Pygame 2.6+ (rendering, input)
- NumPy (physics calculations)

## 📝 Roadmap Ideas

- [ ] GPU-accelerated rendering with ModernGL
- [ ] Multiplayer civilization collaboration
- [ ] More scenarios and initial conditions
- [ ] Ship deployment (send Trisolaran fleet)
- [ ] Advanced prediction tools (draw freehand, multi-sun)
- [ ] Soundtrack and better audio
- [ ] Particle effects for stellar phenomena
- [ ] Civilization tech tree

---

*"The universe is a dark forest. Every civilization is an armed hunter stalking through the trees." — Liu Cixin*