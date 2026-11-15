"""A small manual binary min-heap, shared by routing and events."""


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
