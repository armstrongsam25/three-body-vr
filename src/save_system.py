"""Save/Load system for Three Body VR."""

import json
import os
import numpy as np
from datetime import datetime

SAVE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "saves")
MAX_SAVES = 10


class SaveSystem:
    """Handles game save/load functionality."""

    def __init__(self):
        os.makedirs(SAVE_DIR, exist_ok=True)

    def save_game(self, simulation, planet, civilization, milestones, metadata=None):
        """Save current game state to a file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"save_{timestamp}.json"
        filepath = os.path.join(SAVE_DIR, filename)

        # Serialize simulation state
        bodies_data = []
        for body in simulation.bodies:
            bodies_data.append({
                'pos': body.pos.tolist(),
                'vel': body.vel.tolist(),
                'mass': body.mass,
                'radius': body.radius,
                'color': list(body.color),
                'name': body.name,
                'is_sun': body.is_sun,
                'trail': [p.tolist() for p in body.trail[-500:]],  # Keep last 500 trail points
            })

        # Serialize civilization
        civ_data = civilization.get_state()
        civ_data['events'] = civilization.events[-50:]  # Keep last 50 events

        save_data = {
            'version': '0.1',
            'timestamp': timestamp,
            'metadata': metadata or {},
            'simulation': {
                'time': simulation.time,
                'bodies': bodies_data,
                'planet_idx': len(bodies_data) - 1,  # Planet is always last
            },
            'civilization': civ_data,
            'milestones': milestones.milestones,
        }

        try:
            with open(filepath, 'w') as f:
                json.dump(save_data, f, indent=2)
            self._cleanup_old_saves()
            return filename
        except Exception as e:
            print(f"Save failed: {e}")
            return None

    def load_game(self, sim_constructor, civ_constructor, milestones_constructor):
        """Load most recent save. Returns (simulation, planet, civilization, milestones, metadata) or None."""
        saves = self.list_saves()
        if not saves:
            return None

        latest = saves[0]  # Most recent
        return self._load_file(latest, sim_constructor, civ_constructor, milestones_constructor)

    def load_specific(self, filename, sim_constructor, civ_constructor, milestones_constructor):
        """Load a specific save file."""
        filepath = os.path.join(SAVE_DIR, filename)
        if not os.path.exists(filepath):
            return None
        return self._load_file(filename, sim_constructor, civ_constructor, milestones_constructor)

    def _load_file(self, filename, sim_constructor, civ_constructor, milestones_constructor):
        """Load game from a specific file."""
        from src.nbody import NBodySimulation, CelestialBody

        filepath = os.path.join(SAVE_DIR, filename)
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Load failed: {e}")
            return None

        # Reconstruct simulation
        sim = NBodySimulation()
        sim.time = data['simulation']['time']

        for body_data in data['simulation']['bodies']:
            body = CelestialBody(
                pos=np.array(body_data['pos']),
                vel=np.array(body_data['vel']),
                mass=body_data['mass'],
                radius=body_data['radius'],
                color=tuple(body_data['color']),
                name=body_data['name'],
                is_sun=body_data['is_sun'],
            )
            body.trail = [np.array(p) for p in body_data.get('trail', [])]
            sim.add_body(body)

        planet = sim.bodies[-1]  # Planet is always last

        # Reconstruct civilization
        civilization = civ_constructor()
        civ_data = data['civilization']
        civilization.population = civ_data.get('population', 50)
        civilization.max_population = civ_data.get('max_population', 100)
        civilization.current_era = civ_data.get('era', 'stable')
        civilization.era_duration = civ_data.get('era_duration', 0)
        civilization.knowledge = civ_data.get('knowledge', 0)
        civilization.collapse_count = civ_data.get('collapse_count', 0)
        civilization.events = civ_data.get('events', [])

        # Reconstruct milestones
        milestones = milestones_constructor()
        milestones.milestones = data.get('milestones', milestones.milestones)

        return sim, planet, civilization, milestones, data.get('metadata', {})

    def list_saves(self):
        """List all save files, newest first."""
        if not os.path.exists(SAVE_DIR):
            return []

        saves = [f for f in os.listdir(SAVE_DIR) if f.startswith('save_') and f.endswith('.json')]
        saves.sort(reverse=True)
        return saves

    def get_save_info(self, filename):
        """Get metadata about a save file."""
        filepath = os.path.join(SAVE_DIR, filename)
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            civ = data.get('civilization', {})
            return {
                'filename': filename,
                'timestamp': data.get('timestamp', 'unknown'),
                'era': civ.get('era', 'unknown'),
                'population': civ.get('population', 0),
                'knowledge': civ.get('knowledge', 0),
            }
        except Exception:
            return {
                'filename': filename,
                'timestamp': 'corrupted',
                'era': 'unknown',
                'population': 0,
                'knowledge': 0,
            }

    def delete_save(self, filename):
        """Delete a save file."""
        filepath = os.path.join(SAVE_DIR, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False

    def _cleanup_old_saves(self):
        """Remove oldest saves if exceeding MAX_SAVES."""
        saves = self.list_saves()
        while len(saves) > MAX_SAVES:
            oldest = saves.pop()
            self.delete_save(oldest)