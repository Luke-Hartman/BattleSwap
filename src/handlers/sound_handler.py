from typing import Dict, Optional
import pygame
import os
from pydispatch import dispatcher
from events import PLAY_SOUND, PlaySoundEvent, STOP_ALL_SOUNDS, StopAllSoundsEvent, CHANGE_MUSIC, ChangeMusicEvent
from game_constants import gc

class SoundHandler:
    """Manages loading and playing of sound effects."""
    
    def __init__(self) -> None:
        """Initialize the sound manager."""
        pygame.mixer.init()
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.music: Dict[str, pygame.mixer.Sound] = {}
        self._load_sounds()
        self._load_music()
        dispatcher.connect(self.handle_play_sound, signal=PLAY_SOUND)
        dispatcher.connect(self.handle_stop_all_sounds, signal=STOP_ALL_SOUNDS)
        dispatcher.connect(self.handle_change_music, signal=CHANGE_MUSIC)
        self._current_music: Optional[pygame.mixer.Sound] = None

    def _load_sounds(self) -> None:
        """Load all sound effects from the assets directory."""
        sound_dir = os.path.join("assets", "sounds")
        for filename in os.listdir(sound_dir):
            if filename.endswith(".wav"):
                path = os.path.join(sound_dir, filename)
                self.sounds[filename] = pygame.mixer.Sound(path)

    def _load_music(self) -> None:
        """Load a music file from the assets directory."""
        music_dir = os.path.join("assets", "music")
        for filename in os.listdir(music_dir):
            if filename.endswith(".wav"):
                path = os.path.join(music_dir, filename)
                self.music[filename] = pygame.mixer.Sound(path)

    def handle_play_sound(self, event: PlaySoundEvent) -> None:
        """Play a sound effect by name."""
        if event.sound_effect.filename in self.sounds:
            sound = self.sounds[event.sound_effect.filename]
            sound.set_volume(event.sound_effect.volume * gc.SOUND_VOLUME)
            sound.play()
        else:
            raise ValueError(f"Sound effect {event.sound_effect.filename} not found")

    def handle_stop_all_sounds(self, event: StopAllSoundsEvent) -> None:
        """Stop all currently playing sound effects."""
        for sound in self.sounds.values():
            sound.fadeout(1000)

    def handle_change_music(self, event: ChangeMusicEvent) -> None:
        """Change the music to the given filename."""
        if event.music_filename in self.music:
            new_music = self.music[event.music_filename]
            if new_music is self._current_music:
                return
            if self._current_music is not None:
                self._current_music.fadeout(1000)
            new_music.play(loops=-1, fade_ms=1000)
            new_music.set_volume(gc.MUSIC_VOLUME * 0.5)
            self._current_music = new_music
        else:
            raise ValueError(f"Music {event.music_filename} not found")
