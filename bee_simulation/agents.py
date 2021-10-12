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

        # Private variables
        self.type = "bee"
        self.nectar_collected = []
        self.energy = self.max_energy

        # Agent Clue information
        self.clue_loc = (random.randint(0, self.model.height), random.randint(0, self.model.width))
        self.clue_grade = 1000
        self.init_clue = True
        self.alive = True

        # State
        self.state = "return_to_hive"
        # Options are:
        # - return_to_hive
        # - explore

        # Init grid memory
        self.hive_pos = None
        self.grid_memory = self.init_grid_memory(self)

        # Explore state
        self.explore_clue = None

        # Grid values
        self.grid_values = helpers.generate_grid_costs(self, self.hive_pos)

    def init_grid_memory(self, agent):  # ----------------------------------------- Hoort dit in bij?
        """Initiating grid memory (and put in hive locations)."""
        grid_memory = np.zeros([self.model.grid_w, self.model.grid_h], dtype=np.str)
        for hive in [a for a in self.model.schedule.agents if a.type == "hive"]:
            grid_memory[hive.pos] = "x"
            agent.hive_pos = hive.pos
        return grid_memory

    def step(self):
        """Figure out what the bee will do in this current time step."""
        if self.alive:
            # Update grid perception
            logic.update_memory(self, perception.percept(self))

            # What action should the bee take?
            self.state = logic.update_state(self)
            # print(f"Current State: {self.state} ID: {self.unique_id}")

            if self.state == "return_to_hive":
                actions.return_to_hive(self)

            # When a bee doesn't yet want to go back to the hive, it will explore
            elif self.state == "explore":
                # We calculate the grid scores, this will indicate where a bee will want to move to
                grid_scores = logic.calc_grid_scores(self)

                np.set_printoptions(precision=1, suppress=True)
                # print(np.rot90(grid_scores))

                # Bee moves to tile with highest score
                move_choice = np.unravel_index(np.argmax(grid_scores), grid_scores.shape)
                actions.move_to_target(self, move_choice)

                nectar_onsite = [a for a in self.model.grid[self.pos] if a.type == "nectar"]

                # If there is nectar in the bee his grid memory.
                if nectar_onsite:

                    # And the bee stands on this nectar
                    nectar_pos = nectar_onsite[0].pos
                    if logic.touch(nectar_pos, self.pos) and logic.touch(nectar_pos, move_choice):

                        # If the flowerfield doesn't stand too close to the hive, the bee will collect the nectar
                        if grid_scores[nectar_pos] > 0 or self.model.collect_negative_value_nectar:
                            actions.collect_nectar(self, nectar_onsite[0])

                        # If however, the flowerfield is not even worth the energy to collect it, the bee will ignore it
                        else:
                            self.grid_memory[nectar_pos] = '/'

            else:
                exit(f"Invalid State: {self.state}")

            # If the bee stands on the hive, it will deposit its nectar
            # ∀a ∃k ∃f((Bee(a) ˄ Beehive(k) ˄ FlowerField(f) ˄ Touch(a, k)) -> (GainHoney(k) ˄ LoseNectar(a)))
            if logic.touch(self.pos, self.hive_pos):
                actions.dropoff_nectar(self)
                actions.refill_energy(self)

            # Bee loses an energie after taking its action
            # ∀a ∀b((Bee(a) ˄ TimeStep(b)) -> MinusOne(Energy(a)))
            self.energy -= 1

            # When
            # ∀a ((Bee(a) ˄ IsZero(Energy(a))) -> Die(a))
            if self.energy <= 0:
                self.alive = False


class FlowerField(StaticObject):
    def __init__(self, unique_id, pos, model, max_nectar_grade, respawn_interval):
        super().__init__(unique_id, pos, model)
        self.type = "flowerfield"
        # self.grade = random.randrange(1, max_nectar_grade + 1)
        self.grade = max_nectar_grade
        self.respawn_interval = respawn_interval
        self.steps_left_for_respawn = self.respawn_interval

    def step(self) -> None:
        """What this flowerfield will do this time step."""
        # All flowerfield gain a nectar after a certain amount of time
        # ∀a((Flowerfield(a) ˄ IsZero(NectarRegrowCountdown(a) -> GainNectar(a))
        self.steps_left_for_respawn -= 1
        if self.steps_left_for_respawn <= 0:
            self.steps_left_for_respawn = self.respawn_interval

            # List of all the nectar that this flowerfield contains
            nectar_on_loc = [agent for agent in self.model.schedule.agents if
                             agent.type == "nectar" and logic.touch(agent.pos, self.pos)]

            # If this flowerfield contains nectar, the nectar agent will gain a nectar
            if nectar_on_loc:
                nectar_on_loc[0].amount += 1

            # Otherwise we make a new nectar agent and give him a new nectar
            else:
                nectar = Nectar(self.model.instance_last_id, self.pos, self, 1, self.grade)
                self.model.grid.place_agent(nectar, self.pos)
                self.model.schedule.add(nectar)
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
