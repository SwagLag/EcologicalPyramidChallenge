import random

from bee_simulation.movement import MovingEntity
from bee_simulation.static_object import StaticObject

import bee_simulation.perception as perception
import bee_simulation.logic as logic
import bee_simulation.actions as actions

import numpy as np


# subclass of RandomWalker, which is subclass to Mesa Agent
class Bee(MovingEntity):
    def __init__(self, unique_id, pos, model, moore):
        # init parent class with required parameters
        super().__init__(unique_id, pos, model, moore=moore)

        # Private vars
        self.type = "bee"
        self.nectar_collected = []

        # State
        self.state = "return_to_hive"
        # Options are:
        # - return_to_hive
        # - fetch_closest_nectar
        # - explore

        # Agent parameters
        self.perception_range = 1

        # Initiating grid memory for logic inferencing (and put in hive locations)
        self.grid_memory = np.zeros([self.model.grid_w, self.model.grid_h], dtype=np.str)
        for hive in [a for a in self.model.schedule.agents if a.type == "hive"]:
            self.grid_memory[hive.pos] = "x"

    def step(self):
        actions.handle_nectar(self)
        logic.update_memory(self, perception.percept(self))
        self.state = logic.plan_rational_move(self)

        print(f"Current State: {self.state}")

        if self.state == "return_to_hive":
            actions.return_to_hive(self)
        elif self.state == "fetch_closest_nectar":
            actions.fetch_closest_nectar(self)
        elif self.state == "explore":
            actions.explore(self)
        else:
            exit(f"Invalid State: {self.state}")

class FlowerField(StaticObject):
    def __init__(self, unique_id, pos, model, max_nectar_grade):
        super().__init__(unique_id, pos, model)
        self.type = "flowerfield"
        self.grade = random.randrange(1, max_nectar_grade+1)


class Nectar(StaticObject):
    def __init__(self, unique_id, pos, model, amount, grade):
        super().__init__(unique_id, pos, model)
        self.type = "nectar"
        self.amount = amount
        self.grade = grade


class Hive(StaticObject):
    def __init__(self, unique_id, pos, model):
        super().__init__(unique_id, pos, model)
        self.type = "hive"

    # step is called for each agent in model.BeeModel.schedule.step()
