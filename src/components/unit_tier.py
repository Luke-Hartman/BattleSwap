from enum import Enum

class UnitTier(Enum):
    BASIC = "Basic"
    ADVANCED = "Advanced"
    ELITE = "Elite"

class UnitTierComponent:
    def __init__(self, tier: UnitTier):
        self.tier = tier