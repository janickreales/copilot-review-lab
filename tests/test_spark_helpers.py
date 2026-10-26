import pytest

pytest.importorskip("pyspark")

from chispa import assert_df_equality  # noqa: E402

from src.utils.spark_helpers import (  # noqa: E402
    dedupe_latest,
    safe_broadcast_join,
    split_sql_statements,
)


def _plan(df) -> str:
    return df._jdf.queryExecution().executedPlan().toString()


def test_dedupe_latest_keeps_most_recent_row_per_key(spark):
    df = spark.createDataFrame(
        [(1, 1, "old", 1), (1, 1, "new", 2), (2, 1, "only", 1)],
        "k1 int, k2 int, value string, ts int",
    )

    result = dedupe_latest(df, keys=["k1", "k2"], order_col="ts")

    expected = spark.createDataFrame([(1, 1, "new", 2), (2, 1, "only", 1)], "k1 int, k2 int, value string, ts int")
    assert_df_equality(result, expected, ignore_row_order=True)


def test_dedupe_latest_requires_keys(spark):
    df = spark.createDataFrame([(1,)], "k int")
    with pytest.raises(ValueError):
        dedupe_latest(df, keys=[], order_col="k")


def test_safe_broadcast_join_broadcasts_small_side(spark):
    large = spark.createDataFrame([(i, i * 10) for i in range(100)], "k int, v int")
    small = spark.createDataFrame([(1, "a"), (2, "b")], "k int, label string")

    result = safe_broadcast_join(large, small, on=["k"], max_small_rows=10)

    assert result.count() == 2
    assert "BroadcastHashJoin" in _plan(result)


def test_safe_broadcast_join_skips_broadcast_above_threshold(spark):
    large = spark.createDataFrame([(i, i * 10) for i in range(100)], "k int, v int")
    small = spark.createDataFrame([(i, str(i)) for i in range(50)], "k int, label string")

    result = safe_broadcast_join(large, small, on=["k"], max_small_rows=10)

    assert result.count() == 50
    assert "BroadcastHashJoin" not in _plan(result)


def test_split_sql_statements_ignores_comments_and_blank_statements():
    script = """
    -- comentario; con punto y coma
    CREATE TABLE a (x INT);

    INSERT INTO a VALUES (1); -- final
    ;
    """

    assert split_sql_statements(script) == [
        "CREATE TABLE a (x INT)",
        "INSERT INTO a VALUES (1)",
    ]
