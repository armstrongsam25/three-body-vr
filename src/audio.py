"""Procedural audio generation for Three Body VR.

Generates sounds programmatically since we can't rely on audio files.
Uses pygame's mixer to create sounds from raw waveforms.
"""

import math
import struct
import pygame
import numpy as np


class AudioEngine:
    """Procedural audio engine for game sounds."""

    def __init__(self):
        self.sounds = {}
        self.music_playing = False
        self.volume = 0.5
        self.enabled = True

        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.initialized = True
        except Exception:
            self.initialized = False
            print("Audio not available (no sound device)")

        if self.initialized:
            self._generate_sounds()
            self._generate_music()

    def _generate_sine_wave(self, frequency, duration, volume=0.3, fade_out=True):
        """Generate a sine wave as raw audio data."""
        sample_rate = 22050
        n_samples = int(sample_rate * duration)
        samples = []

        for i in range(n_samples):
            t = i / sample_rate
            # Simple sine with envelope
            envelope = 1.0
            if fade_out:
                envelope = max(0, 1.0 - t / duration)

            # Add some harmonics for richer sound
            value = (
                math.sin(2 * math.pi * frequency * t) * 0.6 +
                math.sin(2 * math.pi * frequency * 2 * t) * 0.2 +
                math.sin(2 * math.pi * frequency * 3 * t) * 0.1
            ) * volume * envelope

            # Convert to 16-bit int
            sample = int(max(-32767, min(32767, value * 32767)))
            samples.append(sample)

        # Pack as stereo 16-bit
        raw = struct.pack(f'<{len(samples)*2}h', *[
            val for s in samples for val in (s, s)
        ])
        return raw

    def _generate_noise(self, duration, volume=0.2):
        """Generate white noise (for chaos era)."""
        sample_rate = 22050
        n_samples = int(sample_rate * duration)
        samples = []

        for i in range(n_samples):
            t = i / sample_rate
            envelope = max(0, 1.0 - t / duration) if duration > 0.1 else 0.5
            value = (np.random.random() * 2 - 1) * volume * envelope
            sample = int(max(-32767, min(32767, value * 32767)))
            samples.append(sample)

        raw = struct.pack(f'<{len(samples)*2}h', *[
            val for s in samples for val in (s, s)
        ])
        return raw

    def _make_sound(self, data):
        """Create a pygame Sound from raw data."""
        try:
            return pygame.mixer.Sound(buffer=data)
        except Exception:
            return None

    def _generate_sounds(self):
        """Generate all game sounds procedurally."""
        # Era transition sound (rising tone)
        era_trans = self._generate_sine_wave(220, 0.8, 0.4) + \
                    self._generate_sine_wave(440, 0.4, 0.3)
        self.sounds['era_transition'] = self._make_sound(era_trans)

        # Stable era ambient (low hum)
        stable_hum = self._generate_sine_wave(110, 2.0, 0.15, fade_out=False)
        self.sounds['stable_hum'] = self._make_sound(stable_hum)

        # Chaos era sound (noise + dissonance)
        chaos_raw = self._generate_noise(1.5, 0.2)
        chaos_dissonant = self._generate_sine_wave(180, 1.0, 0.15)
        chaos_total = chaos_raw[:len(chaos_dissonant)] if len(chaos_dissonant) < len(chaos_raw) else chaos_dissonant[:len(chaos_raw)]
        self.sounds['chaos_noise'] = self._make_sound(chaos_total)

        # Collapse sound (descending)
        collapse = bytes()
        for freq in [440, 330, 220, 110]:
            collapse += self._generate_sine_wave(freq, 0.15, 0.4)
        self.sounds['collapse'] = self._make_sound(collapse)

        # Knowledge gain (ascending)
        know = bytes()
        for freq in [330, 440, 660, 880]:
            know += self._generate_sine_wave(freq, 0.1, 0.25)
        self.sounds['knowledge'] = self._make_sound(know)

        # Milestone (triumphant)
        milestone = bytes()
        for freq in [440, 554, 660, 880, 1100]:
            milestone += self._generate_sine_wave(freq, 0.12, 0.3)
        self.sounds['milestone'] = self._make_sound(milestone)

        # Click sound
        click = self._generate_sine_wave(800, 0.05, 0.3, fade_out=False)
        self.sounds['click'] = self._make_sound(click)

        # Prediction mode activation
        predict = self._generate_sine_wave(330, 0.1, 0.25) + \
                  self._generate_sine_wave(660, 0.3, 0.2)
        self.sounds['predict'] = self._make_sound(predict)

    def _generate_music(self):
        """Generate procedural ambient music.

        Creates a simple pentatonic melody loop for background music.
        """
        # Pentatonic scale frequencies
        scale = [131, 147, 165, 196, 220, 262, 294, 330, 392, 440]
        music_raw = bytes()

        # Simple ambient sequence
        sequence = [scale[i] for i in [0, 2, 4, 7, 9, 7, 4, 2, 0, 2, 4, 5, 7, 9, 4, 0]]
        note_duration = 0.4

        for freq in sequence:
            music_raw += self._generate_sine_wave(freq, note_duration, 0.15)

        self.music_data = music_raw

    def play(self, name, volume_override=None):
        """Play a named sound."""
        if not self.initialized or not self.enabled:
            return

        sound = self.sounds.get(name)
        if sound:
            vol = volume_override if volume_override is not None else self.volume
            sound.set_volume(vol)
            sound.play()

    def play_era_ambient(self, era):
        """Play ambient sound for current era."""
        if not self.initialized or not self.enabled:
            return

        # Stop any current ambient
        pygame.mixer.stop()

        if era == "stable":
            self.play('stable_hum', 0.08)
        elif era == "chaotic":
            self.play('chaos_noise', 0.12)

    def start_music(self):
        """Start procedural background music loop."""
        if not self.initialized or not self.enabled or self.music_playing:
            return

        try:
            sound = pygame.mixer.Sound(buffer=self.music_data)
            sound.set_volume(0.1)
            sound.play(loops=-1)  # Loop indefinitely
            self.music_playing = True
        except Exception:
            pass

    def stop_music(self):
        """Stop background music."""
        if self.initialized and self.music_playing:
            pygame.mixer.stop()
            self.music_playing = False

    def toggle_mute(self):
        """Toggle audio on/off."""
        self.enabled = not self.enabled
        if not self.enabled:
            pygame.mixer.stop()
        return self.enabled