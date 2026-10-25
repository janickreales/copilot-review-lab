# Databricks notebook source
# MAGIC %md
# MAGIC # 03 · Silver: pedidos y líneas de pedido
# MAGIC
# MAGIC **Propósito:** limpiar, tipar y deduplicar pedidos y líneas de pedido desde bronze.
# MAGIC
# MAGIC **Entradas:** `bronze_orders`, `bronze_lineitem`
# MAGIC
# MAGIC **Salidas:**
# MAGIC - `silver_orders`: overwrite completo, una fila por `o_orderkey`.
# MAGIC - `silver_lineitem`: upsert incremental con `src/sql/merge_silver_orders.sql`, una fila por `(l_orderkey, l_linenumber)`.

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

import json
import os

from pyspark.sql import functions as F

from src.utils.spark_helpers import dedupe_latest, run_sql_file, write_delta

# COMMAND ----------

# MAGIC %md
# MAGIC ## silver_orders

# COMMAND ----------

orders = (
    spark.table(cfg.table("bronze_orders"))
    .select(
        F.col("o_orderkey").cast("bigint"),
        F.col("o_custkey").cast("bigint"),
        F.col("o_orderdate").cast("date"),
        F.year("o_orderdate").alias("order_year"),
        F.col("o_totalprice").cast("decimal(18,2)"),
        F.trim("o_orderstatus").alias("o_orderstatus"),
        "_ingested_at",
    )
)
silver_orders = dedupe_latest(orders, keys=["o_orderkey"], order_col="_ingested_at")
write_delta(silver_orders, cfg.table("silver_orders"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## silver_lineitem (upsert)
# MAGIC El ingreso neto se calcula con expresiones nativas de Spark: `l_extendedprice * (1 - l_discount)`.

# COMMAND ----------

lineitem = (
    spark.table(cfg.table("bronze_lineitem"))
    .select(
        F.col("l_orderkey").cast("bigint"),
        F.col("l_linenumber").cast("int"),
        F.col("l_partkey").cast("bigint"),
        F.col("l_suppkey").cast("bigint"),
        F.col("l_quantity").cast("decimal(18,2)"),
        F.col("l_extendedprice").cast("decimal(18,2)"),
        F.col("l_discount").cast("decimal(18,2)"),
        F.col("l_shipdate").cast("date"),
        "_ingested_at",
    )
    .withColumn(
        "net_revenue",
        (F.col("l_extendedprice") * (F.lit(1) - F.col("l_discount"))).cast("decimal(38,4)"),
    )
)
updates = dedupe_latest(lineitem, keys=["l_orderkey", "l_linenumber"], order_col="_ingested_at")
updates.createOrReplaceTempView("silver_lineitem_updates")

run_sql_file(
    spark,
    os.path.join(SQL_DIR, "merge_silver_orders.sql"),
    {"target_table": cfg.table("silver_lineitem")},
)

# COMMAND ----------

log.info("Silver layer updated for run %s", RUN_ID)
dbutils.notebook.exit(json.dumps({"silver_orders": cfg.table("silver_orders"), "silver_lineitem": cfg.table("silver_lineitem")}))
