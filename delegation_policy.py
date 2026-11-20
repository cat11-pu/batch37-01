from collections import deque


class DelegationPolicy:
    def __init__(self, roles, max_depth=2):
        if not isinstance(max_depth, int) or isinstance(max_depth, bool) or max_depth < 1:
            raise ValueError("max_depth must be a positive integer")
        self.roles = {
            name: {"parents": list(spec.get("parents", []))}
            for name, spec in roles.items()
        }
        for name, spec in self.roles.items():
            for parent in spec["parents"]:
                if parent not in self.roles:
                    raise ValueError("unknown parent role: %s" % parent)
        self._check_role_cycles()
        self.max_depth = max_depth
        self.allows = {name: set() for name in self.roles}
        self.denies = {name: set() for name in self.roles}
        self.delegations = []

    def _check_role_cycles(self):
        visiting, done = set(), set()

        def visit(node):
            if node in done:
                return
            if node in visiting:
                raise ValueError("role hierarchy contains a cycle")
            visiting.add(node)
            for parent in self.roles[node]["parents"]:
                visit(parent)
            visiting.discard(node)
            done.add(node)

        for name in self.roles:
            visit(name)

    def _require_role(self, role):
        if role not in self.roles:
            raise ValueError("unknown role: %s" % role)

    def _lineage(self, role):
        seen, stack = set(), [role]
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            yield current
            stack.extend(self.roles[current]["parents"])

    def _is_denied(self, role, permission):
        return any(permission in self.denies[r] for r in self._lineage(role))

    def _is_allowed(self, role, permission):
        return any(permission in self.allows[r] for r in self._lineage(role))

    def _delegation_closure(self, permission):
        """Roles holding `permission` via grants or delegation chains.

        Returns {role: (remaining_budget, path)} where path is a list of
        ("grant", role) / ("delegate", edge) steps. Each hop consumes one
        budget from both max_depth and the edge's depth, so chains that
        exceed the depth cap or loop around a cycle stop propagating.
        """
        best = {}
        queue = deque()
        for source in sorted(self.roles):
            if self._is_allowed(source, permission) and not self._is_denied(source, permission):
                best[source] = (self.max_depth, [("grant", source)])
                queue.append(source)
        by_source = {}
        for edge in self.delegations:
            if edge["permission"] == permission:
                by_source.setdefault(edge["role"], []).append(edge)
        while queue:
            current = queue.popleft()
            remaining, path = best[current]
            for edge in by_source.get(current, []):
                target = edge["target"]
                budget = min(remaining - 1, edge["depth"] - 1)
                if budget < 0:
                    continue
                if target in best and best[target][0] >= budget:
                    continue
                best[target] = (budget, path + [("delegate", edge)])
                queue.append(target)
        return best

    def grant(self, role, permission):
        self._require_role(role)
        self.allows[role].add(permission)

    def deny(self, role, permission):
        self._require_role(role)
        self.denies[role].add(permission)

    def delegate(self, role, target, permission, depth=1):
        self._require_role(role)
        self._require_role(target)
        if (not isinstance(depth, int) or isinstance(depth, bool)
                or depth < 1 or depth > self.max_depth):
            raise ValueError("invalid delegation depth: %r" % (depth,))
        for edge in self.delegations:
            if (edge["role"] == role and edge["target"] == target
                    and edge["permission"] == permission):
                raise ValueError("duplicate delegation: %s -> %s (%s)"
                                 % (role, target, permission))
        if not self.can(role, permission):
            return False
        self.delegations.append({
            "role": role,
            "target": target,
            "permission": permission,
            "depth": depth,
        })
        return True

    def revoke(self, role, target, permission):
        """Remove one delegation edge; other permissions of the role are untouched."""
        self._require_role(role)
        self._require_role(target)
        for index, edge in enumerate(self.delegations):
            if (edge["role"] == role and edge["target"] == target
                    and edge["permission"] == permission):
                del self.delegations[index]
                return True
        return False

    def reset_delegations(self):
        """Season reset: drop every delegation, keep grants and denies."""
        del self.delegations[:]

    def can(self, role, permission):
        self._require_role(role)
        if self._is_denied(role, permission):
            return False
        if self._is_allowed(role, permission):
            return True
        return role in self._delegation_closure(permission)

    def explain(self, role, permission):
        """Provenance for admins: direct grant, inheritance, or delegation layer."""
        self._require_role(role)
        denied_by = [r for r in self._lineage(role) if permission in self.denies[r]]
        if denied_by:
            return {"allowed": False, "source": None, "denied_by": denied_by, "chain": []}
        for holder in self._lineage(role):
            if permission in self.allows[holder]:
                return {
                    "allowed": True,
                    "source": "direct" if holder == role else "inherited",
                    "granted_by": holder,
                    "denied_by": [],
                    "chain": [],
                }
        closure = self._delegation_closure(permission)
        if role in closure:
            path = closure[role][1]
            hops = [dict(edge) for kind, edge in path if kind == "delegate"]
            return {
                "allowed": True,
                "source": "delegation",
                "granted_by": path[0][1],
                "denied_by": [],
                "chain": hops,
                "hops": len(hops),
            }
        return {"allowed": False, "source": None, "denied_by": [], "chain": []}

    def state(self):
        return {
            "roles": sorted(self.roles),
            "max_depth": self.max_depth,
            "allows": {role: sorted(perms) for role, perms in self.allows.items()},
            "denies": {role: sorted(perms) for role, perms in self.denies.items()},
            "delegations": [dict(edge) for edge in self.delegations],
        }
