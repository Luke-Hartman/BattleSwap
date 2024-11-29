from typing import Dict
import pygame
import os
from pydispatch import dispatcher
from events import PLAY_SOUND, PlaySoundEvent, SoundEffect
from game_constants import gc

class SoundHandler:
    """Manages loading and playing of sound effects."""
    
    def __init__(self) -> None:
        """Initialize the sound manager."""
        pygame.mixer.init()
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self._load_sounds()
        dispatcher.connect(self.handle_play_sound, signal=PLAY_SOUND)

    def _load_sounds(self) -> None:
        """Load all sound effects from the assets directory."""
        sound_dir = os.path.join("assets", "sounds")
        for filename in os.listdir(sound_dir):
            if filename.endswith(".wav"):
                path = os.path.join(sound_dir, filename)
                self.sounds[filename] = pygame.mixer.Sound(path)
    
    def handle_play_sound(self, event: PlaySoundEvent) -> None:
        """Play a sound effect by name."""
        if event.sound_effect.filename in self.sounds:
            sound = self.sounds[event.sound_effect.filename]
            sound.set_volume(event.sound_effect.volume * gc.SOUND_VOLUME)
            sound.play()
        else:
            raise ValueError(f"Sound effect {event.sound_effect.filename} not found")

    def stop_all_sounds(self) -> None:
        """Stop all currently playing sound effects."""
        for sound in self.sounds.values():
            sound.fadeout(1000)