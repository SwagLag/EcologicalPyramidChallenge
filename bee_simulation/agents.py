import random

from bee_simulation.movement import MovingEntity
from bee_simulation.static_object import StaticObject

import bee_simulation.perception as perception
import bee_simulation.logic as logic
import bee_simulation.actions as actions
import bee_simulation.helpers as helpers

import numpy as np


# subclass of RandomWalker, which is subclass to Mesa Agent
class Bee(MovingEntity):
    def __init__(self, unique_id, pos, model, moore):
        # init parent class with required parameters
        super().__init__(unique_id, pos, model, moore=moore)

        # Agent parameters
        self.perception_range = 1
        self.max_energy = 20

        # Private vars
        self.type = "bee"
        self.nectar_collected = []
        self.energy = self.max_energy
        self.clue_loc = None

        # State
        self.state = "return_to_hive"
        # Options are:
        # - return_to_hive
        # - fetch_closest_nectar
        # - explore

        # Init grid memory
        self.hive_pos = None
        self.grid_memory = self.init_grid_memory(self)

        # Grid values
        self.grid_values = helpers.generate_grid_costs(self, self.hive_pos)

    def init_grid_memory(self, agent):
        # Initiating grid memory for logic inferencing (and put in hive locations)
        grid_memory = np.zeros([self.model.grid_w, self.model.grid_h], dtype=np.str)
        for hive in [a for a in self.model.schedule.agents if a.type == "hive"]:
            grid_memory[hive.pos] = "x"
            agent.hive_pos = hive.pos
        return grid_memory

    def step(self):
        actions.handle_nectar(self)
        logic.update_memory(self, perception.percept(self))
        self.state = logic.update_state(self)

        # Energy usage
        self.energy -= 1
        # if self.energy <= 0:
        #     self.model.running = False

        print(f"Current State: {self.state}")

        if self.state == "return_to_hive":
            actions.return_to_hive(self)
        elif self.state == "fetch_closest_nectar":
            actions.fetch_closest_nectar(self)
        elif self.state == "explore":
            grid_scores = logic.calc_grid_scores(self)
            np.set_printoptions(precision=3, suppress=True)
            print(np.rot90(grid_scores))
            move_choice = np.unravel_index(np.argmax(grid_scores), grid_scores.shape)
            actions.move_to_target(self, move_choice)
        else:
            exit(f"Invalid State: {self.state}")


class FlowerField(StaticObject):
    def __init__(self, unique_id, pos, model, max_nectar_grade):
        super().__init__(unique_id, pos, model)
        self.type = "flowerfield"
        self.grade = random.randrange(1, max_nectar_grade + 1)
        self.respawn_interval = 1
        self.steps_left_for_respawn = self.respawn_interval

    def step(self) -> None:
        self.steps_left_for_respawn -= 1
        if self.steps_left_for_respawn <= 0:
            self.steps_left_for_respawn = self.respawn_interval

            nectar_on_loc = [a for a in self.model.schedule.agents if a.type == "nectar" and a.pos == self.pos]
            if len(nectar_on_loc) > 0:
                nectar_on_loc.amount += 1
            else:
                p = Nectar(self.model.instance_last_id, self.pos, self, 1, self.grade)
                self.grid.place_agent(p, self.pos)
                self.model.schedule.add(p)
                self.instance_last_id += 1


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
        self.energy = 20

    # step is called for each agent in model.BeeModel.schedule.step()
