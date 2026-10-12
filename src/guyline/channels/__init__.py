"""Guyline channels subsystem.

Provides a message-bus architecture for integrating chat platforms
(Telegram, Discord, Slack, etc.) with the Guyline query engine.

Usage::

    from guyline.channels import BaseChannel, ChannelManager, MessageBus
"""

from guyline.channels.bus.events import InboundMessage, OutboundMessage
from guyline.channels.bus.queue import MessageBus
from guyline.channels.impl.base import BaseChannel
from guyline.channels.impl.manager import ChannelManager

__all__ = [
    "BaseChannel",
    "ChannelManager",
    "InboundMessage",
    "MessageBus",
    "OutboundMessage",
]
