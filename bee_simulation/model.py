from bee_simulation.agents import Bee, Nectar, Hive, Flowerfield
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
            min_nectar=1,
            max_nectar=1,
            min_grd_nectar=1,
            max_grd_nectar=3
    ):
        if min_nectar > max_nectar:
            min_nectar = max_nectar
        self.height = height
        self.width = width
        self.init_people = init_bees
        self.init_nectar = init_flowers
        self.min_nectar = min_nectar
        self.max_nectar = max_nectar
        self.grades_nectar = [x for x in range(min_grd_nectar,max_grd_nectar+1)]
        np.random.shuffle(self.grades_nectar)  # Numpy shuffle can only be done in-place, no assignment necessary.
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
            p = Bee(self.instance_last_id, hive_loc, self, init_flowers, False)
            self.grid.place_agent(p, hive_loc)
            self.schedule.add(p)
            self.instance_last_id += 1

        # Spawn Flowerfields and accompanying Nectar
        for i in range(0, self.init_nectar):

            if len(self.grades_nectar) > 0:
                grade = self.grades_nectar.pop()
            else:
                grade = 1

            flower_loc = self.grid.find_empty()
            p = Flowerfield(self.instance_last_id, flower_loc, self, grade)
            self.grid.place_agent(p, flower_loc)
            self.instance_last_id += 1  # Don't want both flowerfield and nectar to have the same ID
            p.spawn_nectar()

    def step(self):
        # tell all the agents in the model to run their step function
        self.schedule.step()
        # collect data
        self.datacollector.collect(self)

    def run_model(self):
        for i in range(self.run_time):
            self.step()
