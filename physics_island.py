class IslandManager:
    def __init__(self):
        self.bodies = {}
        self.contacts = []
        self.adjacency = {}

    def add_body(self, body_id, sleeping=False):
        if body_id in self.bodies:
            raise ValueError(f"duplicate body id: {body_id!r}")
        self.bodies[body_id] = bool(sleeping)
        self.adjacency[body_id] = set()

    def remove_body(self, body_id):
        if body_id not in self.bodies:
            raise ValueError(f"unknown body id: {body_id!r}")
        for neighbor in self.adjacency[body_id]:
            self.adjacency[neighbor].discard(body_id)
        self.contacts = [
            (left, right)
            for left, right in self.contacts
            if left != body_id and right != body_id
        ]
        del self.adjacency[body_id]
        del self.bodies[body_id]

    def wake(self, body_id):
        if body_id not in self.bodies:
            raise ValueError(f"unknown body id: {body_id!r}")
        for member in self._island(body_id):
            self.bodies[member] = False

    def step(self, contacts, moving=None):
        edges = []
        for contact in contacts:
            try:
                left, right = contact
            except TypeError:
                raise ValueError(f"invalid contact: {contact!r}")
            if (
                left not in self.bodies
                or right not in self.bodies
                or left == right
            ):
                raise ValueError(f"invalid contact: {contact!r}")
            edges.append((left, right))

        movers = list(moving) if moving is not None else []
        for body_id in movers:
            if body_id not in self.bodies:
                raise ValueError(f"unknown body id: {body_id!r}")

        self.contacts = edges
        self.adjacency = {body_id: set() for body_id in self.bodies}
        for left, right in edges:
            self.adjacency[left].add(right)
            self.adjacency[right].add(left)

        for body_id in movers:
            self.wake(body_id)

    def state(self):
        return dict(self.bodies)

    def _island(self, body_id):
        seen = set()
        stack = [body_id]
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            stack.extend(self.adjacency[current] - seen)
        return seen
