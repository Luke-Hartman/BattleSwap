"""Simple timing system for the game."""

from fractions import Fraction
from settings import settings, save_settings

# Available game speeds
GAME_SPEEDS = [
    Fraction(1, 4),
    Fraction(1, 2),
    Fraction(1, 1),
    Fraction(3, 2),
    Fraction(2, 1),
    Fraction(3, 1),
    Fraction(4, 1),
]

# Game state
_is_paused: bool = False
_in_battle: bool = False
_global_clock: float = 0.0


def get_current_speed() -> Fraction:
    """Get the current game speed as a Fraction."""
    # Find the closest speed in our predefined list to the settings value
    saved_speed = settings.GAME_SPEED if settings else 1.0
    saved_fraction = Fraction(saved_speed).limit_denominator()
    
    if saved_fraction in GAME_SPEEDS:
        return saved_fraction
    else:
        # Find closest speed in the list
        return min(GAME_SPEEDS, key=lambda x: abs(float(x) - saved_speed))


def increase_game_speed() -> None:
    """Increase the game speed."""
    current_speed = get_current_speed()
    current_index = GAME_SPEEDS.index(current_speed)
    new_index = min(current_index + 1, len(GAME_SPEEDS) - 1)
    new_speed = GAME_SPEEDS[new_index]
    
    if settings:
        settings.GAME_SPEED = float(new_speed)
        save_settings()


def decrease_game_speed() -> None:
    """Decrease the game speed."""
    current_speed = get_current_speed()
    current_index = GAME_SPEEDS.index(current_speed)
    new_index = max(current_index - 1, 0)
    new_speed = GAME_SPEEDS[new_index]
    
    if settings:
        settings.GAME_SPEED = float(new_speed)
        save_settings()


def toggle_pause() -> None:
    """Toggle the pause state."""
    global _is_paused
    _is_paused = not _is_paused


def pause() -> None:
    """Pause the game."""
    global _is_paused
    _is_paused = True


def resume() -> None:
    """Resume the game."""
    global _is_paused
    _is_paused = False


def is_paused() -> bool:
    """Check if the game is paused."""
    return _is_paused


def enter_battle() -> None:
    """Enter battle mode."""
    global _in_battle
    _in_battle = True


def leave_battle() -> None:
    """Leave battle mode."""
    global _in_battle
    _in_battle = False


def is_in_battle() -> bool:
    """Check if in battle mode."""
    return _in_battle


def get_dt() -> float:
    """Get delta time for combat simulation.
    
    This controls how much time passes for combat each frame.
    This is either 1/60 or 0, depending on whether the game is paused.
    Keeping this at 1/60 is critical for deterministic gameplay.
    """
    if _in_battle and _is_paused:
        return 0.0
    return 1.0 / 60.0


def get_max_fps() -> float:
    """Get the maximum FPS for the game loop.
    
    This indirectly controls the rate of the game through the max FPS.
    """
    if _is_paused or not _in_battle:
        return 60.0
    return 60.0 * float(get_current_speed())


def get_global_clock() -> float:
    """Get the global game clock."""
    return _global_clock


def tick() -> None:
    """Advance the global clock."""
    global _global_clock
    _global_clock += get_dt()