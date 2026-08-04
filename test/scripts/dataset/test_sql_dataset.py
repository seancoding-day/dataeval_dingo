"""
SQL Dataset 测试文件

使用 SQLite 数据库进行简单测试（无需额外安装驱动）
"""

import os
import sqlite3
import tempfile
import uuid

import pytest

from dingo.config import DatasetArgs, DatasetSqlArgs, InputArgs
from dingo.data.dataset.sql import SqlDataset
from dingo.data.datasource.sql import SqlDataSource


def create_test_database():
    """创建一个测试 SQLite 数据库"""
    # 创建临时数据库文件
    db_path = os.path.join(tempfile.gettempdir(), f"test_dingo_sql_{uuid.uuid4().hex}.db")

    # 连接数据库并创建测试表
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 创建测试表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_data (
            id INTEGER PRIMARY KEY,
            prompt TEXT,
            content TEXT,
            context TEXT,
            image TEXT
        )
    """)

    # 插入测试数据
    test_data = [
        (1, "测试提示1", "这是第一条测试内容", "上下文1", "image1.jpg"),
        (2, "测试提示2", "这是第二条测试内容", "上下文2", "image2.jpg"),
        (3, "测试提示3", "这是第三条测试内容", "上下文3", "image3.jpg"),
        (4, "测试提示4", "这是第四条测试内容", "上下文4", "image4.jpg"),
        (5, "测试提示5", "这是第五条测试内容", "上下文5", "image5.jpg"),
    ]

    cursor.executemany(
        "INSERT OR REPLACE INTO test_data VALUES (?, ?, ?, ?, ?)",
        test_data
    )

    conn.commit()
    conn.close()

    return db_path


def test_sql_dataset():
    """测试 SqlDataset 功能"""
    print("=" * 60)
    print("测试 SqlDataset")
    print("=" * 60)

    # 创建测试数据库
    db_path = create_test_database()
    print(f"✓ 创建测试数据库: {db_path}")

    datasource = None
    try:
        # 配置 SQL 连接参数（SQLite）
        sql_config = DatasetSqlArgs(
            dialect="sqlite",
            driver="",
            username="",
            password="",
            host="",
            port="",
            database=db_path
        )

        # 配置数据集参数
        dataset_config = DatasetArgs(
            source="sql",
            format="jsonl",  # SQL 每行数据类似 JSONL，使用 jsonl 格式
            sql_config=sql_config
        )

        # SQL 查询
        sql_query = "SELECT * FROM test_data"

        # 创建 InputArgs
        input_args = InputArgs(
            task_name="sql_test",
            input_path=sql_query,
            output_path="outputs/sql_test/",
            dataset=dataset_config,
            evaluator=[]
        )

        print("✓ 配置参数创建成功")

        # 创建数据源
        datasource = SqlDataSource(input_args=input_args)
        print("✓ SqlDataSource 创建成功")

        # 创建数据集
        dataset = SqlDataset(source=datasource, name="test_sql_dataset")
        print("✓ SqlDataset 创建成功")

        # 测试流式读取
        print("\n开始流式读取数据:")
        count = 0
        for idx, data in enumerate(dataset.get_data()):
            count += 1
            print(f"  [{idx + 1}] 读取到数据: {data}")

        print(f"\n✓ 成功读取 {count} 条数据")

        # 验证数据源类型
        assert datasource.get_source_type() == "sql", "数据源类型不正确"
        print("✓ 数据源类型验证通过")

        # 验证数据集类型
        assert dataset.get_dataset_type() == "sql", "数据集类型不正确"
        print("✓ 数据集类型验证通过")

        # 验证 to_dict 方法
        dataset_dict = dataset.to_dict()
        assert "name" in dataset_dict, "数据集字典缺少 name 字段"
        assert "digest" in dataset_dict, "数据集字典缺少 digest 字段"
        print("✓ to_dict 方法验证通过")

        print("\n" + "=" * 60)
        print("✓ 所有测试通过!")
        print("=" * 60)

    finally:
        if datasource is not None:
            datasource.engine.dispose()
        # 清理测试数据库
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
                print(f"\n✓ 清理测试数据库: {db_path}")
            except PermissionError:
                print(f"\n! 跳过清理（文件占用）: {db_path}")


def test_stream_results():
    """测试流式结果是否正确工作（不会一次性加载所有数据到内存）"""
    print("\n" + "=" * 60)
    print("测试流式读取特性")
    print("=" * 60)

    # 创建一个包含更多数据的测试数据库
    db_path = os.path.join(
        tempfile.gettempdir(),
        f"test_dingo_sql_stream_{uuid.uuid4().hex}.db"
    )
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS large_table (
            id INTEGER PRIMARY KEY,
            data TEXT
        )
    """)

    # 插入 1000 条数据
    large_data = [(i, f"数据_{i}") for i in range(1, 1001)]
    cursor.executemany("INSERT INTO large_table VALUES (?, ?)", large_data)
    conn.commit()
    conn.close()

    print(f"✓ 创建包含 1000 条数据的测试数据库")

    datasource = None
    try:
        sql_config = DatasetSqlArgs(
            dialect="sqlite",
            driver="",
            username="",
            password="",
            host="",
            port="",
            database=db_path
        )

        dataset_config = DatasetArgs(
            source="sql",
            format="jsonl",  # SQL 每行数据类似 JSONL，使用 jsonl 格式
            sql_config=sql_config
        )

        input_args = InputArgs(
            task_name="stream_test",
            input_path="SELECT * FROM large_table",
            output_path="outputs/stream_test/",
            dataset=dataset_config,
            evaluator=[]
        )

        datasource = SqlDataSource(input_args=input_args)
        dataset = SqlDataset(source=datasource, name="stream_test_dataset")

        # 只读取前 10 条，验证流式读取（不会加载全部 1000 条到内存）
        print("开始流式读取（只读取前 10 条）:")
        count = 0
        data_iterator = iter(dataset.get_data())
        try:
            for idx, data in enumerate(data_iterator):
                if idx < 10:
                    print(f"  [{idx + 1}] {data}")
                count += 1
                if idx >= 9:  # 只读取前 10 条就停止
                    break
        finally:
            close_method = getattr(data_iterator, "close", None)
            if callable(close_method):
                close_method()

        print(f"\n✓ 流式读取验证通过（处理了 {count} 条数据后停止）")

    finally:
        if datasource is not None:
            datasource.engine.dispose()
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
                print(f"✓ 清理测试数据库: {db_path}")
            except PermissionError:
                print(f"! 跳过清理（文件占用）: {db_path}")


