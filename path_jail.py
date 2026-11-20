class PathJail:
    def __init__(self, root, allow_symlinks=False):
        self.root = root
        self.allow_symlinks = allow_symlinks

    def resolve(self, relative):
        return None
