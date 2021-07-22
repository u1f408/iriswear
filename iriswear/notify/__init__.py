import time
import json
import logging
import paho.mqtt.client as mqtt

from .. import cli
from ..config import current_config


class Notifier:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

        self.notifiers = []
        self.queue = []
        self.running = False

        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.mqtt_on_connect

    def add_notifier(self, name: str, fn):
        self.logger.debug(f"Registering notifier {repr(name)}: {repr(fn)}")
        self.notifiers.append((name, fn))

    def push(self, text: str, **kwargs):
        self.queue.append({
            'message': text,
            **kwargs,
        })

    def run(self):
        mqtt_host, mqtt_port = current_config.mqtt_host_port
        self.logger.info(f"Connecting to MQTT: {mqtt_host}:{mqtt_port}")
        self.mqtt_client.connect_async(mqtt_host, port=mqtt_port)
        self.mqtt_client.loop_start()
        
        try:
            self.logger.info("Notifier started")
            self.running = True
            while self.running:
                self.single_iter()
                time.sleep(0.1)

        except KeyboardInterrupt:
            self.logger.warn("Shutting down…")
            self.mqtt_client.disconnect()
            self.shutdown()

    def shutdown(self):
        self.running = False

    def single_iter(self):
        if len(self.queue) > 0:
            obj = self.queue.pop(0)
            if not isinstance(obj, dict):
                return
                
            message = obj['message']
            del obj['message']
            
            self.logger.info(f"Notification: {repr(message)} {repr(obj)}")

            for (name, fn) in self.notifiers:
                try:
                    fn(self, message, **obj)
                except Exception as ex:
                    self.logger.warn(f"Notifier {name} raised: {repr(ex)}")

    def mqtt_on_connect(self, client, userdata, flags, rc):
        self.logger.info(f"mqtt_on_connect: rc {repr(rc)}")
        self.mqtt_client.message_callback_add(current_config.mqtt_topic['notify'], self.mqtt_on_message)
        self.mqtt_client.subscribe(current_config.mqtt_topic['notify'])
        
    def mqtt_on_message(self, client, userdata, message):
        if message.topic == current_config.mqtt_topic['notify']:
            self.logger.debug(f"mqtt_on_message: {repr(message.topic)} {repr(message.payload)}")
            self.handle_message(message.payload)
    
    def handle_message(self, payload):
        try:
            payload = json.loads(payload)
        except Exception as ex:
            self.logger.warn(f"Failed to parse notify payload: {repr(ex)}")
            return
        
        if not 'message' in payload or payload['message'] is None:
            self.logger.warn(f"No message in payload, ignoring")
            return

        message = payload['message']
        del payload['message']
        
        title = None
        if 'title' in payload and payload['title'] is not None:
            title = payload['title']
            del payload['title']
        
        priority = 0
        if 'priority' in payload and payload['priority'] is not None:
            priority = payload['priority']
            del payload['priority']

        self.push(message, title=title, priority=priority, extra=payload)


@cli.subcommand()
def notify(args):
    """Start the notification daemon
    """
    
    notifier = Notifier()

    from .announce import notify_announce
    notifier.add_notifier("announce", notify_announce)
    
    notifier.run()
