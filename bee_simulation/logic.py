import mesa
import numpy as np
import bee_simulation.helpers as helpers
import bee_simulation.agents as agents
from typing import List, Union


def update_memory(agent, perception, show_grid=False):
    for tile in perception:
        for entity in agent.model.grid[tile]:
            if entity.type == "nectar" and agent.grid_memory[tile] != '/':  # remember nectar locations
                agent.grid_memory[tile] = "nectar"
        if agent.grid_memory[tile] == '':  # '' is unobserved
            agent.grid_memory[tile] = 'o'  # o for observed

    if show_grid:
        print(np.rot90(agent.grid_memory))


def update_state(agent):
    if helpers.calc_distance(agent.pos, agent.hive_pos) >= agent.energy - 1 and agent.pos != agent.hive_pos:
        # ∀a ∃k ((Bee(a) ˄ Beehive(k) ˄ NeedToGoHome(TicksToHome(a, k), TicksOfEnergy(a)) -> GoHome(a, b)))
        # When a bee has just enough energy to go home, he will go home
        return "return_to_hive"
    if len(agent.nectar_collected) > 0:
        # ∀a ∃k ((Bee(a) ˄ Beehive(k) ˄ HasNectar(a)) -> GoHome(a, k)))
        # If a bee has collected nectar, he wants to go home
        return "return_to_hive"
    if len(np.argwhere(agent.grid_memory == '')) == 0:
        # ∀a ∃g ∃k((Bee(a) ˄ Beehive(k) ˄ GridExplored(g)) -> GoHome(a, k)))
        # When a bee has explored the whole grid, he will go home
        return "return_to_hive"
    return "explore"


def calc_grid_scores(agent):
    grid_cost_base = helpers.generate_grid_costs(agent, nexus_pos=agent.hive_pos)
    grid_cost_cpos = helpers.generate_grid_costs(agent, nexus_pos=agent.pos, from_agent=True)
    grid_gain_gain = helpers.generate_grid_gain(agent, clue_loc=agent.clue_loc, clue_grade=agent.clue_grade)

    # print("grid_cost_base:\n",np.rot90(grid_cost_base))
    # print("grid_cost_cpos:\n",np.rot90(grid_cost_cpos))
    # print("grid_gain_wclue:\n",np.rot90(grid_gain_gain))

    grid_scores = - grid_cost_base - grid_cost_cpos + grid_gain_gain
    grid_scores = np.clip(grid_scores, -1000, 1000)
    return grid_scores


def touch(agent_a: mesa.Agent, agent_b: mesa.Agent):
    """∀a ∀b ∃p ((PhysicalConcept(a) ˄ PhysicalConcept(b) ˄ Tile(p) ˄ (IsAt(a, p) ˄ IsAt(b, p)) -> Touch(a, b))).
    When a two physical concepts are on the same square, they touch."""

    if agent_a.pos == agent_b.pos:
        return True
    return False


def bee_die(bee):
    """∀a ((Bee(a) ˄ NoEnergy(a)) -> Die(a)). When a bee has nog energy left, it will die."""

    if bee.energy <= 0:
        bee.model.running = False
