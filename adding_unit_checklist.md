When adding a new unit, make all of the following changes:

- [ ] In src/components/unit_type.py
    - Add the unit's type to the `UnitType` enum.
- [ ] In src/game_constants.py
    - Add the unit's constants to the GameConstants class.
- [ ] In data/game_constants.json
    - Add the unit's constants matching the GameConstants class.
- [ ] In src/entities/units.py
    - Create a new function for the unit (in alphabetical order) matching the function in create_unit.
        - If instructed to make a new unit work similarly to an existing unit, use the existing unit's function and stats as a reference, but don't re-use any of the existing unit's code. For example, if re-using the core swordsman's sprite and stats, still create new entries for the new unit's sprite and stats and use those instead of the core swordsman's. Unless instructed otherwise, use the same numerical values for the new unit as the existing unit.
    - Add the unit's type to the `unit_theme_ids` dictionary.
    - Add the unit's type to the `unit_values` dictionary.
    - Add the unit's type to the `unit_icon_surfaces` dictionary.
    - Add the unit's type to the `unit_filenames` dictionary.
    - Add the unit's type to the `unit_icon_paths` dictionary.
    - Add the unit's function to the `create_unit` function.
- [ ] In data/theme.json
    - Add the unit's icon to the theme.
- [ ] In src/stats_cards.py
    - Add the unit's stats to the stats_cards function.

Be sure to add enum/dictionary values in alphabetical order, if the existing values are already in alphabetical order.

Additionally, note that a unit's name is always in the format of `<FACTION>_<NAME>`. For example, "CRUSADER_SOLDIER" or "core_swordsman". This makes it easier to find units in the code, especially when things are alphabetically ordered.

Finally, before you are finished, review this checklist to make sure you have followed all of the instructions.