from helpers import load_config, feasibility_total, build_paper_list_for_digest
from schemas import Paper, GateResult

# load_config
config = load_config()
print(config["agent"]["max_searches"])   # should print 4

# feasibility_total
# (use one of your earlier GateResult test objects)