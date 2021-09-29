import random

import numpy as np
import pandas as pd
from scipy.stats import expon


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


def generate_grid_costs(agent, nexus_pos, from_agent: bool = False):
    grid_values = np.zeros([agent.model.grid_w, agent.model.grid_h], dtype=np.float)

    for ix, x in enumerate(grid_values):
        for yx, y in enumerate(x):
            if from_agent:
                grid_values[ix, yx] = calc_distance(agent.pos, (ix, yx))
            else:
                grid_values[ix, yx] = calc_distance(nexus_pos, (ix, yx))

    return grid_values


def generate_grid_gain(agent, clue_loc=None, clue_grade=None):
    grid_values = np.zeros([agent.model.grid_w, agent.model.grid_h], dtype=np.float)

    for ix, x in enumerate(grid_values):
        for yx, y in enumerate(x):
            if agent.grid_memory[ix, yx] in ['o', 'x', '/']:
                grid_values[ix, yx] = -1000
            if type(clue_loc) is not type(None) and clue_loc[0] == ix and clue_loc[1] == yx:
                grid_values[ix, yx] = clue_grade
                # n = [a for a in agent.model.grid[ix, yx] if a.type == 'nectar']
                # if len(n) > 0:
                #     grid_values[ix, yx] = n[0].grade
            if agent.grid_memory[ix, yx] == 'n':
                n = [a for a in agent.model.grid[ix, yx] if a.type == 'nectar']
                if len(n) > 0:
                    grid_values[ix, yx] = n[0].grade

    return grid_values


def gen_clue_distance(max_radius):
    x = np.linspace(expon.ppf(0.01),
                    expon.ppf(0.99), 100)
    x = expon.pdf(x)

    df = pd.DataFrame((x * max_radius))
    df = df.round()
    return max(max_radius, (int(df.sample(1)[0])))


def gen_clue_tile(model, center, max_radius):
    radius = gen_clue_distance(max_radius)
    options = []
    for ix, x in enumerate(model.grid):
        for yx, y in enumerate(model.grid):
            d = calc_distance([ix, yx], center)
            if d == radius:
                options.append([ix, yx])

    return random.choice(options)
