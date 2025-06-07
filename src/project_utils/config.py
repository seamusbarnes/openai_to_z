import yaml

class ConfigNamespace:
    def __init__(self, d):
        for k, v in d.items():
            if isinstance(v, dict):
                v = ConfigNamespace(v)
            setattr(self, k, v)

    def __getitem__(self, key):
        return getattr(self, key)

    def __repr__(self):
        return f"{self.__class__.__name__}({vars(self)})"

class Config:
    def __init__(self, filepath):
        with open(filepath) as f:
            data = yaml.safe_load(f)
        self._data = data
        # All keys are attributes of self._ns, not Config itself!
        self._ns = ConfigNamespace(data)

    def __getattr__(self, name):
        # This is only called *if* regular attribute lookup fails,
        # so it *only* finds "paths", "dataset", etc from self._ns
        return getattr(self._ns, name)

    def get(self, *keys, default=None):
        obj = self._ns
        for k in keys:
            try:
                obj = getattr(obj, k)
            except AttributeError:
                return default
        return obj
    
    def dump_dict(self):
        """Return the underlying dictionary."""
        return self._data