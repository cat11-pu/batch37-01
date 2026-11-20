import heapq


class RenderGraph:
    def __init__(self, passes):
        self.passes = []
        seen = set()
        for entry in passes:
            pid = entry.get("id")
            if not isinstance(pid, str) or not pid:
                raise ValueError(f"invalid pass id: {pid!r}")
            if pid in seen:
                raise ValueError(f"duplicate pass id: {pid}")
            seen.add(pid)
            reads = list(entry.get("reads") or [])
            writes = list(entry.get("writes") or [])
            after = list(entry.get("after") or [])
            for name in reads + writes:
                if not isinstance(name, str) or not name:
                    raise ValueError(f"invalid resource name: {name!r}")
            self.passes.append(
                {"id": pid, "reads": reads, "writes": writes, "after": after}
            )

    def compile(self):
        ids = [p["id"] for p in self.passes]
        known = set(ids)
        deps = {pid: set() for pid in ids}

        for p in self.passes:
            for target in p["after"]:
                if target == p["id"]:
                    raise ValueError(f"pass {p['id']} depends on itself")
                if target not in known:
                    raise ValueError(
                        f"pass {p['id']} has unknown dependency: {target}"
                    )
                deps[p["id"]].add(target)

        resources = {}
        for index, p in enumerate(self.passes):
            for name in p["reads"]:
                resources.setdefault(name, []).append((index, p["id"], False))
            for name in p["writes"]:
                resources.setdefault(name, []).append((index, p["id"], True))

        for accesses in resources.values():
            accesses.sort(key=lambda item: item[0])
            writers = [pid for _, pid, is_write in accesses if is_write]
            readers = [pid for _, pid, is_write in accesses if not is_write]
            for earlier, later in zip(writers, writers[1:]):
                if earlier != later:
                    deps[earlier].add(later)
            if not writers or not readers:
                continue
            if accesses[0][2]:
                for writer in writers:
                    for reader in readers:
                        if writer != reader:
                            deps[writer].add(reader)
            else:
                for reader in readers:
                    for writer in writers:
                        if reader != writer:
                            deps[reader].add(writer)

        dependents = {pid: set() for pid in ids}
        indegree = {}
        for pid, required in deps.items():
            indegree[pid] = len(required)
            for other in required:
                dependents[other].add(pid)

        ready = [pid for pid in ids if indegree[pid] == 0]
        heapq.heapify(ready)
        order = []
        while ready:
            pid = heapq.heappop(ready)
            order.append(pid)
            for follower in dependents[pid]:
                indegree[follower] -= 1
                if indegree[follower] == 0:
                    heapq.heappush(ready, follower)

        if len(order) != len(ids):
            raise ValueError("dependency cycle detected")
        return order
