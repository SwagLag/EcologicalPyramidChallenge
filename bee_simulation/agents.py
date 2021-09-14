from bee_simulation.random_walk import RandomWalker
from bee_simulation.static_object import StaticObject


# subclass of RandomWalker, which is subclass to Mesa Agent
class Bee(RandomWalker):
    def __init__(self, unique_id, pos, model, moore):
        # init parent class with required parameters
        super().__init__(unique_id, pos, model, moore=moore)

        self.type = "bee"
        self.has_nectar = False

    # step is called for each agent in model.BeeModel.schedule.step()
    def step(self):
        # move to a cell in my Moore neighborhood
        self.random_move()

        bees = [a for a in self.model.schedule.agents if a.type == "bee" and a != self]
        nectars = [a for a in self.model.schedule.agents if a.type == "nectar"]
        hives = [a for a in self.model.schedule.agents if a.type == "hive"]
        # Dropping of Nectar
        for hive in hives:
            if self.pos == hive.pos and self.has_nectar == True:
                self.has_nectar = False
                self.model.nectar_collected += 1

        # Collection of Nectar
        for nectar in nectars:
            if self.pos == nectar.pos:
                if self.has_nectar == False:
                    self.model.grid.remove_agent(nectar)
                    self.has_nectar = True


class Nectar(StaticObject):
    def __init__(self, unique_id, pos, model):
        # init parent class with required parameters
        super().__init__(unique_id, pos, model)

        self.type = "nectar"

    # step is called for each agent in model.BankReservesModel.schedule.step()


class Hive(StaticObject):
    def __init__(self, unique_id, pos, model):
        # init parent class with required parameters
        super().__init__(unique_id, pos, model)

        self.type = "hive"

    # step is called for each agent in model.BankReservesModel.schedule.step()
