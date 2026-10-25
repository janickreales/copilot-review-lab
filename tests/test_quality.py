import pytest

pytest.importorskip("pyspark")

from src.utils.quality import check_not_null, check_range, check_unique  # noqa: E402


@pytest.fixture
def orders(spark):
    return spark.createDataFrame(
        [(1, 0.05), (2, None), (2, 0.20), (3, 0.0)],
        "o_orderkey int, l_discount double",
    )


def test_check_not_null_counts_nulls_per_column(orders):
    [result] = check_not_null(orders, "t", ["l_discount"], max_null_ratio=0.0, total=4)

    assert result.failed_rows == 1
    assert result.failed_ratio == 0.25
    assert not result.passed


def test_check_not_null_passes_within_threshold(orders):
    [result] = check_not_null(orders, "t", ["l_discount"], max_null_ratio=0.25, total=4)

    assert result.passed


def test_check_unique_counts_extra_rows(orders):
    result = check_unique(orders, "t", ["o_orderkey"], max_duplicate_ratio=0.0, total=4)

    assert result.failed_rows == 1
    assert not result.passed


def test_check_range_ignores_nulls_and_flags_out_of_range(orders):
    result = check_range(orders, "t", "l_discount", 0.0, 0.10, total=4)

    assert result.failed_rows == 1
    assert result.column_name == "l_discount"


def test_as_row_includes_failed_ratio(orders):
    result = check_unique(orders, "t", ["o_orderkey"], max_duplicate_ratio=0.0, total=4)

    row = result.as_row()

    assert row["failed_ratio"] == 0.25
    assert row["check_name"] == "unique"
