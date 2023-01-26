import os

class Database:
    def __init__(self, name):
        self.name = name

        # Set cache directory
        cache_root = os.getenv("XDG_CACHE_HOME",
            os.path.join(os.path.expanduser("~"), ".cache"))
        self.cache = os.path.join(cache_root, "curator", name)
        os.makedirs(self.cache, exist_ok=True)
