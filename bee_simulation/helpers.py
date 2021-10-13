import random

import numpy as np
import pandas as pd
import scipy.stats as stats

class Task:
    """
    Abstract helper class for designating tasks that agents have
    to complete. Agent interpretation should be handled by assigning
    a unique task type to each object, and assigning unique attributes
    afterwards related to that task type.
    """
    def __init__(self, tasktype):
        self.type = tasktype


def calc_distance(origin_pos, target_pos):
    """
    Calculate Manhatten distance between two coördinates.
    """
    return abs(origin_pos[0] - target_pos[0]) + abs(origin_pos[1] - target_pos[1])


def calc_closest_of_list(origin_pos, target_positions):
    """
    Calculate closest tile from a list of target positions.
    """
    best = {"pos": (0, 0), "distance": 1000}
    for pos in target_positions:
        d = calc_distance(origin_pos, pos)
        if d < best['distance']:
            best['distance'] = d
            best['pos'] = pos
    return best['pos']


def gather_gridknowledge(model):
    grid_grade, grid_amount = np.zeros((model.width, model.height), dtype=np.int), np.zeros((model.width, model.height), dtype=np.int)
    beeknowledge = [x.grid_memory for x in model.schedule.agents if x.type == "bee"]
    nectars = [y for x in model.grid for y in x if y.type == "nectar"]
    for nectar in nectars:
        for gm in beeknowledge:
            if gm[nectar.pos] == "n":
                grid_grade[nectar.pos] = nectar.grade
                grid_amount[nectar.pos] = nectar.amount
    return grid_grade, grid_amount


def gather_tasks_nectar(grid_grade, grid_amount):
    """
    Creates task objects based on the amount, position and grade of
    each nectar object.
    """
    if grid_grade.shape == grid_amount.shape:
        tasks = []
        tasktype = "nectar"
        for i, x in enumerate(grid_grade):
            for j, _ in enumerate(x):
                if grid_grade[i, j] > 0:
                    for _ in range(grid_amount[i, j]):
                        task = Task(tasktype)
                        task.pos = (i, j)
                        task.grade = grid_grade[i, j]
                        tasks.append(task)

        return tasks
    else:
        raise Exception()


def generate_grid_costs(agent, nexus_pos, from_agent: bool = False):
    """
    Calculate the cost (distance) for every tile in the grid from the position of the agent or from a different point.

    This function only gets used in the function 'generate_grid_gain'.
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
    Calculate the (gain (nectar) - cost (distance)) for every tile for a certain agent.
    """
    grid_values = np.zeros([agent.model.grid_w, agent.model.grid_h], dtype=np.float)

    for ix, x in enumerate(grid_values):
        for yx, y in enumerate(x):
            if type(clue_loc) is not type(None):

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


def task_distribution_algorithm(agents, tasks):
    """
    Distributes tasks based on the value each agent gives
    to a task.
    """

    if tasks:
        assignments = []
        t_agents = agents[0].copy()
        t_tasks = tasks.copy()

        # Fase 1: Reken voor elke agent voor elke taak zijn gegeven value uit.
        taskagents = [t_agents for t_task in t_tasks]
        taskvalues = [[] for t_task in t_tasks]

        for i, t_task in enumerate(t_tasks):
            for t_agent in t_agents:
                taskvalues[i].append(t_agent.value(t_task))

        # Fase 2: Taak (en agents!) worden gesorteerd o.b.v. value bij de taak values per taak.
        sortedtaskvalues, sortedtaskagents = [], []

        for i in range(len(t_agents)):
            # TODO: Fix de gelijkwaardige soort manier
            # TypeError: '<' not supported between instances of 'Bee' and 'Bee'
            print('------------------------')
            print(i)
            print(taskagents)
            print(taskvalues)


            x2 = taskagents[i].copy()
            x1 = taskvalues[i].copy()
            x = zip(x1, x2)

            # s = sorted(x)
            #
            # stv, sta = zip(s)
            # sortedtaskvalues.append(list(stv))
            # sortedtaskagents.append(list(sta))

        # Fase 3: Wijs voor elke taak een agent toe
        for i, t_task in enumerate(t_tasks):
            bestagent = sortedtaskagents[i][-1]
            assignments.append((bestagent, t_task))

            # Nadat een agent toegewezen is, kan hij niet toegewezen worden aan een andere taak.
            # Ofwel, we verwijderen hem van alle sortedtaskagent lijsten.
            for lst in sortedtaskagents:
                lst.remove(bestagent)
        return assignments

    else:
        # Er zijn geen bloemenvelden gevonden, dus iedereen moet gaan ontdekken.
        return []


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
