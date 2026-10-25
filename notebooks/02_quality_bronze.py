# Databricks notebook source
# MAGIC %md
# MAGIC # 02 · Calidad de datos sobre bronze
# MAGIC
# MAGIC **Propósito:** validar nulos, unicidad de claves y rangos en las tablas bronze antes de construir silver.
# MAGIC
# MAGIC **Entradas:** `bronze_orders`, `bronze_lineitem`, `bronze_partsupp`, `bronze_supplier`
# MAGIC
# MAGIC **Salidas:** filas en `dq_results` (append, una por check) y vista temporal `v_dq_results`
# MAGIC
# MAGIC **Falla el task** si algún check no pasa, para que el job no avance con datos inválidos.

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

# MAGIC %md
# MAGIC ## Checks por tabla
# MAGIC Cada tabla se cuenta una sola vez y el total se reutiliza en todos sus checks.

# COMMAND ----------

import json

from pyspark.sql import functions as F

from src.utils.quality import check_not_null, check_range, check_unique

q = cfg.quality
results = []

orders = spark.table(cfg.table("bronze_orders"))
orders_total = orders.count()
results += check_not_null(
    orders, "bronze_orders", ["o_orderkey", "o_custkey", "o_orderdate"], q.max_null_ratio, orders_total
)
results.append(check_unique(orders, "bronze_orders", ["o_orderkey"], q.max_duplicate_ratio, orders_total))

lineitem = spark.table(cfg.table("bronze_lineitem"))
lineitem_total = lineitem.count()
results += check_not_null(
    lineitem,
    "bronze_lineitem",
    ["l_orderkey", "l_linenumber", "l_partkey", "l_suppkey"],
    q.max_null_ratio,
    lineitem_total,
)
results.append(
    check_unique(lineitem, "bronze_lineitem", ["l_orderkey", "l_linenumber"], q.max_duplicate_ratio, lineitem_total)
)
results.append(
    check_range(lineitem, "bronze_lineitem", "l_discount", q.min_discount, q.max_discount, lineitem_total)
)

partsupp = spark.table(cfg.table("bronze_partsupp"))
results.append(
    check_unique(partsupp, "bronze_partsupp", ["ps_partkey", "ps_suppkey"], q.max_duplicate_ratio, partsupp.count())
)

supplier = spark.table(cfg.table("bronze_supplier"))
results.append(check_unique(supplier, "bronze_supplier", ["s_suppkey"], q.max_duplicate_ratio, supplier.count()))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Registro de resultados

# COMMAND ----------

results_df = (
    spark.createDataFrame([r.as_row() for r in results])
    .withColumn("run_id", F.lit(RUN_ID))
    .withColumn("checked_at", F.current_timestamp())
    .select(
        "run_id",
        "table_name",
        "check_name",
        "column_name",
        F.col("failed_rows").cast("bigint"),
        F.col("total_rows").cast("bigint"),
        F.col("threshold").cast("double"),
        "passed",
        F.col("failed_ratio").cast("double"),
        "checked_at",
    )
)
results_df.write.mode("append").saveAsTable(cfg.table("dq_results"))
results_df.createOrReplaceTempView("v_dq_results")

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     table_name,
# MAGIC     check_name,
# MAGIC     column_name,
# MAGIC     failed_rows,
# MAGIC     total_rows,
# MAGIC     passed
# MAGIC FROM v_dq_results
# MAGIC ORDER BY passed, table_name, check_name

# COMMAND ----------

failed = [r for r in results if not r.passed]
if failed:
    details = "; ".join(f"{r.table_name}.{r.column_name} ({r.check_name}): {r.failed_rows} rows" for r in failed)
    raise ValueError(f"{len(failed)} data quality check(s) failed: {details}")

log.info("All %s data quality checks passed", len(results))
dbutils.notebook.exit(json.dumps({"checks": len(results), "failed": 0}))
