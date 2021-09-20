import numpy as np

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
