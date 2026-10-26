"""Validaciones de calidad de datos sobre DataFrames de Spark.

Cada check devuelve `CheckResult` (una lista, uno por columna, en el caso de
`check_not_null`) para que el notebook decida qué hacer con los fallos:
registrar, alertar o abortar.
"""

from collections.abc import Sequence
from dataclasses import asdict, dataclass

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


@dataclass(frozen=True)
class CheckResult:
    table_name: str
    check_name: str
    column_name: str
    failed_rows: int
    total_rows: int
    threshold: float
    passed: bool

    @property
    def failed_ratio(self) -> float:
        return self.failed_rows / self.total_rows if self.total_rows else 0.0

    def as_row(self) -> dict:
        row = asdict(self)
        row["failed_ratio"] = self.failed_ratio
        return row


def _result(table, check, column, failed, total, threshold) -> CheckResult:
    ratio = failed / total if total else 0.0
    return CheckResult(table, check, column, failed, total, threshold, ratio <= threshold)


def check_not_null(
    df: DataFrame, table: str, columns: Sequence[str], max_null_ratio: float, total: int
) -> list[CheckResult]:
    """Cuenta nulos por columna en una sola pasada sobre `df`.

    Un check pasa si la proporción de nulos es menor o igual a `max_null_ratio`.
    `total` es el conteo de filas de `df`, calculado una vez por el llamador.
    """
    counts = df.select([F.sum(F.col(c).isNull().cast("long")).alias(c) for c in columns]).first()
    return [_result(table, "not_null", c, int(counts[c] or 0), total, max_null_ratio) for c in columns]


def check_unique(df: DataFrame, table: str, keys: Sequence[str], max_duplicate_ratio: float, total: int) -> CheckResult:
    """Verifica que `keys` identifique filas de forma única.

    Las filas fallidas son las que sobran: total menos combinaciones distintas.
    """
    duplicated_keys = df.groupBy(*keys).count().filter(F.col("count") > 1).count()
    return _result(table, "unique", ",".join(keys), duplicated_keys, total, max_duplicate_ratio)


def check_range(
    df: DataFrame,
    table: str,
    column: str,
    min_value: float,
    max_value: float,
    total: int,
    max_out_of_range_ratio: float = 0.0,
) -> CheckResult:
    """Cuenta filas con `column` fuera del rango cerrado [min_value, max_value].

    Los nulos no cuentan como fuera de rango; los cubre `check_not_null`.
    """
    failed = df.filter(F.col(column).isNotNull() & ~F.col(column).between(min_value, max_value)).count()
    return _result(table, "range", column, failed, total, max_out_of_range_ratio)
