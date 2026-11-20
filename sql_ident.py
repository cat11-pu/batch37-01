import re


_MAX_IDENTIFIER_LENGTH = 63
_IDENTIFIER_PATTERN = re.compile(r'^[A-Za-z_][A-Za-z0-9_"]*$')


class SqlIdentifier:
    def __init__(self, reserved=None):
        if isinstance(reserved, str):
            reserved = (reserved,)
        self.reserved = {word.lower() for word in (reserved or ())}

    def quote(self, name):
        if not isinstance(name, str):
            raise ValueError("identifier must be a string")
        if not name or len(name) > _MAX_IDENTIFIER_LENGTH:
            raise ValueError("identifier length must be between 1 and 63")
        if not _IDENTIFIER_PATTERN.fullmatch(name):
            raise ValueError("identifier contains invalid characters")
        if name.lower() in self.reserved:
            raise ValueError("identifier is a reserved word")

        return '"' + name.replace('"', '""') + '"'

    def qualified(self, schema, table):
        return f"{self.quote(schema)}.{self.quote(table)}"
