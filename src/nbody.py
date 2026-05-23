"""N-body physics engine for the three-body problem."""

import numpy as np
from src.constants import G, SOFTENING


class CelestialBody:
    """A celestial body with position, velocity, mass, and rendering info."""

    def __init__(self, pos, vel, mass, radius, color, name="", is_sun=True):
        self.pos = np.array(pos, dtype=np.float64)
        self.vel = np.array(vel, dtype=np.float64)
        self.mass = mass
        self.radius = radius
        self.color = color
        self.name = name
        self.is_sun = is_sun
        self.acc = np.zeros(2, dtype=np.float64)
        # Orbit trail
        self.trail = []
        self.max_trail = 2000

    def copy(self):
        """Deep copy for prediction mode."""
        b = CelestialBody(
            self.pos.copy(), self.vel.copy(),
            self.mass, self.radius, self.color, self.name, self.is_sun
        )
        b.acc = self.acc.copy()
        return b


class NBodySimulation:
    """Simulates N gravitationally interacting bodies."""

    def __init__(self):
        self.bodies = []
        self.time = 0.0
        self.dt = 0.1

    def add_body(self, body):
        self.bodies.append(body)

    def compute_accelerations(self):
        """Compute gravitational accelerations for all bodies."""
        n = len(self.bodies)
        for i in range(n):
            self.bodies[i].acc = np.zeros(2, dtype=np.float64)

        for i in range(n):
            for j in range(i + 1, n):
                bi = self.bodies[i]
                bj = self.bodies[j]
                r_vec = bj.pos - bi.pos
                r_sq = np.dot(r_vec, r_vec) + SOFTENING ** 2
                r = np.sqrt(r_sq)
                r_hat = r_vec / r

                force_mag = G * bi.mass * bj.mass / r_sq
                force = force_mag * r_hat

                bi.acc += force / bi.mass
                bj.acc -= force / bj.mass

    def step(self, dt=None):
        """Advance simulation by dt using velocity Verlet integration."""
        if dt is None:
            dt = self.dt

        # Record trail positions
        for body in self.bodies:
            body.trail.append(body.pos.copy())
            if len(body.trail) > body.max_trail:
                body.trail.pop(0)

        # Velocity Verlet: half-step velocity
        self.compute_accelerations()
        for body in self.bodies:
            body.vel += 0.5 * body.acc * dt

        # Full-step position
        for body in self.bodies:
            body.pos += body.vel * dt

        # Full-step velocity (with new accelerations)
        self.compute_accelerations()
        for body in self.bodies:
            body.vel += 0.5 * body.acc * dt

        self.time += dt

    def get_body_positions(self):
        return np.array([b.pos for b in self.bodies])

    def get_stability_metric(self):
        """Calculate how stable the system currently is.
        
        Returns a value 0-1 where 0 is maximally chaotic and 1 is extremely stable.
        Based on orbital energy variance.
        """
        if len(self.bodies) < 2:
            return 1.0

        energies = []
        for body in self.bodies:
            ke = 0.5 * body.mass * np.dot(body.vel, body.vel)
            pe = 0
            for other in self.bodies:
                if other is body:
                    continue
                r = np.linalg.norm(body.pos - other.pos) + SOFTENING
                pe += -G * body.mass * other.mass / r
            energies.append(ke + pe)

        energies = np.array(energies)
        if np.std(energies) < 1e-6:
            return 1.0
        # Normalize: lower variance = more stable
        stability = 1.0 / (1.0 + np.std(energies) / (np.abs(np.mean(energies)) + 1e-6))
        return np.clip(stability, 0.0, 1.0)

    def is_body_ejected(self, body_idx):
        """Check if a body is being ejected from the system."""
        if len(self.bodies) < 3:
            return False
        # Check if body is far from center of mass
        com = np.zeros(2)
        total_mass = 0
        for i, b in enumerate(self.bodies):
            if i != body_idx:
                com += b.pos * b.mass
                total_mass += b.mass
        if total_mass > 0:
            com /= total_mass

        dist = np.linalg.norm(self.bodies[body_idx].pos - com)
        # Check velocity direction relative to COM
        vel_toward_com = np.dot(
            self.bodies[body_idx].vel,
            (com - self.bodies[body_idx].pos) / (dist + 1e-6)
        )
        return dist > 800 and vel_toward_com < 0

    def check_collisions(self):
        """Check for close encounters/collisions between bodies."""
        collisions = []
        for i in range(len(self.bodies)):
            for j in range(i + 1, len(self.bodies)):
                bi = self.bodies[i]
                bj = self.bodies[j]
                dist = np.linalg.norm(bi.pos - bj.pos)
                collision_dist = (bi.radius + bj.radius) * 1.5
                if dist < collision_dist:
                    collisions.append((i, j, dist))
        return collisions

    def get_closest_pair(self):
        """Get the closest pair of suns."""
        if len(self.bodies) < 2:
            return None
        min_dist = float('inf')
        closest = None
        for i in range(len(self.bodies)):
            for j in range(i + 1, len(self.bodies)):
                if not self.bodies[i].is_sun or not self.bodies[j].is_sun:
                    continue
                dist = np.linalg.norm(self.bodies[i].pos - self.bodies[j].pos)
                if dist < min_dist:
                    min_dist = dist
                    closest = (i, j, dist)
        return closest

    def is_planet_between_suns(self, planet_idx):
        """Check if the planet is between two suns (double daylight - very hot!)."""
        if len(self.bodies) < 3:
            return 0
        
        planet = self.bodies[planet_idx]
        sun_count = 0
        close_suns = 0
        
        for i, body in enumerate(self.bodies):
            if i != planet_idx and body.is_sun:
                dist = np.linalg.norm(planet.pos - body.pos)
                if dist < 150:
                    close_suns += 1
                if dist < 300:
                    sun_count += 1
        
        return sun_count

    def get_planet_temperature(self, planet_idx):
        """Calculate approximate temperature based on sun distances."""
        planet = self.bodies[planet_idx]
        temp = 0
        base_temp = -50  # Base cold planet
        
        for i, body in enumerate(self.bodies):
            if i != planet_idx and body.is_sun:
                dist = np.linalg.norm(planet.pos - body.pos)
                if dist < 500:
                    temp += body.mass * 5 / (dist / 50 + 1)
        
        return base_temp + temp

    def copy(self):
        """Deep copy the simulation."""
        sim = NBodySimulation()
        sim.bodies = [b.copy() for b in self.bodies]
        sim.time = self.time
        sim.dt = self.dt
        return sim


