import random

from bee_simulation.movement import MovingEntity
from bee_simulation.static_object import StaticObject

import bee_simulation.perception as perception
import bee_simulation.logic as logic
import bee_simulation.actions as actions
import bee_simulation.helpers as helpers

import numpy as np


class Bee(MovingEntity):
    def __init__(self, unique_id, pos, model, moore):
        super().__init__(unique_id, pos, model, moore=moore)

        # Agent parameters
        self.perception_range = self.model.perception_range
        self.max_energy = self.model.max_bee_energy

        # Private vars
        self.type = "bee"
        self.nectar_collected = []
        self.energy = self.max_energy
        self.clue_loc = None
        self.clue_grade = None

        # State
        self.state = "return_to_hive"
        # Options are:
        # - return_to_hive
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
        # Perception
        logic.update_memory(self, perception.percept(self))
        self.state = logic.update_state(self)
        print(f"Current State: {self.state}")

        # Logic
        if self.state == "return_to_hive":
            actions.return_to_hive(self)
        elif self.state == "explore":
            grid_scores = logic.calc_grid_scores(self)
            np.set_printoptions(precision=3, suppress=True)
            print(np.rot90(grid_scores))
            move_choice = np.unravel_index(np.argmax(grid_scores), grid_scores.shape)
            actions.move_to_target(self, move_choice)

            nectar_onsite = [a for a in self.model.grid[self.pos] if a.type == "nectar"]
            if len(nectar_onsite) > 0:
                nectar_pos = nectar_onsite[0].pos
                if nectar_pos == self.pos and nectar_pos==move_choice:
                    if grid_scores[nectar_pos] > 0 or self.model.collect_negative_value_nectar:
                        actions.collect_nectar(self, nectar_onsite[0])
                    else:
                        self.grid_memory[nectar_pos] = '/'

        else:
            exit(f"Invalid State: {self.state}")

        # Handle nectar
        if self.pos == self.hive_pos:
            actions.dropoff_nectar(self)
            actions.refill_energy(self)

        # Energy usage
        self.energy -= 1
        if self.energy <= 0:
            self.model.running = False


class FlowerField(StaticObject):
    def __init__(self, unique_id, pos, model, max_nectar_grade, respawn_interval):
        super().__init__(unique_id, pos, model)
        self.type = "flowerfield"
        self.grade = random.randrange(1, max_nectar_grade + 1)
        self.respawn_interval = respawn_interval
        self.steps_left_for_respawn = self.respawn_interval

    def step(self) -> None:
        self.steps_left_for_respawn -= 1
        if self.steps_left_for_respawn <= 0:
            self.steps_left_for_respawn = self.respawn_interval

            nectar_on_loc = [a for a in self.model.schedule.agents if a.type == "nectar" and a.pos == self.pos]
            if len(nectar_on_loc) > 0:
                nectar_on_loc[0].amount += 1
            else:
                p = Nectar(self.model.instance_last_id, self.pos, self, 1, self.grade)
                self.model.grid.place_agent(p, self.pos)
                self.model.schedule.add(p)
                self.model.instance_last_id += 1


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
