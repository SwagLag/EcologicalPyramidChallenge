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
        self.nectar_amount = 0

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
            if self.pos == hive.pos and self.nectar_amount > 0:
                self.model.nectar_collected += self.nectar_amount
                self.nectar_amount = 0

        # Collection of Nectar
        for nectar in nectars:
            if self.pos == nectar.pos:
                if self.nectar_amount <= 0:  # Collect Nectar if not loaded (Support for carrying more nectar at once later)
                    if nectar.amount <= 1:
                        self.nectar_amount += 1
                        self.model.grid.remove_agent(nectar)
                        self.grid_memory[self.pos] = 'o'
                    else:
                        self.nectar_amount += 1
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

    def _calc_distance(self, target_pos):
        return abs(self.pos[0] - target_pos[0]) + abs(self.pos[1] - target_pos[1])

    def _calc_closest_of_list(self, target_positions):
        best = {"pos": (0, 0), "distance": 100000000}
        for pos in target_positions:
            d = self._calc_distance(pos)
            if d < best['distance']:
                best['distance'] = d
                best['pos'] = pos
        return best['pos']

    def return_to_hive(self):
        hives = [a.pos for a in self.model.schedule.agents if a.type == "hive" and a.pos is not None]
        self.move_to_target(self._calc_closest_of_list(hives))

    def fetch_closest_nectar(self):
        # nectar = [a.pos for a in self.model.schedule.agents if a.type == "nectar" and a.pos != None]
        nectar = np.argwhere(self.grid_memory == 'n')
        self.move_to_target(self._calc_closest_of_list(nectar))

    def explore(self):
        unexplored = np.argwhere(self.grid_memory == '')
        self.move_to_target(self._calc_closest_of_list(unexplored))

    # step is called for each agent in model.BeeModel.schedule.step()
    def step(self):
        self.handle_nectar()
        self.update_world_knowledge(verbose=True)

        if self.nectar_amount > 0:
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


class Flowerfield(StaticObject):
    def __init__(self, unique_id, pos, model):
        super().__init__(unique_id, pos, model)
        self.type = "flowerfield"


class Nectar(StaticObject):
    def __init__(self, unique_id, pos, model, amount):
        super().__init__(unique_id, pos, model)
        self.type = "nectar"
        self.amount = amount


class Hive(StaticObject):
    def __init__(self, unique_id, pos, model):
        super().__init__(unique_id, pos, model)
        self.type = "hive"

    # step is called for each agent in model.BeeModel.schedule.step()
