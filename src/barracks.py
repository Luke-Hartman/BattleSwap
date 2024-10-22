"""Barracks module for managing units between battles."""

import json
from typing import Dict
from entities.units import UnitType

class Barracks:
    """A container for units between battles."""

    def __init__(self, save_file: str = "barracks_save.json"):
        """Initialize the Barracks."""
        self.units: Dict[UnitType, int] = {unit_type: 0 for unit_type in UnitType}
        self.save_file = save_file
        self.load()

    def exchange_units(self, add_units: Dict[UnitType, int], remove_units: Dict[UnitType, int]) -> bool:
        """
        Exchange units in the barracks.

        Args:
            add_units: Dictionary of {UnitType: count} to add.
            remove_units: Dictionary of {UnitType: count} to remove.

        Returns:
            bool: True if the exchange was successful, False otherwise.
        """
        temp_units = self.units.copy()

        for unit_type, count in add_units.items():
            temp_units[unit_type] += count

        for unit_type, count in remove_units.items():
            if temp_units[unit_type] < count:
                return False
            temp_units[unit_type] -= count

        self.units = temp_units
        self.save()
        return True

    def get_contents(self) -> Dict[UnitType, int]:
        """
        Get the contents of the barracks.

        Returns:
            Dict[UnitType, int]: A dictionary with the count for each unit type.
        """
        return self.units.copy()

    def save(self) -> None:
        """Save the current state of the barracks to disk."""
        with open(self.save_file, 'w') as f:
            json.dump({unit_type.name: count for unit_type, count in self.units.items()}, f)

    def load(self) -> None:
        """Load the state of the barracks from disk."""
        try:
            with open(self.save_file, 'r') as f:
                data = json.load(f)
                self.units = {UnitType[unit_type]: count for unit_type, count in data.items()}
        except FileNotFoundError:
            # If the file doesn't exist, we'll use the default empty barracks
            pass
