from typing import Dict, Optional
import pygame
import os
from pydispatch import dispatcher
from events import PLAY_SOUND, PlaySoundEvent, STOP_ALL_SOUNDS, StopAllSoundsEvent, CHANGE_MUSIC, ChangeMusicEvent, PLAY_VOICE, PlayVoiceEvent
from game_constants import gc

class SoundHandler:
    """Manages loading and playing of sound effects."""
    
    def __init__(self) -> None:
        """Initialize the sound manager."""
        pygame.mixer.init()
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.voices: Dict[str, pygame.mixer.Sound] = {}
        self._load_sounds()
        self._load_voices()
        dispatcher.connect(self.handle_play_sound, signal=PLAY_SOUND)
        dispatcher.connect(self.handle_play_voice, signal=PLAY_VOICE)
        dispatcher.connect(self.handle_stop_all_sounds, signal=STOP_ALL_SOUNDS)
        dispatcher.connect(self.handle_change_music, signal=CHANGE_MUSIC)
        self._current_music: Optional[str] = None
        # Reserve one channel for voice
        self._voice_channel = pygame.mixer.Channel(0)
        pygame.mixer.set_reserved(1)

    def _load_sounds(self) -> None:
        """Load all sound effects from the assets directory."""
        sound_dir = os.path.join("assets", "sounds")
        for filename in os.listdir(sound_dir):
            if filename.endswith(".wav"):
                path = os.path.join(sound_dir, filename)
                self.sounds[filename] = pygame.mixer.Sound(path)

    def _load_voices(self) -> None:
        """Load all voice lines from the assets directory."""
        voice_dir = os.path.join("assets", "voices")
        for filename in os.listdir(voice_dir):
            if filename.endswith(".wav"):
                path = os.path.join(voice_dir, filename)
                self.voices[filename] = pygame.mixer.Sound(path)

    def handle_play_sound(self, event: PlaySoundEvent) -> None:
        """Play a sound effect by name."""
        sound = self.sounds[event.filename]
        sound.set_volume(event.volume * gc.SOUND_VOLUME)
        sound.play()

    def handle_play_voice(self, event: PlayVoiceEvent) -> None:
        """Play a voice line by name."""
        if self._voice_channel.get_busy() and not event.force:
            return
        voice = self.voices[event.filename]
        voice.set_volume(gc.VOICE_VOLUME)
        self._voice_channel.play(voice)

    def handle_stop_all_sounds(self, event: StopAllSoundsEvent) -> None:
        """Stop all currently playing sound effects."""
        for sound in self.sounds.values():
            sound.fadeout(1000)
        for voice in self.voices.values():
            voice.fadeout(1000)

    def handle_change_music(self, event: ChangeMusicEvent) -> None:
        """Change the music to the given filename."""
        if event.filename == self._current_music:
            return
        pygame.mixer.music.load(os.path.join("assets", "music", event.filename))
        pygame.mixer.music.play(loops=-1, fade_ms=1000)
        pygame.mixer.music.set_volume(gc.MUSIC_VOLUME)
        self._current_music = event.filename
