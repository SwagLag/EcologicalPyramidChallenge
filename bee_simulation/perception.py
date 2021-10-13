def percept(agent):
    """What the bee percepts after it has moved."""
    perception = agent.model.grid.get_neighborhood(agent.pos, agent.moore, include_center=True,
                                                  radius=agent.perception_range)
    return perception
