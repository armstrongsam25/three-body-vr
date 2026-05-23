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

    def copy(self):
        """Deep copy the simulation."""
        sim = NBodySimulation()
        sim.bodies = [b.copy() for b in self.bodies]
        sim.time = self.time
        sim.dt = self.dt
        return sim


def create_three_body_system():
    """Create the classic three-body problem configuration.
    
    Three suns with slightly perturbed initial conditions for interesting chaos.
    """
    sim = NBodySimulation()

    # Sun 1 (Alpha) - large, central
    sun1 = CelestialBody(
        pos=(0, 0),
        vel=(0, -15),
        mass=120.0,
        radius=20,
        color=(255, 200, 60),
        name="Alpha Sun",
        is_sun=True,
    )

    # Sun 2 (Beta) - medium, orbiting
    sun2 = CelestialBody(
        pos=(300, 0),
        vel=(0, 25),
        mass=100.0,
        radius=18,
        color=(255, 140, 40),
        name="Beta Sun",
        is_sun=True,
    )

    # Sun 3 (Gamma) - smaller, eccentric orbit
    sun3 = CelestialBody(
        pos=(-200, -150),
        vel=(20, -20),
        mass=80.0,
        radius=16,
        color=(255, 100, 50),
        name="Gamma Sun",
        is_sun=True,
    )

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