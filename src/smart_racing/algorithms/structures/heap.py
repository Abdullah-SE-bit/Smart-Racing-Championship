"""Manual binary heaps for event scheduling, rankings and indexed routing."""


class MinHeap:
    def __init__(self, items=(), trace=None):
        self._items = list(items)
        self.operations = 0
        self.trace = trace
        # Bottom-up heapify is linear in the number of items.
        for index in range(len(self._items) // 2 - 1, -1, -1):
            self._sift_down(index)
        if self.trace is not None:
            self.trace.append({"action": "heapify", "value": len(self._items)})

    def _sift_down(self, index):
        items = self._items
        item = items[index]
        while 2 * index + 1 < len(items):
            child = 2 * index + 1
            if child + 1 < len(items) and items[child + 1] < items[child]:
                child += 1
            if item <= items[child]:
                break
            items[index] = items[child]
            index = child
        items[index] = item

    def __len__(self):
        return len(self._items)

    def push(self, item):
        items = self._items
        items.append(item)
        index = len(items) - 1
        while index:
            parent = (index - 1) // 2
            if items[parent] <= item:
                break
            items[index] = items[parent]
            index = parent
        items[index] = item
        self.operations += 1
        if self.trace is not None:
            self.trace.append({"action": "heap insert", "value": len(items)})

    def peek(self):
        if not self._items:
            raise IndexError("peek from empty heap")
        return self._items[0]

    def pop(self):
        items = self._items
        if not items:
            raise IndexError("pop from empty heap")
        result = items[0]
        last = items.pop()
        if items:
            items[0] = last
            self._sift_down(0)
        self.operations += 1
        if self.trace is not None:
            self.trace.append({"action": "heap extract", "value": len(items)})
        return result


class IndexedMinHeap:
    """A routing heap with at most one (priority, distance, vertex) per vertex."""

    def __init__(self):
        self._items = []
        self._positions = {}
        self.operations = 0

    def __len__(self):
        return len(self._items)

    def _swap(self, first, second):
        items = self._items
        items[first], items[second] = items[second], items[first]
        self._positions[items[first][2]] = first
        self._positions[items[second][2]] = second

    def push_or_decrease(self, item):
        """Insert a vertex or replace its entry with a strictly smaller one."""
        vertex = item[2]
        if vertex in self._positions:
            index = self._positions[vertex]
            if item >= self._items[index]:
                raise ValueError("A heap update must decrease the vertex priority")
            self._items[index] = item
        else:
            index = len(self._items)
            self._items.append(item)
            self._positions[vertex] = index
        while index:
            parent = (index - 1) // 2
            if self._items[parent] <= self._items[index]:
                break
            self._swap(parent, index)
            index = parent
        self.operations += 1

    def pop(self):
        if not self._items:
            raise IndexError("pop from empty heap")
        result = self._items[0]
        last = self._items.pop()
        del self._positions[result[2]]
        if self._items:
            self._items[0] = last
            self._positions[last[2]] = 0
            index = 0
            while 2 * index + 1 < len(self._items):
                child = 2 * index + 1
                if child + 1 < len(self._items) and self._items[child + 1] < self._items[child]:
                    child += 1
                if self._items[index] <= self._items[child]:
                    break
                self._swap(index, child)
                index = child
        self.operations += 1
        return result
