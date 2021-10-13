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


def get_task(df):
    y = df.max()
    agent = y.idxmax()
    task = df[agent].idxmax()
    return task


def get_bid(df, agent, task):
    if len(df[agent]) > 0:
        return max(0, df[agent][task] - df[agent].nlargest(2)[-1:].values[0])
    else:
        return max(0, df[agent][task])


def best_bid(df, task):
    """Find the agent who most wants this task."""
    highest_bid = {'agent': None, 'bid': -1}

    # For every agent
    for agent in df.columns:

        # Find out how badly he wants the task
        bid = get_bid(df, agent, task)

        # If he wants it more than the last agents, then he will get it
        if bid > highest_bid['bid']:
            highest_bid['agent'] = agent
            highest_bid['bid'] = bid
    return highest_bid


def skim_df(df, agent, task):
    """Delete the agent and his assigned task from the dataframe."""
    x = df.drop(agent, axis=1)
    x = x.drop(task, axis=0)
    return x


def gather_gridknowledge(model):
    """The bees gridknowledge gets updated, it now has the total gridknowledge from every bee. They also gain the
    knowledge where every flower presides, how much nectar it has left and what the nectars grade is."""
    grid_grade, grid_amount = np.zeros((model.width, model.height), dtype=np.int), np.zeros((model.width, model.height), dtype=np.int)

    # When a hivemind signal gets send, the gridmemory of every bee gets updated
    # ∀a ∀b ((Bee(a) ˄ Bee(b) ˄ HiveMind(a, b)) -> (GainGridMemory(a, b) ˄ GainGridMemory(b, a)))
    beeknowledge = [x.grid_memory for x in model.schedule.agents if x.type == "bee"]
    nectars = [y for x in model.grid for y in x if y.type == "nectar"]
    for nectar in nectars:
        for gm in beeknowledge:
            if gm[nectar.pos] == "n":
                grid_grade[nectar.pos] = nectar.grade
                grid_amount[nectar.pos] = nectar.amount
    return grid_grade, grid_amount


def gather_tasks_bees(grid_grade, grid_amount, agent_amount):
    """
    Creates task objects based on the amount, position and grade of each nectar object.
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

        if agent_amount > len(tasks):
            explorer_tasks = agent_amount - len(tasks)
            for k in range(explorer_tasks):
                task = Task("explore")
                tasks.append(task)

        return tasks
    else:
        raise Exception()


def generate_grid_costs(agent, nexus_pos, from_agent: bool = False):
    """
    Calculate the cost (distance) for every tile in the grid from the position of the agent or from a different point.
    """
    grid_values = np.zeros([agent.model.width, agent.model.height], dtype=np.float)

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
    grid_values = np.zeros([agent.model.width, agent.model.height], dtype=np.float)

    for ix, x in enumerate(grid_values):
        for yx, y in enumerate(x):
            if type(clue_loc) is not type(None):

                clue_distance = calc_distance([ix, yx], clue_loc)
                grid_values[ix, yx] = clue_grade * calc_distance_score_multiplier(clue_distance)
            if agent.grid_memory[ix, yx] == 'n':
                n = [a for a in agent.model.grid[ix, yx] if a.type == 'nectar']
                if len(n) > 0:
                    grid_values[ix, yx] = n[0].grade

            # Ignore the bees own position
            if agent.pos == [ix, yx]:
                grid_values[ix, yx] = -1000

            # Also ignore the following tiles:
            # - A hive(x)
            # - An empty explored tile (o)
            # - Nectar with a negative gain (/).

            if agent.grid_memory[ix, yx] in ['o', 'x', '/']:
                grid_values[ix, yx] = -1000
    return grid_values


def gen_linspace():
    """
    Function around uncertainty of the clue radius.
    """
    global global_linspace_ppf, global_linspace_pdf
    global_linspace_ppf = np.linspace(stats.expon.ppf(0.01),
                                      stats.expon.ppf(0.99), 100)
    global_linspace_pdf = stats.expon.pdf(global_linspace_ppf)


def generate_valuedataframe(agents, tasks):
    assignments = []
    t_agents = agents.copy()
    t_tasks = tasks.copy()
    t_agent_ids = [x.unique_id for x in t_agents]

    # Wordt verzorgd door gather_tasks_bees()
    # if len(agents) > len(tasks):  # Als er meer agents zijn dan tasks
    #     for i in range(len(agents) - len(tasks)):
    #         t_tasks.append(Task("explore"))

    valuematrix = np.zeros((len(t_tasks), len(t_agent_ids)))
    valuedataframe = pd.DataFrame(valuematrix,columns=t_agent_ids, dtype=np.int)
    for i, x in valuedataframe.iterrows():
        for j, _ in enumerate(x):
            valuedataframe[t_agent_ids[j]][i] = t_agents[j].value(t_tasks[i])
    return valuedataframe


def assign_tasks(df):
    assignments = []

    while df.shape[0] > 2 and df.shape[1] > 2:
        try:
            task = get_task(df)
            bb = best_bid(df, task)
        except:
            print(df)
        assignments.append((bb['agent'], task))
        df = skim_df(df, bb['agent'], task)
    return assignments


def translate_assignments(assignments, agents, tasks):
    """
    :param assignments: The list that contains tuples containing (agentid, taskid)
    :param tasks: The list that contains the tasks used in the generate_valuedataframe func
    :param agents: The list that contains the agents used in the generate_valuedataframe func
    :return: A list containing tuples containing (agent, task)
    """
    agent_ids = [x.unique_id for x in agents]
    translated = []

    for pair in assignments:
        agent_id = pair[0]
        task_id = pair[1]
        relevant_agent = agents[agent_ids.index(agent_id)]
        relevant_task = tasks[task_id]
        translated.append((relevant_agent,relevant_task))

    return translated

def task_distribution_algorithm(agents, tasks):
    """
    Distributes tasks based on the value each agent gives
    to a task.
    """

    if tasks:
        assignments = []
        t_agents = agents.copy()
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
            temp = list(zip(taskvalues[i], taskagents[i]))
            temp2 = sorted(temp)
            stv, sta = zip(*temp2)
            # stv, sta = zip(*sorted(zip(taskvalues[i].copy(), taskagents[i].copy())))
            sortedtaskvalues.append(list(stv))
            sortedtaskagents.append(list(sta))

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


