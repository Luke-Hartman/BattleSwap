"""UnusableCorpse component for Battle Swap.

This component indicates that an entity's corpse cannot be used by effects
like zombie infection.
"""


class UnusableCorpse:
    """Component indicating that an entity's corpse cannot be used by effects.
    
    This is a marker component - it has no data, its presence indicates
    the entity's corpse cannot be used by effects like zombie infection.
    """
    pass

