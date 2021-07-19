import types

from pathlib import Path


class Config:
    def __init__(self):
        self.raw_values = {}

    def __getitem__(self, *args):
        return self.raw_values.__getitem__(*args)

    def __setitem__(self, *args):
        return self.raw_values.__setitem__(*args)

    def load_from_file(self, path):
        d = types.ModuleType("config")
        d.__file__ = str(path)

        with open(path, 'rb') as fh:
            exec(compile(fh.read(), str(path), "exec"), d.__dict__)

        self.load_from_object(d)

    def load_from_object(self, obj):
        self.raw_values = dict(obj.__dict__)


current_config = Config()