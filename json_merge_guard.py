class JsonMergeGuard:
    def __init__(self, max_depth=8, max_keys=100):
        self.max_depth = max_depth
        self.max_keys = max_keys

    def merge(self, base_json, patch_json):
        return {}
