from dataclasses import dataclass, field
from threading import Event

@dataclass
class TransferControl:
    """Control flags for transfers."""

    pause: Event = field(default_factory=Event)
    cancel: Event = field(default_factory=Event)
