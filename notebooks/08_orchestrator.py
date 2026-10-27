# Databricks notebook source
# MAGIC %md
# MAGIC # 08 · Orquestador por notebook
# MAGIC
# MAGIC **Propósito:** ejecutar el pipeline completo desde un solo notebook con `dbutils.notebook.run`, como alternativa al DAG de `margin_pipeline`.
# MAGIC
# MAGIC **Contrato con cada notebook:**
# MAGIC - Recibe los parámetros `env`, `catalog`, `schema` y `run_id` (los mismos widgets que define `00_config`), más `part_name_filter`.
# MAGIC - Devuelve un JSON con `dbutils.notebook.exit`, o nada en el caso del notebook SQL.
# MAGIC
# MAGIC Si un paso falla, `dbutils.notebook.run` lanza la excepción y el orquestador se detiene en ese paso.

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

import json

dbutils.widgets.text("part_name_filter", cfg.part_name_filter, "Filtro de parte")

STEPS = [
    ("./01_ingest_bronze", 3600),
    ("./02_quality_bronze", 1800),
    ("./03_silver_orders", 3600),
    ("./04_dim_supplier_part", 1800),
    ("./05_fact_margin", 3600),
    ("./06_gold_aggregates", 1800),
    ("./07_export_report", 1800),
]

step_params = {
    "env": cfg.env,
    "catalog": cfg.catalog,
    "schema": cfg.schema,
    "run_id": RUN_ID,
    "part_name_filter": dbutils.widgets.get("part_name_filter"),
}

# COMMAND ----------

summary = {}
for path, timeout_seconds in STEPS:
    log.info("Running %s", path)
    raw = dbutils.notebook.run(path, timeout_seconds, step_params)
    summary[path] = json.loads(raw) if raw else {}
    log.info("Finished %s -> %s", path, summary[path])

# COMMAND ----------

dbutils.notebook.exit(json.dumps({"run_id": RUN_ID, "steps": summary}))
