import random

import numpy as np

from bee_simulation import logic, helpers
from bee_simulation.helpers import calc_distance, calc_closest_of_list


def move_to_target(agent, target_pos):
    # X then Y method
    if target_pos[0] < agent.pos[0]:
        agent.model.grid.move_agent(agent, (agent.pos[0] - 1, agent.pos[1]))
    elif target_pos[0] > agent.pos[0]:
        agent.model.grid.move_agent(agent, (agent.pos[0] + 1, agent.pos[1]))
    elif target_pos[1] < agent.pos[1]:
        agent.model.grid.move_agent(agent, (agent.pos[0], agent.pos[1] - 1))
    elif target_pos[1] > agent.pos[1]:
        agent.model.grid.move_agent(agent, (agent.pos[0], agent.pos[1] + 1))
    elif target_pos[0] == agent.pos[0] and target_pos[1] == agent.pos[1]:
        print("move_to_target origin same as target")
    else:
        exit(f"move_to_target error,current_position:{agent.pos}, target:{target_pos}")


def return_to_hive(agent):
    hives = np.argwhere(agent.grid_memory == 'x')
    return move_to_target(agent, calc_closest_of_list(agent.pos, hives))


def fetch_closest_nectar(agent):
    nectar = np.argwhere(agent.grid_memory == 'n')
    return move_to_target(agent, calc_closest_of_list(agent.pos, nectar))


def explore(agent):
    unexplored = np.argwhere(agent.grid_memory == '')
    return move_to_target(agent, calc_closest_of_list(agent.pos, unexplored))


def explore2(agent):

    best_pos = logic.calc_values_of_list(agent.model, agent.pos, np.ndindex(agent.grid_values.shape), agent.grid_values, agent.grid_memory)
    return move_to_target(agent, best_pos)


def bee_dance(agent):
    nectar_pos = np.argwhere(agent.grid_memory == 'n')
    hive_pos = agent.hive_pos

    # Wipe grid memory
    agent.grid_memory = agent.init_grid_memory(agent)

    # Reset grid values
    agent.grid_values = helpers.generate_grid_costs(agent, hive_pos)
    if len(nectar_pos) > 0:
        # Put clue into grid values
        clue_loc = random.choice(nectar_pos)
        agent.clue_loc = clue_loc

        # print(np.clip(-20+helpers.generate_grid_values(agent.model, clue_loc),-1000,0))
        # agent.grid_values += np.clip(-10+helpers.generate_grid_costs(agent, clue_loc, wlue=True), -1000, 0)


def handle_nectar(agent):
    nectars = [a for a in agent.model.grid[agent.pos] if a.type == "nectar"]
    hives = [a for a in agent.model.grid[agent.pos] if a.type == "hive"]
    # Dropping of Nectar
    for hive in hives:
        if agent.pos == hive.pos and len(agent.nectar_collected) > 0:
            for n in agent.nectar_collected:
                agent.model.nectar_collected += n
                hive.energy += n  # Add energy to hive
            agent.nectar_collected = []

            # Refill energy
            refill_amount = agent.max_energy - agent.energy
            if hive.energy >= refill_amount:
                hive.energy -= refill_amount
                agent.energy += refill_amount
            else:
                agent.energy += hive.energy
                hive.energy = 0

            # Bee dance
            bee_dance(agent)

    # Collection of Nectar
    for nectar in nectars:
        if agent.pos == nectar.pos:
            if len(agent.nectar_collected) == 0:
                agent.nectar_collected.append(nectar.grade)
                if nectar.amount == 1:
                    agent.model.grid.remove_agent(nectar)
                    agent.grid_memory[agent.pos] = 'o'
                else:
                    nectar.amount -= 1
