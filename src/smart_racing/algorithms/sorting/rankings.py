"""Three manual sorting methods and heap top-k with a shared key."""

from smart_racing.algorithms.structures.heap import MinHeap


def merge_sort(items, key=lambda x: x, trace=None):
    values = list(items)
    if len(values) < 2:
        return values
    middle = len(values) // 2
    left = merge_sort(values[:middle], key, trace)
    right = merge_sort(values[middle:], key, trace)
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if key(left[i]) <= key(right[j]):
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    if trace is not None:
        trace.append({"action": "merge", "values": [str(key(item)) for item in result]})
    return result


def quick_sort(items, key=lambda x: x, trace=None):
    values = list(items)
    if len(values) < 2:
        return values
    pivot = key(values[len(values) // 2])
    less, equal, greater = [], [], []
    for item in values:
        value = key(item)
        if value < pivot:
            less.append(item)
        elif value > pivot:
            greater.append(item)
        else:
            equal.append(item)
    if trace is not None:
        trace.append({"action": "partition", "values": [str(key(item)) for item in less + equal + greater]})
    return quick_sort(less, key, trace) + equal + quick_sort(greater, key, trace)


def heap_sort(items, key=lambda x: x, trace=None):
    values = list(items)
    size = len(values)

    def sift(root, end):
        while 2 * root + 1 < end:
            child = 2 * root + 1
            if child + 1 < end and key(values[child]) < key(values[child + 1]):
                child += 1
            if key(values[root]) >= key(values[child]):
                return
            values[root], values[child] = values[child], values[root]
            root = child

    for index in range(size // 2 - 1, -1, -1):
        sift(index, size)
    for end in range(size - 1, 0, -1):
        values[0], values[end] = values[end], values[0]
        sift(0, end)
        if trace is not None:
            trace.append({"action": "extract maximum", "values": [str(key(item)) for item in values]})
    return values


def top_k(items, k: int, key=lambda x: x, trace=None):
    if k < 0:
        raise ValueError("k cannot be negative")
    heap = MinHeap(((key(item), sequence, item) for sequence, item in enumerate(items)), trace=trace)
    return [heap.pop()[2] for _ in range(min(k, len(heap)))]
