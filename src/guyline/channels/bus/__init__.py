"""Message bus module for decoupled channel-agent communication."""

from guyline.channels.bus.events import InboundMessage, OutboundMessage
from guyline.channels.bus.queue import MessageBus

__all__ = ["InboundMessage", "MessageBus", "OutboundMessage"]
