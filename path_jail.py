import os
from urllib.parse import unquote


class PathJail:
    _MAX_DECODE_PASSES = 16

    def __init__(self, root, allow_symlinks=False):
        try:
            root = os.fspath(root)
        except TypeError as exc:
            raise ValueError("root must be an absolute path") from exc

        if (
            not isinstance(root, str)
            or not root
            or "\x00" in root
            or not os.path.isabs(root)
        ):
            raise ValueError("root must be an absolute path")

        self.root = os.path.realpath(root)
        self.allow_symlinks = allow_symlinks

    def _decode(self, path):
        for _ in range(self._MAX_DECODE_PASSES):
            decoded = unquote(path)
            if decoded == path:
                return decoded
            path = decoded

        raise ValueError("path has too many encoding layers")

    def _is_inside_root(self, path):
        try:
            return os.path.commonpath((self.root, path)) == self.root
        except ValueError:
            return False

    def resolve(self, relative):
        if not isinstance(relative, str) or not relative:
            raise ValueError("path must be a non-empty string")

        decoded = self._decode(relative)

        if "\x00" in decoded:
            raise ValueError("path must not contain NUL bytes")
        if "\\" in decoded:
            raise ValueError("path must not contain backslashes")
        if not decoded or os.path.isabs(decoded):
            raise ValueError("path must be relative")

        joined = os.path.join(self.root, decoded)
        if not self._is_inside_root(os.path.normpath(joined)):
            raise ValueError("path escapes the root directory")

        resolved = os.path.realpath(joined)
        if not self.allow_symlinks and not self._is_inside_root(resolved):
            raise ValueError("path escapes the root directory")

        return resolved
