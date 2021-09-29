import random

import numpy as np

from bee_simulation import helpers
from bee_simulation.helpers import calc_closest_of_list


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


def bee_dance(agent):
    agent.clue_loc = None
    agent.clue_grade = None

    nectar_positions = []
    for ix, x in enumerate(agent.grid_memory):
        for yx, y in enumerate(x):
            if agent.grid_memory[ix, yx] == 'n':
                nectar_positions.append([ix, yx])

    hive_pos = agent.hive_pos

    # Wipe grid memory
    agent.grid_memory = agent.init_grid_memory(agent)

    # Reset grid values
    agent.grid_values = helpers.generate_grid_costs(agent, hive_pos)

    if len(nectar_positions) > 0:
        # Put clue into grid values
        true_clue_loc = random.choice(nectar_positions)
        clue_loc = helpers.gen_clue_tile(agent.model, true_clue_loc, agent.model.max_clue_radius)
        # print(f"True loc:{true_clue_loc}, Clue loc:{clue_loc}")
        nectar = [a for a in agent.model.grid[true_clue_loc] if a.type == "nectar"]
        agent.clue_grade = nectar[0].grade
        agent.clue_loc = clue_loc

def refill_energy(agent):
    hive = [a for a in agent.model.grid[agent.pos] if a.type == "hive"][0]
    refill_amount = abs(agent.max_energy - agent.energy)
    if hive.energy >= refill_amount:
        hive.energy -= refill_amount
        agent.energy += refill_amount
    else:
        agent.energy += hive.energy
        hive.energy = 0


def collect_nectar(agent, nectar):
    """∀a ∀b ((Bee(a) ˄ FlowerField(b) ˄ ¬ HasNectar(a) ˄ (Touch(a, b) ˄ Nectar(b) ) -> (GainNectar(a) ˄
    LoseNectar(b))))).
    When a bee stands on a flowerfield, hasn't gathered any nectar yet and the flowerfield does contain nectar, then
    the bee will collect this nectar."""

    if len(agent.nectar_collected) == 0:
        agent.nectar_collected.append(nectar.grade)
        if nectar.amount == 1:
            agent.model.grid.remove_agent(nectar)
            agent.grid_memory[agent.pos] = 'o'
        else:
            nectar.amount -= 1


def dropoff_nectar(agent):
    hives = [a for a in agent.model.grid[agent.pos] if a.type == "hive"]
    for hive in hives:
        if agent.pos == hive.pos:
            if len(agent.nectar_collected) > 0:
                for n in agent.nectar_collected:
                    agent.model.nectar_collected += n
                    hive.energy += n  # Add energy to hive
                agent.nectar_collected = []

                # Bee dance
                bee_dance(agent)
