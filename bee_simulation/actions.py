import random

import numpy as np

from bee_simulation import helpers
from bee_simulation.helpers import calc_closest_of_list
import bee_simulation.logic as logic


def move_to_target(agent, target_pos):
    """Calculate which tile the agent want to go to next in order to go to their target."""

    # We want our agent to go in a 'straight line' towards its target. To simulate this, we want him to randomly prefer
    # moving along the x or y coördinates.

    first_x = random.choice([True, False])
    if first_x:
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

    else:
        if target_pos[1] < agent.pos[1]:
            agent.model.grid.move_agent(agent, (agent.pos[0], agent.pos[1] - 1))
        elif target_pos[1] > agent.pos[1]:
            agent.model.grid.move_agent(agent, (agent.pos[0], agent.pos[1] + 1))
        elif target_pos[0] < agent.pos[0]:
            agent.model.grid.move_agent(agent, (agent.pos[0] - 1, agent.pos[1]))
        elif target_pos[0] > agent.pos[0]:
            agent.model.grid.move_agent(agent, (agent.pos[0] + 1, agent.pos[1]))
        elif target_pos[0] == agent.pos[0] and target_pos[1] == agent.pos[1]:
            print("move_to_target origin same as target")
        else:
            exit(f"move_to_target error,current_position:{agent.pos}, target:{target_pos}")


def return_to_hive(agent):
    """The bee wants to return to the hive."""
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
        agent.init_clue = False
        # Put clue into grid values
        true_clue_loc = random.choice(nectar_positions)
        clue_loc = helpers.gen_clue_tile(agent.model, true_clue_loc, agent.model.max_clue_radius)
        # print(f"True loc:{true_clue_loc}, Clue loc:{clue_loc}")
        nectar = [a for a in agent.model.grid[true_clue_loc] if a.type == "nectar"]
        if len(nectar) > 0:
            agent.clue_grade = nectar[0].grade
            agent.clue_loc = clue_loc
        else:
            agent.init_clue = True
            agent.clue_loc = (random.randint(0, agent.model.height), random.randint(0, agent.model.width))
            agent.clue_grade = 1000
    else:
        agent.init_clue = True
        agent.clue_loc = (random.randint(0, agent.model.height), random.randint(0, agent.model.width))
        agent.clue_grade = 1000


def refill_energy(agent):
    """Bee restores energy when entering the hive."""
    hive = [a for a in agent.model.grid[agent.pos] if a.type == "hive"][0]
    refill_amount = abs(agent.max_energy - agent.energy)

    # The bee gains energy and the hive loses energy when the bee stands on the hive
    # ∀a ∃k ∃f((Bee(a) ˄ Beehive(k) ˄ FlowerField(f) ˄ Touch(a, k)) -> (GainHoney(k) ˄ LoseNectar(a)))
    if hive.energy >= refill_amount:
        hive.energy -= refill_amount
        agent.energy += refill_amount
    else:
        agent.energy += hive.energy
        hive.energy = 0


def collect_nectar(agent, nectar):
    """Bee collects nectar from flowerfield."""

    # When a bee stands on a flowerfield, hasn't gathered any nectar yet and the flowerfield does contain nectar, then
    # the bee will collect this nectar
    # ∀a ∀b ((Bee(a) ˄ FlowerField(b) ˄ ¬ HasNectar(a) ˄ (Touch(a, b) ˄ Nectar(b))) -> (GainNectar(a) ˄ LoseNectar(b)))
    if len(agent.nectar_collected) == 0:
        agent.nectar_collected.append(nectar.grade)
        if nectar.amount == 1:
            agent.model.grid.remove_agent(nectar)
            agent.grid_memory[agent.pos] = 'o'
        else:
            nectar.amount -= 1


def dropoff_nectar(agent):
    """A bee drops of his nectar."""
    hives = [a for a in agent.model.grid[agent.pos] if a.type == "hive"]
    for hive in hives:
        if logic.touch(agent.pos, hive.pos):
            if len(agent.nectar_collected) > 0:
                for n in agent.nectar_collected:
                    agent.model.nectar_collected += n
                    hive.energy += n  # Add energy to hive
                agent.nectar_collected = []

                # Bee dance
                bee_dance(agent)
