def calc_distance(origin, target_pos):
    return abs(origin.pos[0] - target_pos[0]) + abs(origin.pos[1] - target_pos[1])


def calc_closest_of_list(origin, target_positions):
    best = {"pos": (0, 0), "distance": 100000000}
    for pos in target_positions:
        d = origin._calc_distance(origin, pos)
        if d < best['distance']:
            best['distance'] = d
            best['pos'] = pos
    return best['pos']