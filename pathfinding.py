from collections import deque


def find_path(world, start, goal):
    """Find a shortest path between two tiles with a breadth-first search.

    Returns the list of tiles to cross, in order. The start tile is not
    included, the goal tile is. Returns an empty list if we are already
    there or if no path exists.
    """
    if start == goal:
        return []

    # the 4 directions we can move in: right, left, down, up
    steps = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    queue = deque()
    queue.append(start)

    # for each tile we reached, remember the tile we came from
    came_from = {start: None}

    while len(queue) > 0:
        current = queue.popleft()
        if current == goal:
            break

        for step_x, step_y in steps:
            next_x = current[0] + step_x
            next_y = current[1] + step_y
            next_tile = (next_x, next_y)

            if next_tile in came_from:
                continue
            if world.is_solid(next_x, next_y):
                continue

            came_from[next_tile] = current
            queue.append(next_tile)

    if goal not in came_from:
        return []

    # walk back from the goal to the start, then reverse the list
    path = []
    tile = goal
    while tile != start:
        path.append(tile)
        tile = came_from[tile]
    path.reverse()
    return path