from bee_simulation.agents import Bee, Nectar, Hive, FlowerField
from mesa import Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from mesa.time import RandomActivation

import numpy as np


# Start of datacollector functions
def get_nectar_collected(model):
    return model.nectar_collected


def get_nectar_per_t(model):
    return (get_nectar_collected(model)/(max(1,model.steps_past)))


def get_hive_energy(model):
    return model.tracked_hive.energy


def get_bee_energy(model):
    return model.tracked_bee.energy


# --------------------------------

class BeeSimulation(Model):
    # grid height
    grid_h = 10
    # grid width
    grid_w = 10

    """init parameters "init_people", "rich_threshold", and "reserve_percent"
       are all UserSettableParameters"""

    def __init__(self, height=grid_h, width=grid_w, init_bees=1, init_flowers=6, init_min_nectar_grade=1,
                 init_max_nectar_grade=30, min_nectar=1, max_nectar=1, nectar_respawn_interval=50,
                 collect_negative_value_nectar=True,
                 perception_range=1, max_bee_energy=30):

        super().__init__()
        self.height = height
        self.width = width
        self.steps_past = 0

        # Server parameters
        min_nectar = min_nectar
        if min_nectar > max_nectar:
            min_nectar = max_nectar
        self.init_bees = init_bees
        self.init_flowers = init_flowers
        self.init_nectar_grade = init_max_nectar_grade
        self.collect_negative_value_nectar = collect_negative_value_nectar
        self.perception_range = perception_range
        self.max_bee_energy = max_bee_energy

        # Agent parameters
        # self.behaviourprobability = behaviourprobability
        # self.beedanceinaccuracy = beedanceinaccuracy
        # self.beepatience = beepatience

        self.schedule = RandomActivation(self)
        self.grid = MultiGrid(self.width, self.height, torus=False)

        self.nectar_collected = 0

        self.instance_last_id = 0

        # Spawn Hives
        hive_loc = self.grid.find_empty()
        p = Hive(self.instance_last_id, hive_loc, self)
        self.tracked_hive = p  # For model reporter
        self.grid.place_agent(p, hive_loc)
        self.schedule.add(p)
        self.instance_last_id += 1

        # Spawn Bees
        for i in range(self.init_bees):
            # empty_loc = self.grid.find_empty()
            p = Bee(self.instance_last_id, hive_loc, self, False)
            self.tracked_bee = p  # for model reporter
            self.grid.place_agent(p, hive_loc)
            self.schedule.add(p)
            self.instance_last_id += 1

        # Spawn Flowerfields and accompanying Nectar
        for i in range(0, self.init_flowers):
            flower_loc = self.grid.find_empty()
            grade = np.random.randint(init_min_nectar_grade, init_max_nectar_grade + 1)
            p = FlowerField(self.instance_last_id, flower_loc, self, grade, nectar_respawn_interval)
            self.schedule.add(p)
            self.grid.place_agent(p, flower_loc)
            self.instance_last_id += 1  # Don't want both flowerfield and nectar to have the same ID

            amount = np.random.randint(min_nectar, max_nectar + 1)
            p = Nectar(self.instance_last_id, flower_loc, self, amount, p.grade)
            self.grid.place_agent(p, flower_loc)
            self.instance_last_id += 1

        self.datacollector = DataCollector(
            model_reporters={
                "Nectar/T": get_nectar_per_t,
                "Bee energy": get_bee_energy,
                "Nectar stored": get_hive_energy,
                "Nectar Collected": get_nectar_collected,
            },
        )
        self.running = True
        self.datacollector.collect(self)

    def step(self):
        # tell all the agents in the model to run their step function
        self.schedule.step()
        # collect data
        self.steps_past+=1
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
