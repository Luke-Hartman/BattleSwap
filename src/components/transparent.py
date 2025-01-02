from dataclasses import dataclass


@dataclass
class Transparency:
    """A component that makes an entity transparent."""

    alpha: int
