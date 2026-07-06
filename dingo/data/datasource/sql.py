from typing import Any, Dict, Generator, Optional
from urllib.parse import parse_qsl

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, Engine

from dingo.config import InputArgs
from dingo.data.datasource.base import DataSource


@DataSource.register()
class SqlDataSource(DataSource):
    _ENGINE_ARG_TYPES = {
        "pool_pre_ping": "bool",
        "pool_recycle": "int",
        "pool_size": "int",
        "max_overflow": "int",
        "pool_timeout": "int",
    }

    def __init__(
        self,
        input_args: InputArgs = None,
        config_name: Optional[str] = None,
    ):
        """Create a `SqlDataSource` instance.
        Args:
            input_args: A `InputArgs` instance to load the dataset from.
            config_name: Optional configuration name.
        """
        self.engine = self._get_engine(input_args.dataset.sql_config)
        self.sql_query = input_args.input_path
        self.config_name = config_name
        super().__init__(input_args=input_args)

    @staticmethod
    def _get_engine(sql_config) -> Engine:
        """创建SQLAlchemy引擎"""
        if not sql_config.dialect or not sql_config.database:
            raise RuntimeError(
                "SQL connection parameters (dialect, database) "
                "must be set when using SQL datasource."
            )

        dialect = sql_config.dialect.lower()
        query_args = SqlDataSource._parse_connect_args(sql_config.connect_args)

        connection_url = SqlDataSource._build_connection_url(sql_config, query_args)

        engine_kwargs: Dict[str, Any] = {"pool_pre_ping": True}
        if dialect in {"mysql", "mariadb"}:
            engine_kwargs["pool_recycle"] = 1800
        engine_kwargs.update(SqlDataSource._parse_engine_args(sql_config.engine_args))

        engine = create_engine(connection_url, **engine_kwargs)
        return engine

    @staticmethod
    def _build_driver_name(sql_config) -> str:
        return (
            f"{sql_config.dialect}+{sql_config.driver}"
            if sql_config.driver
            else sql_config.dialect
        )

    @staticmethod
    def _parse_connect_args(connect_args: str) -> Dict[str, str]:
        return SqlDataSource._parse_query_arg_string(connect_args)

    @staticmethod
    def _parse_query_arg_string(raw_arg_string: str) -> Dict[str, str]:
        if not raw_arg_string:
            return {}
        normalized = raw_arg_string.strip()
        if normalized.startswith("?"):
            normalized = normalized[1:]
        if not normalized:
            return {}
        return {
            key: value
            for key, value in parse_qsl(normalized, keep_blank_values=False)
            if key
        }

    @staticmethod
    def _parse_bool_value(raw_value: str, key: str) -> bool:
        normalized = raw_value.strip().lower()
        if normalized == "true":
            return True
        if normalized == "false":
            return False
        raise RuntimeError(
            f"SQL engine arg '{key}' expects 'true' or 'false', got: {raw_value}."
        )

    @staticmethod
    def _parse_engine_args(engine_args: str) -> Dict[str, Any]:
        raw_engine_args = SqlDataSource._parse_query_arg_string(engine_args)
        if not raw_engine_args:
            return {}

        parsed_engine_args: Dict[str, Any] = {}
        for key, raw_value in raw_engine_args.items():
            expected_type = SqlDataSource._ENGINE_ARG_TYPES.get(key)
            if expected_type is None:
                allowed = ", ".join(sorted(SqlDataSource._ENGINE_ARG_TYPES.keys()))
                raise RuntimeError(
                    f"Unsupported SQL engine arg '{key}'. Allowed keys: {allowed}."
                )

            if expected_type == "int":
                try:
                    parsed_engine_args[key] = int(raw_value)
                except ValueError as exc:
                    raise RuntimeError(
                        f"SQL engine arg '{key}' expects an integer value, got: {raw_value}."
                    ) from exc
            elif expected_type == "bool":
                parsed_engine_args[key] = SqlDataSource._parse_bool_value(raw_value, key)

        return parsed_engine_args

    @staticmethod
    def _parse_port(port: str) -> Optional[int]:
        if not port:
            return None
        try:
            return int(port)
        except ValueError as exc:
            raise RuntimeError("SQL connection parameter 'port' must be an integer.") from exc

    @staticmethod
    def _build_connection_url(sql_config, query_args: Dict[str, str]) -> URL:
        driver_name = SqlDataSource._build_driver_name(sql_config)
        query = query_args or None

        if sql_config.dialect.lower() == "sqlite":
            return URL.create(
                drivername=driver_name,
                database=sql_config.database,
                query=query,
            )

        # 对于非 SQLite 数据库，需要用户名、密码和主机
        if not sql_config.username or not sql_config.host:
            raise RuntimeError(
                f"For {sql_config.dialect}, username and host must be set."
            )

        return URL.create(
            drivername=driver_name,
            username=sql_config.username,
            password=sql_config.password or None,
            host=sql_config.host,
            port=SqlDataSource._parse_port(sql_config.port),
            database=sql_config.database,
            query=query,
        )

    @staticmethod
    def get_source_type() -> str:
        return "sql"

    def load(self, **kwargs) -> Generator[Dict[str, Any], None, None]:
        """使用服务器游标方式流式加载SQL查询结果。

        Args:
            kwargs: Additional keyword arguments used for loading the dataset.

        Returns:
            A generator that yields rows as dictionaries.
        """
        return self._load()

    def _load(self) -> Generator[Dict[str, Any], None, None]:
        """使用stream_results方式流式读取数据库"""
        with self.engine.connect() as conn:
            # 使用stream_results=True启用服务器端游标
            result = conn.execution_options(stream_results=True).execute(
                text(self.sql_query)
            )

            # 直接迭代结果，SQLAlchemy自动处理分页
            for row in result:
                # 将Row对象转换为字典
                yield dict(row._mapping)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sql_query": self.sql_query,
            "config_name": self.config_name,
        }

    def __del__(self):
        """清理资源"""
        if hasattr(self, 'engine'):
            self.engine.dispose()
