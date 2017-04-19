def get_square_distance(p1, p2):
    """
    Square distance between two points
    """
    dx = p1['time'] - p2['time']
    dy = p1['mean'] - p2['mean']

    return dx * dx + dy * dy


def get_square_segment_distance(p, p1, p2):
    """
    Square distance between point and a segment
    """
    x = p1['time']
    y = p1['mean']

    dx = p2['time'] - x
    dy = p2['mean'] - y

    if dx != 0 or dy != 0:
        t = ((p['time'] - x) * dx + (p['mean'] - y) * dy) / (dx * dx + dy * dy)

        if t > 1:
            x = p2['time']
            y = p2['mean']
        elif t > 0:
            x += dx * t
            y += dy * t

    dx = p['time'] - x
    dy = p['mean'] - y

    return dx * dx + dy * dy


def simplify_radial_distance(points, tolerance):
    length = len(points)
    prev_point = points[0]
    new_points = [prev_point]

    for i in range(length):
        point = points[i]

        if get_square_distance(point, prev_point) > tolerance:
            new_points.append(point)
            prev_point = point

    if prev_point != point:
        new_points.append(point)

    return new_points


def simplify_douglas_peucker(points, tolerance):
    length = len(points)
    markers = [0] * length  # Maybe not the most efficent way?

    first = 0
    last = length - 1

    first_stack = []
    last_stack = []

    new_points = []

    markers[first] = 1
    markers[last] = 1

    while last:
        max_sqdist = 0

        for i in range(first, last):
            sqdist = get_square_segment_distance(points[i], points[first], points[last])

            if sqdist > max_sqdist:
                index = i
                max_sqdist = sqdist

        if max_sqdist > tolerance:
            markers[index] = 1

            first_stack.append(first)
            last_stack.append(index)

            first_stack.append(index)
            last_stack.append(last)

        # Can pop an empty array in Javascript, but not Python, so check
        # the length of the list first
        if len(first_stack) == 0:
            first = None
        else:
            first = first_stack.pop()

        if len(last_stack) == 0:
            last = None
        else:
            last = last_stack.pop()

    for i in range(length):
        if markers[i]:
            new_points.append(points[i])

    return new_points


def simplify(points, tolerance=0.1, highest_quality=True):
    sqtolerance = tolerance * tolerance

    if not highest_quality:
        points = simplify_radial_distance(points, sqtolerance)

    return simplify_douglas_peucker(points, sqtolerance)
