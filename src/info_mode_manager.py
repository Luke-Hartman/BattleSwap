class InfoModeManager:
    def __init__(self):
        import sys
        self._info_mode = False
        if sys.platform == 'darwin':
            self._modifier_key = 'Cmd'
        else:
            self._modifier_key = 'Alt'

    @property
    def info_mode(self):
        return self._info_mode

    @info_mode.setter
    def info_mode(self, value: bool):
        self._info_mode = value

    @property
    def modifier_key(self):
        return self._modifier_key

info_mode_manager = InfoModeManager() 