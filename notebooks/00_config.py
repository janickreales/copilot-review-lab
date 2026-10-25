# Databricks notebook source
# MAGIC %md
# MAGIC # 00 · Configuración compartida
# MAGIC
# MAGIC **Propósito:** definir los widgets del pipeline, cargar `config/<env>.json` y fijar el catálogo y esquema de trabajo.
# MAGIC
# MAGIC **Uso:**
# MAGIC - Como task `setup` del job: crea el esquema de destino si no existe.
# MAGIC - Vía `%run ./00_config` desde los demás notebooks: deja disponibles `cfg`, `RUN_ID`, `SQL_DIR`, `PROJECT_ROOT`, `log` y `set_task_value()`.
# MAGIC
# MAGIC **No** termina con `dbutils.notebook.exit`: hacerlo cortaría la ejecución del notebook que lo incluye con `%run`.
# MAGIC
# MAGIC | Parámetro | Default | Descripción |
# MAGIC |---|---|---|
# MAGIC | `env` | `dev` | Selecciona `config/<env>.json` |
# MAGIC | `catalog` | `workspace` | Catálogo de Unity Catalog |
# MAGIC | `schema` | `margin_dev` | Esquema de destino |
# MAGIC | `run_id` | vacío | Id de la corrida; el job lo llena con `{{job.run_id}}` |

# COMMAND ----------

import os
import sys
import uuid

# Los notebooks viven en notebooks/; la raíz del proyecto (donde está src/) es el directorio padre.
PROJECT_ROOT = os.path.abspath(os.path.join(os.getcwd(), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from src.utils.config_loader import load_config
from src.utils.logging_utils import get_logger

# COMMAND ----------

dbutils.widgets.text("env", "dev", "Ambiente")
dbutils.widgets.text("catalog", "workspace", "Catálogo")
dbutils.widgets.text("schema", "margin_dev", "Esquema")
dbutils.widgets.text("run_id", "", "Run id")

cfg = load_config(
    env=dbutils.widgets.get("env"),
    catalog=dbutils.widgets.get("catalog"),
    schema=dbutils.widgets.get("schema"),
    config_dir=os.path.join(PROJECT_ROOT, "config"),
)
RUN_ID = dbutils.widgets.get("run_id") or f"interactive-{uuid.uuid4().hex[:12]}"
SQL_DIR = os.path.join(PROJECT_ROOT, "src", "sql")
log = get_logger("retail_margin")


def set_task_value(key, value):
    """Publica un task value para los tasks siguientes del job.

    Si el notebook corre vía dbutils.notebook.run (08_orchestrator), no es un
    task del job y Databricks rechaza el set; en ese caso se omite y el valor
    viaja en el JSON de dbutils.notebook.exit.
    """
    try:
        dbutils.jobs.taskValues.set(key=key, value=value)
    except Exception as exc:
        if "not a task run" not in str(exc):
            raise
        log.info("Skipping task value %s: notebook is not running as a job task", key)

# COMMAND ----------

# El esquema se crea con IDENTIFIER() y un parámetro nombrado; catalog y schema ya fueron validados por load_config.
spark.sql(
    "CREATE SCHEMA IF NOT EXISTS IDENTIFIER(:schema_fqn)",
    args={"schema_fqn": f"{cfg.catalog}.{cfg.schema}"},
)
spark.catalog.setCurrentCatalog(cfg.catalog)
spark.catalog.setCurrentDatabase(cfg.schema)

log.info(
    "Config ready: env=%s target=%s.%s range=%s..%s run_id=%s",
    cfg.env,
    cfg.catalog,
    cfg.schema,
    cfg.date_from,
    cfg.date_to,
    RUN_ID,
)
