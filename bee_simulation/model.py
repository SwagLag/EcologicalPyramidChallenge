from bee_simulation import helpers
from bee_simulation.agents import Bee, Nectar, Hive, FlowerField
from mesa import Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from mesa.time import RandomActivation

import numpy as np

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
            init_flowers=3,
            init_max_nectar_grade=3,
            min_nectar=1,
            max_nectar=1,
            behaviourprobability=50,
            beedanceinaccuracy=3,
            beepatience=8
    ):
        if min_nectar > max_nectar:
            min_nectar = max_nectar
        self.height = height
        self.width = width

        # Server parameters
        self.init_people = init_bees
        self.init_nectar = init_flowers
        self.init_nectar_grade = init_max_nectar_grade

        # Agent parameters
        self.behaviourprobability = behaviourprobability
        self.beedanceinaccuracy = beedanceinaccuracy
        self.beepatience = beepatience

        self.schedule = RandomActivation(self)
        self.grid = MultiGrid(self.width, self.height, torus=False)

        self.nectar_collected = 0

        self.datacollector = DataCollector(
            model_reporters={
                "Nectar Collected": get_nectar_collected,
            },
        )

        # create people for the model according to number of people set by user
        self.instance_last_id = 0

        # Spawn Hives
        hive_loc = self.grid.find_empty()
        p = Hive(self.instance_last_id, hive_loc, self)
        self.grid.place_agent(p, hive_loc)
        self.schedule.add(p)
        self.running = True
        self.datacollector.collect(self)
        self.instance_last_id += 1

        # Spawn Bees
        for i in range(self.init_people):
            # empty_loc = self.grid.find_empty()
            p = Bee(self.instance_last_id, hive_loc, self, False)
            self.grid.place_agent(p, hive_loc)
            self.schedule.add(p)
            self.instance_last_id += 1

        # Spawn Flowerfields and accompanying Nectar
        for i in range(0, self.init_nectar):
            flower_loc = self.grid.find_empty()
            grade = np.random.randint(1, init_max_nectar_grade + 1)
            p = FlowerField(self.instance_last_id, flower_loc, self, grade)
            self.grid.place_agent(p, flower_loc)
            self.instance_last_id += 1  # Don't want both flowerfield and nectar to have the same ID

            amount = np.random.randint(min_nectar, max_nectar + 1)
            p = Nectar(self.instance_last_id, flower_loc, self, amount, p.grade)
            self.grid.place_agent(p, flower_loc)
            self.schedule.add(p)
            self.instance_last_id += 1

    def step(self):
        # tell all the agents in the model to run their step function
        self.schedule.step()
        # collect data
        self.datacollector.collect(self)

    def run_model(self):
        for i in range(self.run_time):
            self.step()


    # def swap_bee(self, bee, hive_loc, clue_loc=False):
    #     self.instance_last_id += 1
    #     p = Bee(self.instance_last_id, hive_loc, self, False)
    #     self.grid.place_agent(p, hive_loc)
    #     self.schedule.add(p)
    #
    #     if clue_loc is not False:
    #         gv = p.grid_values
    #         p.grid_values -= helpers.generate_grid_values(self, clue_loc, update=gv)
    #
    #     # self.grid.remove_agent(bee)
