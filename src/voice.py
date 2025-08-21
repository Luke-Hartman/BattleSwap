"""Voice lines."""

import random
from typing import Dict, List
from components.unit_type import UnitType
from events import PLAY_VOICE, PlayVoiceEvent, emit_event

class VoiceOptions:
    """A mapping from unit type to a list of voice lines.
    
    Avoids playing the same voice line twice in a row."""

    def __init__(self, options: Dict[UnitType, List[str]]):
        self.options = options
        for unit_type in self.options:
            if len(self.options[unit_type]) < 2:
                raise ValueError(f"Need at least 2 sounds for {unit_type}")
        self.last_played: Dict[UnitType, str] = {}
    
    def __getitem__(self, unit_type: UnitType) -> str:
        options = self.options[unit_type].copy()
        previous_voice = self.last_played.get(unit_type, None)
        if previous_voice:
            options.remove(previous_voice)
        selected_line = random.choice(options)
        self.last_played[unit_type] = selected_line
        return selected_line

introductions = VoiceOptions({
    # UnitType.CORE_DUELIST: [
    #     f"core_duelist_intro{i + 1}.wav" for i in range(3)
    # ]
})
def play_intro(unit_type: UnitType) -> None:
    """Play the intro voice line for a unit."""
    try:
        emit_event(PLAY_VOICE, event=PlayVoiceEvent(filename=introductions[unit_type], force=False))
    except KeyError:
        pass

deaths = VoiceOptions({
    # UnitType.CORE_DUELIST: [
    #     f"core_duelist_death{i + 1}.wav" for i in range(4)
    # ]
})
def play_death(unit_type: UnitType) -> None:
    """Play the death voice line for a unit."""
    try:
        emit_event(PLAY_VOICE, event=PlayVoiceEvent(filename=deaths[unit_type], force=False))
    except KeyError:
        pass

kill_voices = VoiceOptions({
    UnitType.ORC_BERSERKER: [
        "orc_berserker_kill.wav",
        "orc_berserker_blood.wav",
        "orc_berserker_death.wav"
    ],
    UnitType.ORC_WARRIOR: [
        f"orc_kill_sound{i}.wav" for i in range(1, 5)
    ],
    UnitType.ORC_WARCHIEF: [
        "orc_warlord_laugh.wav",
        "orc_warlord_pathetic.wav",
        "orc_warlord_unstoppable.wav",
        "orc_warlord_too_late.wav"
    ]
})
def play_kill(unit_type: UnitType) -> None:
    """Play the kill voice line for a unit."""
    try:
        emit_event(PLAY_VOICE, event=PlayVoiceEvent(filename=kill_voices[unit_type], force=False))
    except KeyError:
        pass