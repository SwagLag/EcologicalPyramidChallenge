import random

from bee_simulation.movement import MovingEntity
from bee_simulation.static_object import StaticObject

import numpy as np


# subclass of RandomWalker, which is subclass to Mesa Agent
class Bee(MovingEntity):
    def __init__(self, unique_id, pos, model, moore):
        # init parent class with required parameters
        super().__init__(unique_id, pos, model, moore=moore)

        # Private vars
        self.type = "bee"
        self.nectar_collected = []

        # Agent parameters
        self.perception_range = 1

        # Initiating grid memory for logic inferencing (and put in hive locations)
        self.grid_memory = np.zeros([self.model.grid_w, self.model.grid_h], dtype=np.str)
        for hive in [a for a in self.model.schedule.agents if a.type == "hive"]:
            self.grid_memory[hive.pos] = "x"

    def handle_nectar(self):
        nectars = [a for a in self.model.grid[self.pos] if a.type == "nectar"]
        hives = [a for a in self.model.grid[self.pos] if a.type == "hive"]
        # Dropping of Nectar
        for hive in hives:
            if self.pos == hive.pos and len(self.nectar_collected) > 0:
                for n in self.nectar_collected:
                    self.model.nectar_collected += n
                self.nectar_collected = []

        # Collection of Nectar
        for nectar in nectars:
            if self.pos == nectar.pos:
                if len(self.nectar_collected) == 0:
                    self.nectar_collected.append(nectar.grade)
                    if nectar.amount == 1:
                        self.model.grid.remove_agent(nectar)
                        self.grid_memory[self.pos] = 'o'
                    else:
                        nectar.amount -= 1


    def update_world_knowledge(self, verbose=False):
        perception = self.model.grid.get_neighborhood(self.pos, self.moore, include_center=True,
                                                      radius=self.perception_range)
        for tile in perception:
            for entity in self.model.grid[tile]:
                if entity.type == "nectar":  # remember nectar locations
                    self.grid_memory[tile] = entity.type
            if self.grid_memory[tile] == '':  # '' is unobserved
                self.grid_memory[tile] = 'o'  # o for observed

        if verbose:
            # print(self.grid_memory)
            print(np.rot90(self.grid_memory))

    def move_to_target(self, target_pos):
        # X then Y method
        if target_pos[0] < self.pos[0]:
            self.model.grid.move_agent(self, (self.pos[0] - 1, self.pos[1]))
        elif target_pos[0] > self.pos[0]:
            self.model.grid.move_agent(self, (self.pos[0] + 1, self.pos[1]))
        elif target_pos[1] < self.pos[1]:
            self.model.grid.move_agent(self, (self.pos[0], self.pos[1] - 1))
        elif target_pos[1] > self.pos[1]:
            self.model.grid.move_agent(self, (self.pos[0], self.pos[1] + 1))
        else:
            print(f"move_to_target error,current_position:{self.pos}, target:{target_pos}")

    def _calc_distance(self, origin, target_pos):
        return abs(origin.pos[0] - target_pos[0]) + abs(origin.pos[1] - target_pos[1])

    def _calc_closest_of_list(self, origin, target_positions):
        best = {"pos": (0, 0), "distance": 100000000}
        for pos in target_positions:
            d = origin._calc_distance(origin, pos)
            if d < best['distance']:
                best['distance'] = d
                best['pos'] = pos
        return best['pos']

    def return_to_hive(self):
        # hives = [a.pos for a in self.model.schedule.agents if a.type == "hive" and a.pos is not None]
        hives = np.argwhere(self.grid_memory == 'x')
        self.move_to_target(self._calc_closest_of_list(self, hives))

    def fetch_closest_nectar(self):
        # nectar = [a.pos for a in self.model.schedule.agents if a.type == "nectar" and a.pos != None]
        nectar = np.argwhere(self.grid_memory == 'n')
        self.move_to_target(self._calc_closest_of_list(self, nectar))

    def explore(self):
        unexplored = np.argwhere(self.grid_memory == '')
        self.move_to_target(self._calc_closest_of_list(self, unexplored))

    def plan_rational_move(self):
        pass

    def step(self):
        self.handle_nectar()
        self.update_world_knowledge(verbose=True)

        if len(self.nectar_collected) > 0:
            print("return_to_hive")
            self.return_to_hive()
        else:
            if len(np.argwhere(self.grid_memory == 'n')) != 0:
                print("fetch_closest_nectar")
                self.fetch_closest_nectar()
            elif len(np.argwhere(self.grid_memory == '')) == 0:
                print("return_to_hive")
                self.return_to_hive()
            else:
                print("explore")
                self.explore()


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