def create_three_body_system(config="default"):
    """Create the classic three-body problem configuration.
    
    Args:
        config: Which configuration to use.
            "default" - Standard chaotic configuration
            "figure8" - Stable figure-8 orbit (rare!)
            "close" - Tightly packed suns
            "wide" - Widely spaced suns
    """
    sim = NBodySimulation()

    if config == "figure8":
        # The famous figure-8 solution (stable three-body orbit!)
        # This actually works in Newtonian gravity (discovered by Moore, Chenciner, Montgomery)
        sun1 = CelestialBody((0.97000436, -0.24308753), (-0.93240737, -0.86473146),
                            100, 18, (255, 200, 60), "Alpha Sun", True)
        sun2 = CelestialBody((-0.97000436, 0.24308753), (-0.93240737, -0.86473146),
                            100, 18, (255, 140, 40), "Beta Sun", True)
        sun3 = CelestialBody((0, 0), (1.86481474, 1.72946292),
                            100, 18, (255, 100, 50), "Gamma Sun", True)
        # Scale positions up
        for s in [sun1, sun2, sun3]:
            s.pos *= 150
            s.vel *= 20
    elif config == "close":
        sun1 = CelestialBody((0, 0), (0, -10), 100, 18, (255, 200, 60), "Alpha Sun", True)
        sun2 = CelestialBody((150, 80), (5, 15), 90, 16, (255, 140, 40), "Beta Sun", True)
        sun3 = CelestialBody((-120, 100), (-15, -5), 85, 14, (255, 100, 50), "Gamma Sun", True)
    elif config == "wide":
        sun1 = CelestialBody((0, 0), (0, -8), 150, 22, (255, 200, 60), "Alpha Sun", True)
        sun2 = CelestialBody((500, 100), (0, 12), 120, 20, (255, 140, 40), "Beta Sun", True)
        sun3 = CelestialBody((-400, -200), (10, -10), 100, 18, (255, 100, 50), "Gamma Sun", True)
    else:  # default
        sun1 = CelestialBody((0, 0), (0, -15), 120, 20, (255, 200, 60), "Alpha Sun", True)
        sun2 = CelestialBody((300, 0), (0, 25), 100, 18, (255, 140, 40), "Beta Sun", True)
        sun3 = CelestialBody((-200, -150), (20, -20), 80, 16, (255, 100, 50), "Gamma Sun", True)

    sim.add_body(sun1)
    sim.add_body(sun2)
    sim.add_body(sun3)

    return sim


def create_planet(sim, pos, vel, name="Trisolaris"):
    """Add a planet to the simulation."""
    planet = CelestialBody(
        pos=pos,
        vel=vel,
        mass=1.0,
        radius=8,
        color=(40, 180, 255),
        name=name,
        is_sun=False,
    )
    sim.add_body(planet)
    return planet