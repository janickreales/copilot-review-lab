# Databricks notebook source
# MAGIC %md
# MAGIC # 05 · Fact: margen por línea de pedido
# MAGIC
# MAGIC **Propósito:** calcular ingreso, costo y utilidad por línea de pedido para las partes filtradas.
# MAGIC
# MAGIC **Entradas:** `silver_lineitem`, `silver_orders`, `dim_part_supplier`, `dim_supplier`
# MAGIC
# MAGIC **Salida:** `fact_margin` (overwrite, sin particionar; ver DECISIONS.md, decisión 4)
# MAGIC
# MAGIC **Estrategia de joins (DECISIONS.md, decisiones 1-3):**
# MAGIC 1. `silver_lineitem` es el lado grande y nunca se broadcastea.
# MAGIC 2. `dim_part_supplier` ya viene filtrada por parte; se une por la clave compuesta `(l_partkey, l_suppkey)` para tomar el costo del proveedor real de cada línea.
# MAGIC 3. Las dimensiones pequeñas se unen con `safe_broadcast_join`, que solo fuerza broadcast si el lado chico no supera `broadcast_max_rows`.

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

import json

from pyspark.sql import functions as F

from src.utils.spark_helpers import safe_broadcast_join, write_delta

# COMMAND ----------

lineitem = spark.table(cfg.table("silver_lineitem")).select(
    "l_orderkey", "l_linenumber", "l_partkey", "l_suppkey", "l_quantity", "net_revenue"
)

orders = spark.table(cfg.table("silver_orders")).select(
    F.col("o_orderkey").alias("l_orderkey"), "order_year"
)

part_supplier = spark.table(cfg.table("dim_part_supplier")).select(
    F.col("ps_partkey").alias("l_partkey"),
    F.col("ps_suppkey").alias("l_suppkey"),
    "ps_supplycost",
)

supplier = spark.table(cfg.table("dim_supplier")).select(
    F.col("s_suppkey").alias("l_suppkey"), "s_name", "nation", "region"
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Joins
# MAGIC Primero el join que más reduce filas (partes filtradas), luego pedidos y al final proveedor.

# COMMAND ----------

lines_with_cost = safe_broadcast_join(
    lineitem,
    part_supplier,
    on=["l_partkey", "l_suppkey"],
    max_rows=cfg.broadcast_max_rows,
)

lines_with_year = lines_with_cost.join(orders, on="l_orderkey", how="inner")

fact = (
    safe_broadcast_join(
        lines_with_year,
        supplier,
        on=["l_suppkey"],
        max_rows=cfg.broadcast_max_rows,
    )
    .withColumn("revenue", F.col("net_revenue"))
    .withColumn("cost", (F.col("ps_supplycost") * F.col("l_quantity")).cast("decimal(38,4)"))
    .withColumn("profit", (F.col("revenue") - F.col("cost")).cast("decimal(38,4)"))
    .select(
        "l_orderkey",
        "l_linenumber",
        "l_partkey",
        "l_suppkey",
        "s_name",
        "nation",
        "region",
        "order_year",
        "revenue",
        "cost",
        "profit",
    )
)

write_delta(fact, cfg.table("fact_margin"))

# COMMAND ----------

fact_rows = spark.table(cfg.table("fact_margin")).count()
dbutils.jobs.taskValues.set(key="fact_rows", value=fact_rows)
log.info("fact_margin written with %s rows", fact_rows)
dbutils.notebook.exit(json.dumps({"fact_rows": fact_rows}))
