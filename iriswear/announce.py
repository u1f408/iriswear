import json
import logging
import paho.mqtt.client as mqtt

from . import cli
from .config import current_config
from .speech import SpeechDispatcher


class Announcer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.speech = SpeechDispatcher()

        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.mqtt_on_connect
    
    def run(self):
        mqtt_host, mqtt_port = current_config.mqtt_host_port
        self.logger.info(f"Connecting to MQTT: {mqtt_host}:{mqtt_port}")
        self.mqtt_client.connect_async(mqtt_host, port=mqtt_port)
        self.mqtt_client.loop_start()
        
        self.logger.info("Starting SpeechDispatcher…")
        self.speech.run()
    
    def mqtt_on_connect(self, client, userdata, flags, rc):
        self.logger.info(f"mqtt_on_connect: rc {repr(rc)}")
        self.mqtt_client.message_callback_add(current_config.mqtt_topic['announce'], self.mqtt_on_message)
        self.mqtt_client.subscribe(current_config.mqtt_topic['announce'])
        
    def mqtt_on_message(self, client, userdata, message):
        if message.topic == current_config.mqtt_topic['announce']:
            self.logger.debug(f"mqtt_on_message: {repr(message.topic)} {repr(message.payload)}")
            self.handle_message(message.payload)
    
    def handle_message(self, payload):
        try:
            payload = json.loads(payload)
        except:
            pass
        
        arguments = {}
        text = tone = None

        if isinstance(payload, dict):
            if 'text' in payload:
                text = payload['text']
                del payload['text']

            if 'tone' in payload:
                tone = payload['tone']
                del payload['tone']

            arguments = payload
            
        elif isinstance(payload, str):
            text = payload
            
        elif isinstance(payload, bytes):
            text = payload.decode('utf-8')
        
        else:
            self.logger.warn(f"Unknown payload type {repr(type(payload))}")
            return

        self.logger.info(f"Message: {repr(text)} tone:{repr(tone)} args:{repr(arguments)}")
        self.speech.push(text, tone=tone, **arguments)


@cli.subcommand()
def announce(args):
    """Start the text-to-speech announcer
    """
    
    Announcer().run()
