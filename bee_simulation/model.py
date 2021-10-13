import random

from bee_simulation.agents import Bee, Nectar, Hive, FlowerField
from mesa import Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from mesa.time import RandomActivation

import numpy as np
import bee_simulation.helpers as helpers


# Start of datacollector functions
def get_nectar_collected(model):
    return model.nectar_collected


def get_nectar_per_t(model):
    return (get_nectar_collected(model)/(max(1,model.steps_past)))


def get_hive_energy(model):
    return model.tracked_hive.energy


def get_bee_energy(model):
    return model.tracked_bee.energy

def get_steps(model):
    return model.steps_past


# --------------------------------

class BeeSimulation(Model):
    # grid height
    grid_h = 20
    # grid width
    grid_w = 20

    """init parameters "init_people", "rich_threshold", and "reserve_percent"
       are all UserSettableParameters"""

    def __init__(self, height=grid_h, width=grid_w, init_bees=1, init_flowers=6, init_min_nectar_grade=1,
                 init_max_nectar_grade=30, min_nectar=1, max_nectar=1, nectar_respawn_interval=50,
                 collect_negative_value_nectar=True,
                 perception_range=1, max_bee_energy=30, preset=False, max_clue_radius=1, min_flower_distance=5,
                 hivemind_events=True, hivemind_interval=1):

        super().__init__()
        helpers.gen_linspace()
        self.height = height
        self.width = width
        self.steps_past = 0

        # Server parameters
        if min_nectar > max_nectar:
            min_nectar = max_nectar
        self.init_bees = init_bees
        self.init_flowers = init_flowers
        self.init_nectar_grade = init_max_nectar_grade
        self.collect_negative_value_nectar = collect_negative_value_nectar
        self.perception_range = perception_range
        self.max_bee_energy = max_bee_energy
        self.init_min_nectar_grade = init_min_nectar_grade
        self.init_max_nectar_grade = init_max_nectar_grade
        self.preset = preset
        self.max_clue_radius = max_clue_radius
        self.min_flower_distance = min_flower_distance
        self.hivemind_events = hivemind_events
        self.hivemind_interval = hivemind_interval

        # Agent parameters
        # self.behaviourprobability = behaviourprobability
        # self.beedanceinaccuracy = beedanceinaccuracy
        # self.beepatience = beepatience

        self.schedule = RandomActivation(self)
        self.grid = MultiGrid(self.width, self.height, torus=False)

        self.nectar_collected = 0

        self.instance_last_id = 0

        # Spawn Hives

        if not self.preset:
            hive_loc = (10,10)
            # hive_loc = self.grid.find_empty()
        else:
            hive_loc = (10, 10)

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
        locations_flowers = [(3, 1), (3, 4), (1, 4), (5, 8), (14, 5),(16, 13), (6, 4), (2, 8), (12, 18), (18, 17)]
        for i in range(0, self.init_flowers):
            if not self.preset:
                while True:
                    flower_loc = self.grid.find_empty()
                    if helpers.calc_distance(flower_loc, hive_loc) >= self.min_flower_distance:
                        break
            else:
                flower_loc = locations_flowers[i]
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
                "Steps past": get_steps,
            },
            agent_reporters={}
        )
        self.running = True
        self.datacollector.collect(self)

    def step(self):
        # Survival:
        if sum([x.alive for x in self.schedule.agents if isinstance(x, Bee)]) == 0:
            self.running = False

        # Events:
        # After a certain amount of steps, a hivemind signal gets sent
        # ∀a ∀b ∃c((Bee(a) ˄ Bee(b) ˄ Model(c) ˄ IsZero(HiveMindCounter(c)) -> HiveMind(a, b))
        if (self.schedule.steps + 1) % self.hivemind_interval == 0 and self.hivemind_events:
            bees = [x for x in self.schedule.agents if isinstance(x, Bee) and len(x.nectar_collected) == 0]
            # Alleen vrije bijen worden meegenomen in de taakverdeling.
            gk_grade, gk_amount = helpers.gather_gridknowledge(self)
            tasks = helpers.gather_tasks_bees(gk_grade, gk_amount, len(bees))

            valuedataframe = helpers.generate_valuedataframe(bees, tasks)
            assignments = helpers.assign_tasks(valuedataframe)
            translated = helpers.translate_assignments(assignments, bees, tasks)
            # print(translated)
            for assignment in translated:
                agent = assignment[0]
                task = assignment[1]
                print(task.type)

                if task.type == 'explore':
                    if agent.state != 'explore':
                        agent.state = 'explore'
                        agent.clue_pos = (random.randint(0, self.height), random.randint(0, self.width))
                        agent.clue_grade = 1000
                else:  # Fetch nectar
                    print(task.type)
                    agent.state = 'fetch_nectar'
                    agent.clue_pos = task.pos
                    agent.clue_grade = 10000
                    agent.init_clue = False
                    agent.explore_clue = None


        # Main loop:
        # tell all the agents in the model to run their step function
        self.schedule.step()
        # collect data
        self.steps_past += 1
        self.datacollector.collect(self)

    def run_model(self):
        for i in range(self.run_time):
            self.step()
