"""The time manager is responsible for managing the rate of time in the game."""

from fractions import Fraction

class TimeManager:

    def __init__(self):
        self._game_speed = Fraction(1, 1)
        self.game_speeds = [
            Fraction(1, 4),
            Fraction(1, 2),
            Fraction(1, 1),
            Fraction(3, 2),
            Fraction(2, 1),
            Fraction(3, 1),
            Fraction(4, 1),
        ]
        self._is_paused = False
        self._in_battle = False
        self._global_clock = 0

    def increase_game_speed(self):
        current_index = self.game_speeds.index(self._game_speed)
        new_index = min(current_index + 1, len(self.game_speeds) - 1)
        self._game_speed = self.game_speeds[new_index]
    
    def decrease_game_speed(self):
        current_index = self.game_speeds.index(self._game_speed)
        new_index = max(current_index - 1, 0)
        self._game_speed = self.game_speeds[new_index]
    
    def toggle_pause(self):
        self._is_paused = not self._is_paused

    def pause(self):
        self._is_paused = True
    
    def resume(self):
        self._is_paused = False

    def enter_battle(self):
        self._in_battle = True

    def leave_battle(self):
        self._in_battle = False

    @property
    def dt(self):
        """This controls how much time passes for combat each frame.
        
        This is either 1/60 or 0, depending on whether the game is paused.
        
        Keeping this at 1/60 is critical for deterministic gameplay.
        """
        if self._in_battle and self._is_paused:
            return 0
        return 1/60

    @property
    def max_fps(self):
        """This indirectly controls the rate of the game through the max FPS."""
        if self._is_paused or not self._in_battle:
            return 60
        return 60 * self._game_speed

    @property
    def global_clock(self):
        return self._global_clock

    def tick(self):
        self._global_clock += self.dt

time_manager = TimeManager()
