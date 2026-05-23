"""Prediction overlay and interactive knowledge system.

Players can draw predicted orbital paths for the suns to attempt
to solve the three-body problem. Accuracy rewards knowledge points.
"""

import math
import pygame
import numpy as np
from src.constants import *


class PredictionOverlay:
    """Allows players to draw predicted paths for the suns."""

    def __init__(self):
        self.active = False
        self.current_prediction = []  # Points being drawn
        self.predictions = []  # List of (points, color, accuracy)
        self.prediction_color = (100, 255, 200)
        self.selected_sun = 0
        self.max_prediction_points = 200
        self.last_eval_time = 0
        self.eval_interval = 300  # Frames between auto-evaluations

    def toggle(self):
        """Toggle prediction mode."""
        self.active = not self.active
        if not self.active:
            self.current_prediction = []
        return self.active

    def set_sun(self, index):
        """Select which sun to predict for."""
        self.selected_sun = max(0, min(2, index))

    def add_point(self, pos):
        """Add a point to the current prediction."""
        if self.active and len(self.current_prediction) < self.max_prediction_points:
            self.current_prediction.append(np.array(pos))

    def clear_current(self):
        """Clear the current prediction being drawn."""
        self.current_prediction = []

    def commit_prediction(self, simulation):
        """Commit the drawn prediction and evaluate accuracy."""
        if not self.current_prediction:
            return 0

        # Store the prediction with a color
        sun_colors = [SUN_COLOR_A, SUN_COLOR_B, SUN_COLOR_C]
        color = sun_colors[min(self.selected_sun, 2)]

        # Evaluate accuracy
        accuracy = self._evaluate_accuracy(simulation)

        self.predictions.append((self.current_prediction.copy(), color, accuracy))
        self.current_prediction = []

        # Cap predictions
        if len(self.predictions) > 10:
            self.predictions = self.predictions[-10:]

        return accuracy

    def _evaluate_accuracy(self, simulation):
        """Evaluate how accurate the prediction is.
        
        Compares the drawn path to the actual future path of the selected sun.
        Returns accuracy from 0-100.
        """
        if len(self.current_prediction) < 5:
            return 10  # Too short to evaluate meaningfully

        sun = simulation.bodies[self.selected_sun]
        
        # Simulate future path
        future_path = [sun.pos.copy()]
        temp_sim = simulation.copy()
        steps = min(len(self.current_prediction), 50)
        
        for _ in range(steps):
            temp_sim.step(simulation.dt * 2)
            future_path.append(temp_sim.bodies[self.selected_sun].pos.copy())

        # Compare prediction to actual path
        total_error = 0
        for i in range(min(len(self.current_prediction), len(future_path))):
            predicted = self.current_prediction[i]
            actual = future_path[i]
            error = np.linalg.norm(predicted - actual)
            total_error += error

        avg_error = total_error / steps

        # Scale: 0 error = 100% accurate, >100px avg error = 0%
        accuracy = max(0, 100 - avg_error)
        return min(100, accuracy)

    def update(self, simulation, frame_count):
        """Auto-evaluate prediction periodically."""
        if self.active and self.current_prediction and \
           frame_count - self.last_eval_time > self.eval_interval:
            accuracy = self.commit_prediction(simulation)
            self.last_eval_time = frame_count
            return accuracy
        return None

    def draw(self, surface, camera):
        """Draw predictions."""
        # Draw committed predictions
        for points, color, accuracy in self.predictions:
            if len(points) < 2:
                continue
            alpha = int(255 * (accuracy / 100) * 0.5)
            for i in range(len(points) - 1):
                p1 = camera.world_to_screen(points[i])
                p2 = camera.world_to_screen(points[i + 1])
                # Brighter = more accurate
                alpha_fade = int(alpha * (i / len(points)) * 0.7)
                c = (*color[:3], alpha_fade)
                pygame.draw.line(
                    surface, c,
                    (int(p1[0]), int(p1[1])),
                    (int(p2[0]), int(p2[1])),
                    max(1, int(3 * (accuracy / 100)))
                )

        # Draw current prediction
        if self.active and len(self.current_prediction) >= 2:
            for i in range(len(self.current_prediction) - 1):
                p1 = camera.world_to_screen(self.current_prediction[i])
                p2 = camera.world_to_screen(self.current_prediction[i + 1])
                alpha = int(180 * (i / max(1, len(self.current_prediction))))
                c = (*self.prediction_color[:3], alpha)
                pygame.draw.line(
                    surface, c,
                    (int(p1[0]), int(p1[1])),
                    (int(p2[0]), int(p2[1])), 2
                )

            # Draw last point
            p = camera.world_to_screen(self.current_prediction[-1])
            pygame.draw.circle(surface, (200, 255, 200, 200), 
                             (int(p[0]), int(p[1])), 6, 2)


class KnowledgeDiscovery:
    """System for discovering knowledge about the three-body problem."""

    def __init__(self):
        self.discoveries = []
        self.recent_discoveries = []
        self.discovery_cooldown = 0

    def try_discover(self, stability, accuracy, civilization):
        """Try to make a new discovery based on conditions."""
        if self.discovery_cooldown > 0:
            self.discovery_cooldown -= 1
            return None

        # Discovery thresholds
        thresholds = [
            (20, "Basic patterns", "You've noticed the suns follow predictable patterns... sometimes."),
            (40, "Gravitational dance", "The three suns influence each other in a complex gravitational waltz."),
            (60, "Stable regions", "There exist narrow bands of stability in the chaos."),
            (80, "Three-body solution", "You're approaching an understanding of the three-body problem!"),
            (95, "Ultimate knowledge", "The Trisolaran civilization thanks you. You have found the solution."),
        ]

        for req, title, desc in thresholds:
            if civilization.knowledge >= req and title not in [d['title'] for d in self.discoveries]:
                self.discoveries.append({
                    'title': title,
                    'description': desc,
                    'knowledge': req,
                    'timestamp': civilization.total_cycles,
                })
                self.recent_discoveries.append(title)
                self.discovery_cooldown = 60
                return title

        return None

    def get_hint(self, accuracy):
        """Provide hints based on prediction accuracy."""
        if accuracy < 20:
            return "The suns move in complex curves. Try following one sun at a time."
        elif accuracy < 50:
            return "Getting better! The gravitational forces affect all three suns simultaneously."
        elif accuracy < 80:
            return "You're learning. Look for patterns repeating over long time periods."
        else:
            return "Impressive! You're close to understanding the three-body problem."