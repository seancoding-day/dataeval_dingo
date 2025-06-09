from dingo.data.datasource.base import DataSource
from dingo.utils import log

try:
    pass
except Exception as e:
    log.warning("S3 datasource not imported. Open debug log for more details.")
    log.debug(str(e))

datasource_map = DataSource.datasource_map
