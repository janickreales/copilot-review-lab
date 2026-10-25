import pytest


@pytest.fixture(scope="session")
def spark():
    """SparkSession local para tests unitarios (no requiere Databricks)."""
    pyspark_sql = pytest.importorskip("pyspark.sql")
    session = (
        pyspark_sql.SparkSession.builder.master("local[1]")
        .appName("retail-margin-tests")
        .config("spark.sql.shuffle.partitions", "1")
        .config("spark.sql.autoBroadcastJoinThreshold", "-1")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    yield session
    session.stop()
