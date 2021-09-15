from bee_simulation.agents import Bee, Nectar, Hive
from mesa import Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from mesa.time import RandomActivation


# Start of datacollector functions
def get_nectar_collected(model):
    return model.nectar_collected


class BeeSimulation(Model):
    # grid height
    grid_h = 6
    # grid width
    grid_w = 6

    """init parameters "init_people", "rich_threshold", and "reserve_percent"
       are all UserSettableParameters"""

    def __init__(
            self,
            height=grid_h,
            width=grid_w,
            init_bees=1,
            init_nectar=1
    ):
        self.height = height
        self.width = width
        self.init_people = init_bees
        self.init_nectar = init_nectar
        self.schedule = RandomActivation(self)
        self.grid = MultiGrid(self.width, self.height, torus=False)

        self.nectar_collected = 0

        self.datacollector = DataCollector(
            model_reporters={
                "Nectar Collected": get_nectar_collected,
            },
        )

        # create people for the model according to number of people set by user
        instance_last_id = 0

        # Spawn Hives
        hive_loc = self.grid.find_empty()
        p = Hive(instance_last_id, hive_loc, self)
        self.grid.place_agent(p, hive_loc)
        self.schedule.add(p)
        self.running = True
        self.datacollector.collect(self)
        instance_last_id += 1

        # Spawn Bees
        for i in range(self.init_people):
            # empty_loc = self.grid.find_empty()
            p = Bee(instance_last_id, hive_loc, self, True)
            self.grid.place_agent(p, hive_loc)
            self.schedule.add(p)
            instance_last_id += 1

        # Spawn Nectar
        for i in range(0, self.init_nectar):
            empty_loc = self.grid.find_empty()
            p = Nectar(instance_last_id, empty_loc, self)
            self.grid.place_agent(p, empty_loc)
            self.schedule.add(p)
            instance_last_id += 1

    def step(self):
        # tell all the agents in the model to run their step function
        self.schedule.step()
        # collect data
        self.datacollector.collect(self)

    def run_model(self):
        for i in range(self.run_time):
            self.step()
