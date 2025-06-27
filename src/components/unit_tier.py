"""Unit tier component for tracking unit upgrade levels."""

from enum import Enum, auto
from typing import Optional


class UnitTier(Enum):
    """Enumeration for unit tiers."""
    BASIC = "BASIC"
    ADVANCED = "ADVANCED"
    ELITE = "ELITE"

    def next_tier(self) -> 'UnitTier':
        """Get the next tier for upgrading."""
        if self == UnitTier.BASIC:
            return UnitTier.ADVANCED
        elif self == UnitTier.ADVANCED:
            return UnitTier.ELITE
        else:
            return UnitTier.ELITE  # Already at max tier

    def can_upgrade(self) -> bool:
        """Check if this tier can be upgraded."""
        return self != UnitTier.ELITE

    def get_upgrade_cost_type(self) -> Optional[str]:
        """Get the currency type needed to upgrade from this tier."""
        if self == UnitTier.BASIC:
            return "advanced_credits"
        elif self == UnitTier.ADVANCED:
            return "elite_credits"
        else:
            return None  # Can't upgrade from ELITE