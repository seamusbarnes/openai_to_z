# config.py
import yaml

class Config:

    def __init__(self, filepath):
        
        with open(filepath) as f:
            self._data = yaml.safe_load(f)

    def __getitem__(self, key):
        return self._data[key]
    
    def get(self, key, default=None):
        return self._data.get(key, default)
    
    def to_dict(self):
        return self._data