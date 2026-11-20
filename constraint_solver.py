import math
from numbers import Real


class ConstraintSolver:
    def __init__(self, iterations=4):
        if isinstance(iterations, bool) or not isinstance(iterations, int):
            raise ValueError("iterations must be a positive integer")
        if iterations < 1:
            raise ValueError("iterations must be a positive integer")
        self.iterations = iterations
        self.bodies = {}
        self.contacts = []

    @staticmethod
    def _finite_number(value, name):
        if isinstance(value, bool) or not isinstance(value, Real):
            raise ValueError(f"{name} must be a finite number")
        value = float(value)
        if not math.isfinite(value):
            raise ValueError(f"{name} must be a finite number")
        return value

    @staticmethod
    def _body_key(body_id):
        try:
            hash(body_id)
        except TypeError as exc:
            raise ValueError("body id must be hashable") from exc
        return (
            type(body_id).__module__,
            type(body_id).__qualname__,
            repr(body_id),
        )

    @staticmethod
    def _contact_key(contact):
        body_a = contact["a"]
        body_b = contact["b"]
        key_a = ConstraintSolver._body_key(body_a)
        key_b = ConstraintSolver._body_key(body_b)
        nx = contact["nx"]
        ny = contact["ny"]
        if key_a > key_b:
            key_a, key_b = key_b, key_a
            nx = -nx
            ny = -ny
        return (
            key_a,
            key_b,
            nx,
            ny,
            contact["penetration"],
            contact["restitution"],
            contact["friction"],
        )

    def add_body(self, body_id, mass, x, y, vx=0.0, vy=0.0, static=False):
        self._body_key(body_id)
        if body_id in self.bodies:
            raise ValueError(f"duplicate body id: {body_id!r}")

        mass = self._finite_number(mass, "mass")
        if mass < 0.0 or (not static and mass == 0.0):
            raise ValueError("dynamic bodies must have positive mass")

        x = self._finite_number(x, "x")
        y = self._finite_number(y, "y")
        vx = self._finite_number(vx, "vx")
        vy = self._finite_number(vy, "vy")
        static = bool(static)
        inv_mass = 0.0 if static or mass == 0.0 else 1.0 / mass

        self.bodies[body_id] = {
            "mass": mass,
            "x": x,
            "y": y,
            "vx": 0.0 if static else vx,
            "vy": 0.0 if static else vy,
            "static": static,
            "inv_mass": inv_mass,
        }

    def add_contact(
        self,
        a,
        b,
        nx,
        ny,
        penetration,
        restitution=0.0,
        friction=0.0,
    ):
        try:
            a_known = a in self.bodies
            b_known = b in self.bodies
        except TypeError as exc:
            raise ValueError("contact body id must be hashable") from exc
        if not a_known or not b_known:
            raise ValueError("contact references an unknown body")
        if a == b:
            raise ValueError("a body cannot contact itself")

        nx = self._finite_number(nx, "normal x")
        ny = self._finite_number(ny, "normal y")
        normal_length = math.hypot(nx, ny)
        if normal_length == 0.0:
            raise ValueError("contact normal must be non-zero")
        nx /= normal_length
        ny /= normal_length

        penetration = self._finite_number(penetration, "penetration")
        restitution = self._finite_number(restitution, "restitution")
        friction = self._finite_number(friction, "friction")
        if penetration < 0.0:
            raise ValueError("penetration cannot be negative")
        if not 0.0 <= restitution <= 1.0:
            raise ValueError("restitution must be between 0 and 1")
        if friction < 0.0:
            raise ValueError("friction cannot be negative")

        self.contacts.append(
            {
                "a": a,
                "b": b,
                "nx": nx,
                "ny": ny,
                "penetration": penetration,
                "restitution": restitution,
                "friction": friction,
            }
        )

    @staticmethod
    def _add_impulse(body, ix, iy):
        inv_mass = body["inv_mass"]
        body["vx"] += ix * inv_mass
        body["vy"] += iy * inv_mass

    def step(self, dt):
        dt = self._finite_number(dt, "dt")
        if dt < 0.0:
            raise ValueError("dt cannot be negative")

        constraints = []
        for contact in sorted(self.contacts, key=self._contact_key):
            body_a = self.bodies[contact["a"]]
            body_b = self.bodies[contact["b"]]
            nx = contact["nx"]
            ny = contact["ny"]
            inv_sum = body_a["inv_mass"] + body_b["inv_mass"]

            relative_vx = body_b["vx"] - body_a["vx"]
            relative_vy = body_b["vy"] - body_a["vy"]
            normal_velocity = relative_vx * nx + relative_vy * ny

            target_normal_velocity = (
                -contact["restitution"] * min(normal_velocity, 0.0)
            )

            tangent_x = -ny
            tangent_y = nx
            tangent_velocity = relative_vx * tangent_x + relative_vy * tangent_y
            if inv_sum > 0.0:
                support_impulse = (
                    contact["friction"] * abs(tangent_velocity) / inv_sum
                )
            else:
                support_impulse = 0.0

            constraints.append(
                {
                    "contact": contact,
                    "body_a": body_a,
                    "body_b": body_b,
                    "inv_sum": inv_sum,
                    "target_normal_velocity": target_normal_velocity,
                    "normal_impulse": 0.0,
                    "tangent_impulse": 0.0,
                    "support_impulse": support_impulse,
                    "tangent_x": tangent_x,
                    "tangent_y": tangent_y,
                }
            )

        for _ in range(self.iterations):
            for constraint in constraints:
                body_a = constraint["body_a"]
                body_b = constraint["body_b"]
                contact = constraint["contact"]
                inv_sum = constraint["inv_sum"]
                if inv_sum <= 0.0:
                    continue

                nx = contact["nx"]
                ny = contact["ny"]
                relative_vx = body_b["vx"] - body_a["vx"]
                relative_vy = body_b["vy"] - body_a["vy"]
                normal_velocity = relative_vx * nx + relative_vy * ny

                normal_delta = (
                    constraint["target_normal_velocity"] - normal_velocity
                ) / inv_sum
                old_normal_impulse = constraint["normal_impulse"]
                new_normal_impulse = max(
                    0.0, old_normal_impulse + normal_delta
                )
                applied_normal = new_normal_impulse - old_normal_impulse
                constraint["normal_impulse"] = new_normal_impulse
                self._add_impulse(
                    body_a, -applied_normal * nx, -applied_normal * ny
                )
                self._add_impulse(
                    body_b, applied_normal * nx, applied_normal * ny
                )

                tangent_x = constraint["tangent_x"]
                tangent_y = constraint["tangent_y"]
                relative_vx = body_b["vx"] - body_a["vx"]
                relative_vy = body_b["vy"] - body_a["vy"]
                tangent_velocity = relative_vx * tangent_x + relative_vy * tangent_y
                tangent_delta = -tangent_velocity / inv_sum
                old_tangent_impulse = constraint["tangent_impulse"]

                friction_limit = (
                    contact["friction"] * constraint["normal_impulse"]
                )
                if friction_limit == 0.0:
                    friction_limit = constraint["support_impulse"]
                new_tangent_impulse = max(
                    -friction_limit,
                    min(friction_limit, old_tangent_impulse + tangent_delta),
                )
                applied_tangent = new_tangent_impulse - old_tangent_impulse
                constraint["tangent_impulse"] = new_tangent_impulse
                self._add_impulse(
                    body_a,
                    -applied_tangent * tangent_x,
                    -applied_tangent * tangent_y,
                )
                self._add_impulse(
                    body_b,
                    applied_tangent * tangent_x,
                    applied_tangent * tangent_y,
                )

        for constraint in constraints:
            body_a = constraint["body_a"]
            body_b = constraint["body_b"]
            contact = constraint["contact"]
            inv_sum = constraint["inv_sum"]
            if inv_sum <= 0.0:
                continue
            correction = contact["penetration"]
            correction_a = correction * body_a["inv_mass"] / inv_sum
            correction_b = correction * body_b["inv_mass"] / inv_sum
            body_a["x"] -= correction_a * contact["nx"]
            body_a["y"] -= correction_a * contact["ny"]
            body_b["x"] += correction_b * contact["nx"]
            body_b["y"] += correction_b * contact["ny"]

        for body in self.bodies.values():
            if body["inv_mass"] == 0.0:
                continue
            body["x"] += body["vx"] * dt
            body["y"] += body["vy"] * dt

    def state(self):
        return {
            body_id: {
                "mass": body["mass"],
                "x": body["x"],
                "y": body["y"],
                "vx": body["vx"],
                "vy": body["vy"],
                "static": body["static"],
                "inv_mass": body["inv_mass"],
            }
            for body_id, body in self.bodies.items()
        }
