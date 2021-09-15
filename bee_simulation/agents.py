from bee_simulation.movement import MovingEntity
from bee_simulation.static_object import StaticObject

import numpy as np


# subclass of RandomWalker, which is subclass to Mesa Agent

def calc_distance(start_pos, target_pos):
    return abs(start_pos[0] - target_pos[0]) + abs(start_pos[1] - target_pos[1])

class Bee(MovingEntity):
    def __init__(self, unique_id, pos, model, flowers, moore):
        # init parent class with required parameters
        super().__init__(unique_id, pos, model, moore=moore)

        # Private vars
        self.type = "bee"
        self.nectar_amount = 0  # Can only carry 1 for now, but potentially useful for later when we want to increase cap.
        self.nectar_grade = 0  # Determines scoring value, inferred from picked up nectar.
        self.flowerfields = flowers

        # Agent parameters
        self.perception_range = 1
        self.state = 0  # Whether to plan or act.
        self.target = (0, 0)

        # Initiating grid memory for logic inferencing (and put in hive locations)
        self.grid_memory = np.zeros([self.model.grid_w, self.model.grid_h], dtype=np.str)
        self.nectar_memory = dict()
        self.field_memory = dict()
        for hive in [a for a in self.model.schedule.agents if a.type == "hive"]:
            self.grid_memory[hive.pos] = "x"

    def handle_nectar(self):
        nectars = [a for a in self.model.grid[self.pos] if a.type == "nectar"]
        hives = [a for a in self.model.grid[self.pos] if a.type == "hive"]
        # Dropping of Nectar
        for hive in hives:
            if self.pos == hive.pos and self.nectar_amount > 0:
                self.model.nectar_collected += self.nectar_amount * self.nectar_grade
                self.nectar_amount = 0
                self.nectar_grade = 0  # Safety precaution.

        # Collection of Nectar
        for nectar in nectars:
            if self.pos == nectar.pos:
                if self.nectar_amount <= 0:  # Collect Nectar if not loaded (Support for carrying more nectar at once later)
                    if nectar.amount <= 1:
                        self.nectar_amount += 1
                        self.model.grid.remove_agent(nectar)
                        self.nectar_memory.pop(self.pos)
                        self.grid_memory[self.pos] = 'f'
                    else:
                        self.nectar_amount += 1
                        nectar.amount -= 1
                    self.nectar_grade = nectar.grade

    def update_world_knowledge(self, verbose=False):
        perception = self.model.grid.get_neighborhood(self.pos, self.moore, include_center=True,
                                                      radius=self.perception_range)
        for tile in perception:
            tilecontents = self.model.grid[tile]
            entities = self._find_classes(self.model.grid[tile])
            if "Nectar" in entities:
                self.grid_memory[tile] = "n"
                self.nectar_memory[self.model.grid[tile][entities.index("Flowerfield")].pos] = self.model.grid[tile][entities.index("Flowerfield")].grade
                self.field_memory[self.model.grid[tile][entities.index("Flowerfield")].pos] = self.model.grid[tile][entities.index("Flowerfield")].grade
            elif "Flowerfield" in entities:
                self.grid_memory[tile] = "f"
                self.field_memory[self.model.grid[tile][entities.index("Flowerfield")].pos] = self.model.grid[tile][entities.index("Flowerfield")].grade

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

    def _find_classes(self, iterable):
        return [x.__class__.__name__ for x in iterable]

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
        self.target = self._calc_closest_of_list(hives)
        self.state = 1
        self.move_to_target(self.target)

    # def fetch_closest_nectar(self):
    #     # nectar = [a.pos for a in self.model.schedule.agents if a.type == "nectar" and a.pos != None]
    #     nectar = np.argwhere(self.grid_memory == 'n')
    #     self.move_to_target(self._calc_closest_of_list(nectar))

    def fetch_rational_nectar(self):
        # nectar = [a.pos for a in self.model.schedule.agents if a.type == "nectar" and a.pos != None]
        # nectar = np.argwhere(self.grid_memory == 'n')
        # self.move_to_target(self._calc_closest_of_list(nectar))
        hivepos = list(np.argwhere(self.grid_memory == 'x')[0])
        x = self.nectar_memory.copy()
        score = []
        for key in x.keys():
            score.append(x[key] / (calc_distance(self.pos, key) + calc_distance(key, hivepos)))
        print(list(x.keys()))
        ideal = list(x.keys())[score.index(max(score))]
        self.target = ideal
        self.state = 1
        self.move_to_target(self.target)

    def explore(self):
        unexplored = np.argwhere(self.grid_memory == '')
        self.target = self._calc_closest_of_list(unexplored)
        self.state = 1
        self.move_to_target(self.target)

    # step is called for each agent in model.BeeModel.schedule.step()
    def step(self):
        self.update_world_knowledge(verbose=True)

        if self.pos == tuple(self.target):
            self.state = 0
            self.handle_nectar()

        if self.nectar_amount > 0:
            print("return_to_hive")
            self.return_to_hive()
        else:
            if self.state == 0:
                if len(np.argwhere(self.grid_memory == 'n')) != 0:
                    print("fetch_rational_nectar")
                    self.fetch_rational_nectar()
                elif len(np.argwhere(self.grid_memory == '')) == 0 or len(np.argwhere(self.grid_memory == 'f')) == self.flowerfields:
                    print("return_to_hive")
                    self.return_to_hive()
                else:
                    print("explore")
                    self.explore()
            elif self.state == 1:
                self.move_to_target(self.target)


class Flowerfield(StaticObject):
    def __init__(self, unique_id, pos, model, grade):
        super().__init__(unique_id, pos, model)
        self.type = "flowerfield"
        self.grade = grade

    def spawn_nectar(self):
        amount = np.random.randint(self.model.min_nectar,self.model.max_nectar+1)
        p = Nectar(self.model.instance_last_id, self.pos, self, amount, self.grade)
        self.model.grid.place_agent(p, self.pos)
        self.model.schedule.add(p)
        self.model.instance_last_id += 1


class Nectar(StaticObject):
    def __init__(self, unique_id, pos, model, amount, grade):
        super().__init__(unique_id, pos, model)
        self.type = "nectar"
        self.amount = amount  # Determines the amount of Nectar available and thus the amount of trips a bee can make
        self.grade = grade  # Determines the scoring value of the Nectar for bringint it back to a beehive


class Hive(StaticObject):
    def __init__(self, unique_id, pos, model):
        super().__init__(unique_id, pos, model)
        self.type = "hive"

    # step is called for each agent in model.BeeModel.schedule.step()
