from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.UserParam import UserSettableParameter
from bee_simulation.agents import Bee, Nectar, Hive, FlowerField
from bee_simulation.model import BeeSimulation

# Green
BEE_COLOR = "#000000"
NECTAR_COLOR = "#FFA500"
HIVE_COLOR = "#964B00"
FLOWERFIELD_COLOR = "#008000"


def agent_portrayal(agent):
    if agent is None:
        return

    portrayal = {}

    # update portrayal characteristics for each object
    if isinstance(agent, Bee):
        portrayal["Shape"] = "circle"
        portrayal["r"] = 0.5
        portrayal["Layer"] = 3
        portrayal["Filled"] = "true"

        if len(agent.nectar_collected) > 0:
            portrayal["Color"] = "Black"
        else:
            portrayal["Color"] = "Gray"

    if isinstance(agent, Nectar):
        portrayal["Shape"] = "circle"
        portrayal["r"] = 0.3
        portrayal["Layer"] = 1
        portrayal["Filled"] = "true"
        portrayal["Color"] = NECTAR_COLOR
        portrayal["text"] = f"a:{agent.amount},g:{agent.grade}"
        portrayal["text_color"] = "Black"

    if isinstance(agent, Hive):
        portrayal["Shape"] = "rect"
        portrayal["w"] = 0.5
        portrayal['h'] = 0.5
        portrayal["Layer"] = 2
        portrayal["Filled"] = "true"
        portrayal["Color"] = HIVE_COLOR

    if isinstance(agent, FlowerField):
        portrayal["Shape"] = "rect"
        portrayal["w"] = 0.4
        portrayal['h'] = 0.4
        portrayal["Layer"] = 0
        portrayal["Filled"] = "true"
        portrayal["Color"] = FLOWERFIELD_COLOR

    return portrayal


# dictionary of user settable parameters - these map to the model __init__ parameters
model_params = {
    # "init_bees": UserSettableParameter(
    #     "slider", "Bees", 1, 1, 10, description="Initial Number of Bees"
    # ),
    "t1":UserSettableParameter('static_text', value="Space parameters"),
    "init_flowers": UserSettableParameter(
        "slider", "# of flowerfields", 5, 1, 20, description="Number of flower fields"
    ),
    "min_nectar": UserSettableParameter(
        "slider", "Initial minimum # of nectar per flower", 2, 1, 10, description="Minimum nectar available in flowerfields"
    ),
    "max_nectar": UserSettableParameter(
        "slider", "Initial maximum # of nectar per flower", 4, 1, 10, description="Maximum nectar available in flowerfields"
    ),
    "t2":UserSettableParameter('static_text', value="Nectar parameters"),
    "init_min_nectar_grade": UserSettableParameter(
        "slider", "Minimum nectar grade", 5, 1, 100, description="Minimum nectar grade"
    ),
    "init_max_nectar_grade": UserSettableParameter(
        "slider", "Maximum nectar grade", 25, 10, 50, description="Maximum nectar grade"
    ),
    "nectar_respawn_interval": UserSettableParameter(
        "slider", "Nectar respawn interval", 75, 10, 200, description="Nectar respawn interval"
    ),
    "t3": UserSettableParameter('static_text', value="Bee parameters"),
    "max_bee_energy": UserSettableParameter(
        "slider", "Max bee energy", 30, 10, 100, description="Max bee energy"
    ),
    "collect_negative_value_nectar": UserSettableParameter(
        'checkbox', 'Collect negative value nectar', value=True
    ),
    "perception_range":UserSettableParameter(
        'choice', 'Perception range', value=1,
        choices=[1, 2, 3]
    ),
    # "behaviourprobability": UserSettableParameter(
    #     "slider", "Bee Behaviour Probability", 50, 0, 100, description="Probability that the bee will"
    #                                                                    "explore instead of going for the clue,"
    #                                                                    "the inverse (1-%) for going for the clue"
    #                                                                    "first."
    # ),
    # "beedanceinaccuracy": UserSettableParameter(
    #     "slider", "Bee Dance Inaccuracy", 3, 0, 8, description="Radius in which a given clue can generate in from"
    #                                                            "a nectar's actual position."
    # ),
    # "beepatience": UserSettableParameter(
    #     "slider", "Bee Search Duration", 8, 0, 8, description="Time steps that the bee will spend searching before"
    #                                                           "giving up and returning to a default explore state."
    # ),
}

# set the portrayal function and size of the canvas for visualization
canvas_element = CanvasGrid(agent_portrayal, 10, 10, 500, 500)

# map data to chart in the ChartModule
chart_element = ChartModule(
    [
    {"Label": "Nectar stored", "Color": HIVE_COLOR},
    {"Label": "Bee energy", "Color": BEE_COLOR},
    ]
)

chart_element2 = ChartModule(
    [
        {"Label": "Nectar Collected", "Color": NECTAR_COLOR},
    ]
)
# create instance of Mesa ModularServer
server = ModularServer(
    BeeSimulation,
    [canvas_element, chart_element, chart_element2],
    "Dance of the Bees",
    model_params=model_params,
)
