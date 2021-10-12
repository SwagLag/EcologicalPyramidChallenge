import random

import numpy as np
import pandas as pd
import scipy.stats as stats


def calc_distance(origin_pos, target_pos):
    """
    Berekent Manhatten Distance tussen de twee coordinaten
    """
    return abs(origin_pos[0] - target_pos[0]) + abs(origin_pos[1] - target_pos[1])


def calc_closest_of_list(origin_pos, target_positions):
    """
    Berekent de dichtstbijzijnde tile uit een lijst van target_positions
    """
    best = {"pos": (0, 0), "distance": 1000}
    for pos in target_positions:
        d = calc_distance(origin_pos, pos)
        if d < best['distance']:
            best['distance'] = d
            best['pos'] = pos
    return best['pos']


def generate_grid_costs(agent, nexus_pos, from_agent: bool = False):
    """
    Berekent de cost (afstand) voor elke tile in de grid van de
    agent positie (from_agent == True) of vanuit een ander punt (gebruikt voor hive of clue)

    Deze functie wordt alleen gebruikt in de onderstaande functie generate_grid_gain
    """
    grid_values = np.zeros([agent.model.grid_w, agent.model.grid_h], dtype=np.float)

    for ix, x in enumerate(grid_values):
        for yx, y in enumerate(x):
            if from_agent:
                grid_values[ix, yx] = calc_distance(agent.pos, (ix, yx))
            else:
                grid_values[ix, yx] = calc_distance(nexus_pos, (ix, yx))

    return grid_values


def generate_grid_gain(agent, clue_loc=None, clue_grade=None):
    """
    Berekent de (gain (nectar) - cost (distance)) voor elke tile voor een bepaalde agent.
    Hierbij kan een clue_loc en clue_grade worden meegegeven.
    """
    grid_values = np.zeros([agent.model.grid_w, agent.model.grid_h], dtype=np.float)

    for ix, x in enumerate(grid_values):
        for yx, y in enumerate(x):
            if type(clue_loc) is not type(None):
                # Clue distance
                clue_distance = calc_distance([ix, yx], clue_loc)
                grid_values[ix, yx] = clue_grade * calc_distance_score_multiplier(clue_distance)
            if agent.grid_memory[ix, yx] == 'n':
                n = [a for a in agent.model.grid[ix, yx] if a.type == 'nectar']
                if len(n) > 0:
                    grid_values[ix, yx] = n[0].grade

            # De huidige positie altijd negeren
            if agent.pos == [ix, yx]:
                grid_values[ix, yx] = -1000

            # Ook negeren wanneer de tile een van de volgende waardes bevat:
            # - Een hive(x)
            # - Een lege ontdekte tile(o)
            # - Nectar met negatieve gain(/) <- Deze wordt als negeren in de grid gemarkeerd.

            if agent.grid_memory[ix, yx] in ['o', 'x', '/']:
                grid_values[ix, yx] = -1000

    return grid_values


def gen_linspace():
    """
    Functie omtrent onzekerheid van de clue afwijking. (Wordt niet gebruikt in de 3e challenge)
    """
    global global_linspace_ppf, global_linspace_pdf
    global_linspace_ppf = np.linspace(stats.expon.ppf(0.01),
                                      stats.expon.ppf(0.99), 100)
    global_linspace_pdf = stats.expon.pdf(global_linspace_ppf)


def calc_distance_score_multiplier(distance):
    """
    Functie omtrent onzekerheid van de clue afwijking. (Wordt niet gebruikt in de 3e challenge)
    """
    global global_linspace_ppf
    multiplier = len(np.nonzero(stats.expon.cdf(global_linspace_ppf, loc=distance))[0]) / 100
    return multiplier


def gen_clue_distance(max_radius):
    """
    Functie omtrent onzekerheid van de clue afwijking. (Wordt niet gebruikt in de 3e challenge)
    """
    global global_linspace_pdf
    df = pd.DataFrame((global_linspace_pdf * max_radius)).round()
    # df = df.round()
    return max(max_radius, (int(df.sample(1)[0])))


def gen_clue_tile(model, center, max_radius):
    """
    Functie omtrent onzekerheid van de clue afwijking. (Wordt niet gebruikt in de 3e challenge)
    """
    radius = gen_clue_distance(max_radius)
    options = []
    for ix, x in enumerate(model.grid):
        for yx, y in enumerate(model.grid):
            d = calc_distance([ix, yx], center)
            if d == radius:
                options.append([ix, yx])

    return random.choice(options)
