from dingo.data.dataset.base import Dataset
from dingo.utils import log

try:
    pass
except Exception as e:
    log.warning("Spark Dataset not imported. Open debug log for more details.")
    log.debug(str(e))

dataset_map = Dataset.dataset_map
