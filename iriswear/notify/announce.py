import json

from . import Notifier
from ..config import current_config


def notify_announce(
    notifier: Notifier,
    message: str,
    title: str = None,
    priority: int = 0,
    extra = None,
):
    if priority >= current_config.notify_announce_priority:
        text = message
        if title is not None:
            text = f"{title} - {text}"

        notifier.mqtt_client.publish(
            current_config.mqtt_topic['announce'],
            text,
        )
