def percept(agent):
    perception = agent.model.grid.get_neighborhood(agent.pos, agent.moore, include_center=True,
                                                  radius=agent.perception_range)
    return perception
