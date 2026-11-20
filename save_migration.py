import copy


class SaveMigrator:
    def __init__(self, migrations):
        self._migrations = {}
        for migration in migrations:
            self._validate_migration(migration)
            source = migration["from"]
            if source in self._migrations:
                raise ValueError(
                    "duplicate migration defined for version %r" % (source,)
                )
            self._migrations[source] = migration
        self._check_for_cycles()

    @staticmethod
    def _validate_migration(migration):
        if not isinstance(migration, dict):
            raise ValueError(
                "migration must be a dict, got %s" % type(migration).__name__
            )
        for field in ("from", "to", "ops"):
            if field not in migration:
                raise ValueError("migration is missing required field %r" % field)
        if not isinstance(migration["ops"], list):
            raise ValueError("migration field 'ops' must be a list")

    def _check_for_cycles(self):
        for start in self._migrations:
            visited = set()
            version = start
            while version in self._migrations:
                if version in visited:
                    raise ValueError(
                        "migration cycle detected involving version %r" % (version,)
                    )
                visited.add(version)
                version = self._migrations[version]["to"]

    def migrate(self, save):
        if not isinstance(save, dict) or "version" not in save:
            raise ValueError("save must be a dict containing a 'version' field")

        data = copy.deepcopy(save)
        version = data["version"]

        while version in self._migrations:
            migration = self._migrations[version]
            self._apply_ops(migration["ops"], data)
            version = migration["to"]
            data["version"] = version

        return data

    def _apply_ops(self, ops, data):
        for op in ops:
            self._apply_op(op, data)

    def _apply_op(self, op, data):
        if not isinstance(op, dict) or "op" not in op:
            raise ValueError("invalid migration operation: %r" % (op,))
        handlers = {
            "rename": self._op_rename,
            "add": self._op_add,
            "remove": self._op_remove,
            "set": self._op_set,
        }
        handler = handlers.get(op["op"])
        if handler is None:
            raise ValueError("unknown migration operation %r" % (op["op"],))
        handler(op, data)

    @staticmethod
    def _require_field(op, field):
        if field not in op:
            raise ValueError(
                "operation %r is missing required field %r" % (op.get("op"), field)
            )
        return op[field]

    def _op_rename(self, op, data):
        source = self._require_field(op, "from")
        target = self._require_field(op, "to")
        if source not in data:
            raise ValueError("cannot rename missing key %r" % (source,))
        if target in data:
            raise ValueError(
                "cannot rename %r to %r: target key already exists" % (source, target)
            )
        data[target] = data.pop(source)

    def _op_add(self, op, data):
        key = self._require_field(op, "key")
        if "value" not in op:
            raise ValueError("'add' operation for key %r is missing 'value'" % (key,))
        if key in data:
            raise ValueError("cannot add key %r: key already exists" % (key,))
        data[key] = copy.deepcopy(op["value"])

    def _op_remove(self, op, data):
        key = self._require_field(op, "key")
        if key not in data:
            raise ValueError("cannot remove missing key %r" % (key,))
        del data[key]

    def _op_set(self, op, data):
        key = self._require_field(op, "key")
        if "value" not in op:
            raise ValueError("'set' operation for key %r is missing 'value'" % (key,))
        if key not in data:
            raise ValueError("cannot set missing key %r" % (key,))
        data[key] = copy.deepcopy(op["value"])
