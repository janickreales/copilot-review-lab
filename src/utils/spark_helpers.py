"""Helpers de Spark/Delta reutilizados por los notebooks del pipeline."""

import re
from collections.abc import Mapping, Sequence

from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F

from src.utils.logging_utils import get_logger

_log = get_logger(__name__)


def with_ingestion_metadata(df: DataFrame, source: str) -> DataFrame:
    """Agrega columnas de linaje: momento de ingesta y tabla de origen."""
    return df.withColumn("_ingested_at", F.current_timestamp()).withColumn("_source", F.lit(source))


def dedupe_latest(df: DataFrame, keys: Sequence[str], order_col: str) -> DataFrame:
    """Conserva una fila por combinación de `keys`: la de mayor `order_col`.

    Ante empates en `order_col` se queda con una fila cualquiera del empate;
    si eso importa, incluir una columna de desempate en `keys` o en el orden.
    """
    if not keys:
        raise ValueError("dedupe_latest requires at least one key column")
    window = Window.partitionBy(*keys).orderBy(F.col(order_col).desc())
    return df.withColumn("_rn", F.row_number().over(window)).filter(F.col("_rn") == 1).drop("_rn")


def safe_broadcast_join(
    large: DataFrame,
    small: DataFrame,
    on: Sequence[str],
    how: str = "inner",
    max_rows: int = 200_000,
) -> DataFrame:
    """Une `large` con `small`, forzando broadcast solo si `small` es realmente chico.

    Cuenta las filas de `small` (una acción sobre el lado pequeño) y aplica
    `F.broadcast` si no supera `max_rows`. Si lo supera, deja que Spark/AQE
    elija la estrategia. `large` nunca se broadcastea.
    """
    small_rows = small.count()
    if small_rows <= max_rows:
        _log.info("Broadcasting small side (%s rows <= %s)", small_rows, max_rows)
        return large.join(F.broadcast(small), on=list(on), how=how)
    _log.warning("Small side has %s rows (> %s); skipping forced broadcast", small_rows, max_rows)
    return large.join(small, on=list(on), how=how)


def write_delta(df: DataFrame, table: str, mode: str = "overwrite") -> None:
    """Escribe un DataFrame como tabla Delta administrada (sin particionar)."""
    if mode not in ("overwrite", "append"):
        raise ValueError(f"Unsupported write mode {mode!r}")
    writer = df.write.format("delta").mode(mode)
    if mode == "overwrite":
        writer = writer.option("overwriteSchema", "true")
    writer.saveAsTable(table)


def split_sql_statements(sql_text: str) -> list[str]:
    """Divide un script SQL en sentencias, ignorando comentarios de línea `--`.

    Pensado para los scripts de src/sql: no soporta `;` dentro de literales.
    """
    without_comments = re.sub(r"--[^\n]*", "", sql_text)
    return [stmt.strip() for stmt in without_comments.split(";") if stmt.strip()]


def run_sql_file(spark: SparkSession, path: str, params: Mapping[str, object] | None = None) -> None:
    """Ejecuta cada sentencia de un archivo .sql con parámetros nombrados.

    Los valores se pasan como parameter markers (`:nombre`), nunca por
    interpolación de texto. Cada sentencia recibe solo los parámetros que usa.
    """
    with open(path, encoding="utf-8") as handle:
        statements = split_sql_statements(handle.read())
    params = dict(params or {})
    for statement in statements:
        used = {k: v for k, v in params.items() if re.search(rf":{k}\b", statement)}
        _log.info("Running statement from %s with params %s", path, sorted(used))
        spark.sql(statement, args=used)
