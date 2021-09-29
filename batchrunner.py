from mesa.batchrunner import BatchRunner, BatchRunnerMP
from IntelligentBeesChallenge.bee_simulation.model import BeeSimulation, get_nectar_per_t, get_bee_energy, get_hive_energy, \
    get_nectar_collected
import pandas as pd

# PARAMETERS:
#

fixed_params = {
    "height": 10,
    "width": 10,
    "init_bees": 1,
    "init_flowers": 6,
    "init_min_nectar_grade": 1,
    "init_max_nectar_grade": 30,
    "min_nectar": 1,
    "max_nectar": 1,
    "nectar_respawn_interval": 50,
    "collect_negative_value_nectar": True,
    "perception_range": 1,
}

variable_params = {
    "max_bee_energy": range(30, 50, 10)
}

# variable_params = {
#     "nectar_respawn_interval": range(),
#     "max_bee_energy": range(),
#     "init_flowers": range(),
#     "min_nectar": range(),
#     "max_nectar": range(),
#     "init_min_nectar_grade": range(),
#     "init_max_nectar_grade": range(),
# }

batch_run = BatchRunner(BeeSimulation,
                        variable_parameters=variable_params,
                        fixed_parameters=fixed_params,
                        iterations=3,
                        model_reporters={
                            "Nectar/T": get_nectar_per_t,
                            "Bee energy": get_bee_energy,
                            "Nectar stored": get_hive_energy,
                            "Nectar Collected": get_nectar_collected,
                        })

batch_run.run_all()
test = batch_run.get_model_vars_dataframe()
test2 = batch_run.get_collector_model()
print(test.head())
print(test2)
