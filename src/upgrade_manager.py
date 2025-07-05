"""
Upgrade Manager for handling player upgrades and upgrade points.
"""

from typing import Dict, List, Set, Optional
from components.unit_type import UnitType
import json
from pathlib import Path


class UpgradeManager:
    """Manages player upgrades and upgrade points."""
    
    def __init__(self):
        """Initialize the upgrade manager."""
        self.upgrade_points = 1000  # Starting upgrade points for testing
        self.owned_upgrades: Dict[UnitType, Set[str]] = {}
        self.upgrade_data = self._load_upgrade_data()
        
    def _load_upgrade_data(self) -> Dict:
        """Load upgrade data from JSON file."""
        try:
            data_path = Path("data/upgrade_data.json")
            with open(data_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("Warning: upgrade_data.json not found. Using empty upgrade data.")
            return {}
    
    def get_owned_upgrades(self, unit_type: UnitType) -> List[str]:
        """Get list of owned upgrades for a unit type."""
        return list(self.owned_upgrades.get(unit_type, set()))
    
    def get_upgrade_points(self) -> int:
        """Get current upgrade points."""
        return self.upgrade_points
    
    def can_afford_upgrade(self, unit_type: UnitType, upgrade_id: str) -> bool:
        """Check if player can afford an upgrade."""
        unit_key = unit_type.name
        if unit_key not in self.upgrade_data:
            return False
            
        upgrade = self._find_upgrade(unit_key, upgrade_id)
        if not upgrade:
            return False
            
        return self.upgrade_points >= upgrade["cost"]
    
    def has_prerequisites(self, unit_type: UnitType, upgrade_id: str) -> bool:
        """Check if player has all prerequisites for an upgrade."""
        unit_key = unit_type.name
        if unit_key not in self.upgrade_data:
            return False
            
        upgrade = self._find_upgrade(unit_key, upgrade_id)
        if not upgrade:
            return False
            
        owned_upgrades = self.owned_upgrades.get(unit_type, set())
        for prereq in upgrade["prerequisites"]:
            if prereq not in owned_upgrades:
                return False
                
        return True
    
    def purchase_upgrade(self, unit_type: UnitType, upgrade_id: str) -> bool:
        """
        Purchase an upgrade for a unit.
        
        Args:
            unit_type: The unit type to upgrade
            upgrade_id: The ID of the upgrade to purchase
            
        Returns:
            True if purchase was successful, False otherwise
        """
        unit_key = unit_type.name
        if unit_key not in self.upgrade_data:
            return False
            
        upgrade = self._find_upgrade(unit_key, upgrade_id)
        if not upgrade:
            return False
            
        # Check if already owned
        if unit_type in self.owned_upgrades and upgrade_id in self.owned_upgrades[unit_type]:
            return False
            
        # Check prerequisites
        if not self.has_prerequisites(unit_type, upgrade_id):
            return False
            
        # Check if can afford
        if not self.can_afford_upgrade(unit_type, upgrade_id):
            return False
            
        # Purchase the upgrade
        self.upgrade_points -= upgrade["cost"]
        if unit_type not in self.owned_upgrades:
            self.owned_upgrades[unit_type] = set()
        self.owned_upgrades[unit_type].add(upgrade_id)
        
        print(f"Purchased upgrade: {upgrade['name']} for {unit_type.name}")
        return True
    
    def _find_upgrade(self, unit_key: str, upgrade_id: str) -> Optional[Dict]:
        """Find an upgrade by ID."""
        if unit_key not in self.upgrade_data:
            return None
            
        for upgrade in self.upgrade_data[unit_key]["upgrades"]:
            if upgrade["id"] == upgrade_id:
                return upgrade
                
        return None
    
    def add_upgrade_points(self, points: int):
        """Add upgrade points."""
        self.upgrade_points += points
        print(f"Added {points} upgrade points. Total: {self.upgrade_points}")
    
    def get_upgrade_effects(self, unit_type: UnitType) -> Dict:
        """Get combined effects of all owned upgrades for a unit."""
        effects = {}
        owned_upgrades = self.owned_upgrades.get(unit_type, set())
        unit_key = unit_type.name
        
        if unit_key not in self.upgrade_data:
            return effects
            
        for upgrade in self.upgrade_data[unit_key]["upgrades"]:
            if upgrade["id"] in owned_upgrades:
                # Combine effects
                for effect_key, effect_value in upgrade["effect"].items():
                    if effect_key in effects:
                        # For multipliers, multiply them together
                        if "multiplier" in effect_key:
                            effects[effect_key] *= effect_value
                        # For additive effects, add them
                        else:
                            effects[effect_key] += effect_value
                    else:
                        effects[effect_key] = effect_value
        
        return effects


# Global upgrade manager instance
upgrade_manager = UpgradeManager()