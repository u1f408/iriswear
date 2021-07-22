import time
import platform


class SpeechDispatcher:
    def __init__(self):
        self.queue = []
        self.running = False

        self._platform = platform.system()
        init_fn = getattr(self, f"{self._platform}_init", None)
        if callable(init_fn):
            init_fn()

    def push(self, text: str, **kwargs):
        self.queue.append({
            'text': text,
            **kwargs,
        })

    def run(self):
        self.running = True
        while self.running:
            self.single_iter()
            time.sleep(0.1)
        
    def shutdown(self):
        self.running = False

    def single_iter(self):
        if len(self.queue) > 0:
            obj = self.queue.pop(0)
            if isinstance(obj, dict):
                if 'tone' in obj and obj['tone'] is not None:
                    # TODO: tone
                    pass

                if 'text' in obj and obj['text'] is not None:
                    self.speak(obj['text'])

            elif isinstance(obj, str):
                self.speak(obj)

    def speak(self, text: str):
        speech_fn = getattr(self, f"{self._platform}_speak", None)
        if callable(speech_fn):
            return speech_fn(text)

        # TODO: fallbacks
        raise RuntimeError("Unknown platform to dispatch speech")

    def Darwin_init(self):
        from AppKit import NSSpeechSynthesizer
        self._voice_engine = NSSpeechSynthesizer.alloc().init()
        
    def Darwin_speak(self, text: str):
        self._voice_engine.startSpeakingString_(text)

        while not self._voice_engine.isSpeaking():
            time.sleep(0.1)
        while self._voice_engine.isSpeaking():
            time.sleep(0.1)
