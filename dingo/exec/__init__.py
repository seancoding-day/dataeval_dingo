from dingo.utils import log

from dingo.exec.local import LocalExecutor  # noqa E402.
try:
    from dingo.exec.spark import SparkExecutor  # noqa E402.
except Exception as e:
    log.warning("Spark Executor not imported. Open debug log for more details.")
    log.debug(str(e))

from dingo.exec.base import Executor, ExecProto  # noqa E402.
