import numpy as np
import bee_simulation.actions as actions
import bee_simulation.helpers as helpers


def update_memory(agent, perception, show_grid=False):
    for tile in perception:
        for entity in agent.model.grid[tile]:
            if entity.type == "nectar":  # remember nectar locations
                agent.grid_memory[tile] = entity.type
        if agent.grid_memory[tile] == '':  # '' is unobserved
            agent.grid_memory[tile] = 'o'  # o for observed

    if show_grid:
        print(np.rot90(agent.grid_memory))


def plan_rational_move(agent):
    if len(agent.nectar_collected) > 0:
        return "return_to_hive"
    else:
        if len(np.argwhere(agent.grid_memory == 'n')) != 0:
            return "fetch_closest_nectar"
        elif len(np.argwhere(agent.grid_memory == '')) == 0:
            return "return_to_hive"
        else:
            return "explore"


def plan_rational_move2(agent):
    if len(agent.nectar_collected) > 0:
        return "return_to_hive"
    else:
        if len(np.argwhere(agent.grid_memory == '')) == 0:
            return "return_to_hive"
        return "explore"


def calc_values_of_list(model, origin_pos, target_positions, grid_values, grid_memory, verbose=True):
    if verbose:
        value_grid = np.zeros(grid_values.shape, dtype=np.float)

    best = {"pos": (0, 0), "value": 1000}
    for pos in target_positions:
        nectar_multiplier = 0
        if grid_memory[pos] in ['o', 'x']:
            value = 1000
        else:
            if grid_memory[pos] == 'n':
                grade = next(nectar for nectar in model.grid[pos]).grade
                nectar_multiplier = - grade * 100
            d = helpers.calc_distance(origin_pos, pos)
            value = grid_values[pos] + d + nectar_multiplier

        if verbose:
            value_grid[pos] = value

        if value < best['value']:
            best['value'] = value
            best['pos'] = pos

    if verbose:
        print(np.rot90(value_grid))
    return best['pos']
