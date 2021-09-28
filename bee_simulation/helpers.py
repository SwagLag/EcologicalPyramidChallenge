import numpy as np


def calc_distance(origin_pos, target_pos):
    return abs(origin_pos[0] - target_pos[0]) + abs(origin_pos[1] - target_pos[1])


def calc_closest_of_list(origin_pos, target_positions):
    best = {"pos": (0, 0), "distance": 1000}
    for pos in target_positions:
        d = calc_distance(origin_pos, pos)
        if d < best['distance']:
            best['distance'] = d
            best['pos'] = pos
    return best['pos']


def generate_grid_values(model, nexus_pos):
    grid_values = np.zeros([model.grid_w, model.grid_h], dtype=np.float)

    for ix, x in enumerate(grid_values):
        for yx, y in enumerate(x):
            grid_values[ix, yx] = calc_distance(nexus_pos, (ix, yx))

    return grid_values