def test_parse_connect_args_supports_prefix_and_multiple_pairs():
    query_args = SqlDataSource._parse_connect_args(
        "?charset=utf8mb4&read_timeout=120&write_timeout=120"
    )
    assert query_args["charset"] == "utf8mb4"
    assert query_args["read_timeout"] == "120"
    assert query_args["write_timeout"] == "120"


def test_mysql_engine_has_stability_pool_settings():
    sql_config = DatasetSqlArgs(
        dialect="mysql",
        driver="pymysql",
        username="user",
        password="pass",
        host="localhost",
        port="3306",
        database="db",
        connect_args="charset=utf8mb4"
    )
    engine = SqlDataSource._get_engine(sql_config)
    try:
        assert engine.pool._pre_ping is True
        assert engine.pool._recycle == 1800
    finally:
        engine.dispose()


def test_mysql_does_not_inject_default_timeout_query_args():
    sql_config = DatasetSqlArgs(
        dialect="mysql",
        driver="pymysql",
        username="user",
        password="pass",
        host="localhost",
        port="3306",
        database="db",
        connect_args="charset=utf8mb4"
    )
    query_args = SqlDataSource._parse_connect_args(sql_config.connect_args)
    url = SqlDataSource._build_connection_url(sql_config, query_args)
    assert url.query == {"charset": "utf8mb4"}


def test_parse_engine_args_with_supported_types():
    engine_args = SqlDataSource._parse_engine_args(
        "pool_recycle=3600&pool_pre_ping=true&pool_size=8&max_overflow=16&pool_timeout=30"
    )
    assert engine_args == {
        "pool_recycle": 3600,
        "pool_pre_ping": True,
        "pool_size": 8,
        "max_overflow": 16,
        "pool_timeout": 30,
    }


def test_engine_args_override_default_pool_recycle():
    sql_config = DatasetSqlArgs(
        dialect="mysql",
        driver="pymysql",
        username="user",
        password="pass",
        host="localhost",
        port="3306",
        database="db",
        engine_args="pool_recycle=7200&pool_pre_ping=false"
    )
    engine = SqlDataSource._get_engine(sql_config)
    try:
        assert engine.pool._recycle == 7200
        assert engine.pool._pre_ping is False
    finally:
        engine.dispose()


def test_engine_args_rejects_unsupported_key():
    with pytest.raises(RuntimeError, match="Unsupported SQL engine arg"):
        SqlDataSource._parse_engine_args("unsupported_key=1")


def test_engine_args_rejects_invalid_bool_value():
    with pytest.raises(RuntimeError, match="true' or 'false"):
        SqlDataSource._parse_engine_args("pool_pre_ping=not_bool")


def test_engine_args_rejects_numeric_bool_value():
    with pytest.raises(RuntimeError, match="true' or 'false"):
        SqlDataSource._parse_engine_args("pool_pre_ping=1")


def test_invalid_port_raises_runtime_error():
    sql_config = DatasetSqlArgs(
        dialect="mysql",
        driver="pymysql",
        username="user",
        password="pass",
        host="localhost",
        port="not_a_number",
        database="db"
    )
    with pytest.raises(RuntimeError, match="port"):
        SqlDataSource._build_connection_url(sql_config, {})


if __name__ == "__main__":
    # 运行基本测试
    test_sql_dataset()

    # 运行流式读取测试
    test_stream_results()
